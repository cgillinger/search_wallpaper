"""
Huvudprogram för Bing Wallpaper
"""

import os
import sys
import logging
import tempfile
import tkinter as tk
from tkinter import ttk
import time
from api.bing_scraper import BingScraper
from utils.wallpaper import set_wallpaper, download_image
from config.logging_config import setup_logging
from utils.paths import get_app_paths, needs_admin

# Konfigurera loggning
setup_logging()
logger = logging.getLogger(__name__)

class StatusWindow:
    def __init__(self):
        try:
            logger.info("Skapar GUI-fönster...")
            self.root = tk.Tk()
            self.root.title("SearchWallpaper")
            
            # Debug: Skriv ut om fönstret skapades
            logger.info(f"GUI-fönster skapat: {self.root.winfo_exists()}")
            
            # Enklare fönster för test
            self.root.geometry("400x150")
            self.root.configure(bg='white')
            
            # Force window to be visible
            self.root.attributes('-topmost', True)
            self.root.lift()
            self.root.focus_force()
            
            # Status text
            self.status_text = tk.Label(self.root, text="Initierar...", bg='white', font=('Segoe UI', 12))
            self.status_text.pack(pady=20)
            
            # Force update
            self.root.update_idletasks()
            self.root.update()
            
            logger.info("GUI-komponenter initierade")
            
        except Exception as e:
            logger.error(f"Fel vid GUI-initiering: {str(e)}")
            raise

    def update_status(self, message):
        try:
            logger.info(f"Uppdaterar status: {message}")
            self.status_text.config(text=message)
            self.root.update_idletasks()
            self.root.update()
        except Exception as e:
            logger.error(f"Fel vid statusuppdatering: {str(e)}")

    def close(self):
        try:
            logger.info("Stänger GUI")
            if self.root.winfo_exists():
                self.root.destroy()
        except Exception as e:
            logger.error(f"Fel vid stängning av GUI: {str(e)}")

def main():
    """
    Huvudfunktion som kör programmet.
    """
    try:
        logger.info("Startar Bing Wallpaper-applikationen")
        
        # Skapa och visa statusfönster
        status = StatusWindow()
        
        # Kontrollera admin-rättigheter
        if needs_admin():
            status.update_status("Fel: Behöver administratörsrättigheter")
            time.sleep(3)
            status.close()
            sys.exit(1)

        # Hämta sökvägar
        paths = get_app_paths()
        
        # Initiera BingScraper och sök efter bild
        status.update_status("Söker efter bilder...")
        scraper = BingScraper()
        image_result = scraper.get_random_image()
        
        if not image_result:
            status.update_status("Använder cachad bild...")
            time.sleep(1)
            cached_image = scraper.get_cached_image()
            if cached_image:
                if set_wallpaper(cached_image):
                    status.update_status("Bakgrundsbild uppdaterad!")
                    time.sleep(2)
                else:
                    status.update_status("Kunde inte uppdatera bakgrundsbild")
                    time.sleep(2)
            else:
                status.update_status("Ingen bild tillgänglig")
                time.sleep(2)
                status.close()
                sys.exit(1)
            status.close()
            return

        # Hantera ny bild
        image_url = image_result[0]
        logger.info(f"Hämtar bild: {image_url}")
        status.update_status("Laddar ner bild...")

        cache_filename = f"bing_wallpaper_{os.urandom(4).hex()}.jpg"
        cache_path = os.path.join(paths['cache_dir'], cache_filename)
        
        if not download_image(image_url, cache_path):
            status.update_status("Kunde inte ladda ner bilden")
            time.sleep(2)
            status.close()
            sys.exit(1)

        status.update_status("Ställer in bakgrundsbild...")
        if set_wallpaper(cache_path):
            status.update_status("Bakgrundsbild uppdaterad!")
            logger.info("Bakgrundsbilden uppdaterades framgångsrikt.")
        else:
            status.update_status("Kunde inte uppdatera bakgrundsbild")
            logger.error("Misslyckades med att uppdatera bakgrundsbilden.")

        # Vänta och stäng
        time.sleep(2)
        status.close()

    except Exception as e:
        logger.error(f"Oväntat fel i huvudprogrammet: {str(e)}")
        try:
            status.update_status("Ett fel inträffade")
            time.sleep(2)
            status.close()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()