"""
Modul för att hantera nedladdning av bilder och inställning av skrivbordsbakgrund.
"""

import os
import ctypes
import platform
import logging
import requests
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

def download_image(url: str, save_path: str) -> bool:
    """
    Laddar ner en bild från en URL och sparar den lokalt.
    Verifierar också att bilden är i landskapsformat och har tillräcklig upplösning.
    
    Args:
        url (str): URL:en till bilden som ska laddas ner
        save_path (str): Sökvägen där bilden ska sparas
        
    Returns:
        bool: True om nedladdningen lyckades, False annars
    """
    try:
        # Skapa katalogen om den inte finns
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Hämta bilden
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Öppna bilden med PIL för att verifiera format och dimensioner
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        
        # Verifiera att bilden är i landskapsformat och har tillräcklig upplösning
        if width < height:
            logger.error(f"Bilden är i porträttformat: {width}x{height}")
            return False
            
        if width < 1920 or height < 1080:
            logger.error(f"Bilden har för låg upplösning: {width}x{height}")
            return False
        
        # Spara bilden
        img.save(save_path, quality=95)
        logger.info(f"Bild sparad: {save_path}")
        return True
        
    except Exception as e:
        logger.error(f"Fel vid nedladdning av bild: {str(e)}")
        return False

def set_wallpaper(image_path: str) -> bool:
    """
    Sätter den angivna bilden som skrivbordsbakgrund.
    
    Args:
        image_path (str): Sökvägen till bilden som ska användas
        
    Returns:
        bool: True om inställningen lyckades, False annars
    """
    try:
        # Konvertera relativ sökväg till absolut
        abs_path = os.path.abspath(image_path)
        
        if not os.path.exists(abs_path):
            logger.error(f"Bilden kunde inte hittas: {abs_path}")
            return False
            
        # Hantera olika operativsystem
        system = platform.system().lower()
        
        if system == "windows":
            # Windows: Använd ctypes för att anropa SystemParametersInfo
            SPI_SETDESKWALLPAPER = 0x0014
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDCHANGE = 0x02
            
            if ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, abs_path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            ):
                logger.info("Bakgrundsbild inställd på Windows")
                return True
                
        elif system == "darwin":  # macOS
            try:
                from appscript import app, mactypes
                app('Finder').desktop_picture.set(mactypes.File(abs_path))
                logger.info("Bakgrundsbild inställd på macOS")
                return True
            except ImportError:
                logger.error("appscript krävs för att ändra bakgrundsbild på macOS")
                return False
                
        elif system == "linux":
            # Försök med olika skrivbordsmiljöer
            desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
            
            if 'gnome' in desktop or 'unity' in desktop:
                os.system(f"gsettings set org.gnome.desktop.background picture-uri file://{abs_path}")
                logger.info("Bakgrundsbild inställd på GNOME/Unity")
                return True
                
            elif 'kde' in desktop:
                os.system(
                    f"dbus-send --session --dest=org.kde.plasmashell --type=method_call "
                    f"/PlasmaShell org.kde.PlasmaShell.evaluateScript 'string:"
                    f"var all = desktops();for (i=0;i<all.length;i++){{"
                    f"d = all[i];d.wallpaperPlugin = \"org.kde.image\";"
                    f"d.currentConfigGroup = Array(\"Wallpaper\", \"org.kde.image\", \"General\");"
                    f"d.writeConfig(\"Image\", \"file://{abs_path}\")}}'"
                )
                logger.info("Bakgrundsbild inställd på KDE")
                return True
                
            else:
                logger.error(f"Skrivbordsmiljön stöds inte: {desktop}")
                return False
                
        else:
            logger.error(f"Operativsystemet stöds inte: {system}")
            return False
            
    except Exception as e:
        logger.error(f"Fel vid inställning av bakgrundsbild: {str(e)}")
        return False
        
    return False  # Om vi når hit har något gått fel
