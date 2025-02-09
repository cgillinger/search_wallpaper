"""
Konfigurationsmodul för loggning i SearchWallpaper.
"""

import logging
import os
import json
from datetime import datetime
from utils.paths import get_app_paths

def count_log_entries(log_file):
    """Räknar antalet körningar i loggfilen genom att räkna 'Startar SearchWallpaper' meddelanden."""
    try:
        if not os.path.exists(log_file):
            return 0
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            return content.count("Startar SearchWallpaper-applikationen")
    except Exception:
        return 0

def setup_logging():
    """
    Konfigurerar loggning för applikationen.
    Skapar en loggfil i programkatalogen/logs och konfigurerar konsolloggning.
    Roterar loggen efter 50 körningar.
    """
    
    # Hämta sökvägar
    paths = get_app_paths()
    
    # Skapa logs-katalogen om den inte finns
    os.makedirs(paths['logs_dir'], exist_ok=True)
    
    # Huvudloggfil
    log_file = os.path.join(paths['logs_dir'], "search_wallpaper.log")
    
    # Kontrollera antal körningar i loggfilen
    num_runs = count_log_entries(log_file)
    
    # Om det finns mer än 50 körningar, rotera loggen
    if num_runs >= 50:
        # Skapa en backup av den gamla loggfilen
        backup_file = os.path.join(
            paths['logs_dir'], 
            f"search_wallpaper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        try:
            # Flytta den gamla loggfilen till backup
            if os.path.exists(log_file):
                os.rename(log_file, backup_file)
                
            # Ta bort äldre backup-filer om det finns fler än 2
            backup_files = [f for f in os.listdir(paths['logs_dir']) 
                          if f.startswith('search_wallpaper_') and f.endswith('.log')]
            backup_files.sort(reverse=True)  # Nyaste först
            
            # Behåll bara de två senaste backup-filerna
            for old_backup in backup_files[2:]:
                try:
                    os.remove(os.path.join(paths['logs_dir'], old_backup))
                except:
                    pass
                    
        except Exception as e:
            # Om vi inte kan rotera, fortsätt ändå med befintlig fil
            pass
    
    # Grundläggande loggningskonfiguration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='a'),
            logging.StreamHandler()  # För konsolloggning
        ]
    )
    
    # Ställ in loggningsnivå för externa bibliotek
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("WDM").setLevel(logging.WARNING)
    
    # Skapa en logger för denna modul
    logger = logging.getLogger(__name__)
    logger.info("Loggning initierad för SearchWallpaper")
    
    return logger