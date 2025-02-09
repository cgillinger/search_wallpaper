"""
BingScraper - Hämtar bilder från Bing med Selenium.
"""

import random
import json
import os
import logging
import time
import winreg
from typing import Optional, Tuple, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import requests
from PIL import Image
from io import BytesIO
import tkinter as tk
from tkinter import messagebox
from utils.paths import get_app_paths
from config.search_config import load_search_queries

logger = logging.getLogger(__name__)

def check_edge_installed() -> bool:
    """
    Kontrollerar om Microsoft Edge är installerad genom att söka i Windows Registry.
    """
    try:
        # Sökvägar där Edge kan vara registrerad
        possible_paths = [
            r"SOFTWARE\Microsoft\Edge\BLBeacon",  # Modern Edge (Chromium)
            r"SOFTWARE\WOW6432Node\Microsoft\Edge\BLBeacon",  # 32-bit på 64-bit system
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",  # Windows 10/11 app paths
            r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{56EB18F8-B008-4CBD-B6D2-8C97FE7E9062}"  # Edge stable channel
        ]
        
        for reg_path in possible_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    # För app paths behöver vi kontrollera standardvärdet
                    if "App Paths" in reg_path:
                        path = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE, reg_path)
                        if path:
                            logger.info(f"Hittade Edge via App Paths: {path}")
                            return True
                    else:
                        # För övriga nycklar letar vi efter version
                        try:
                            version = winreg.QueryValueEx(key, "version")[0]
                            logger.info(f"Hittade Edge version: {version}")
                            return True
                        except FileNotFoundError:
                            # Om version inte finns, kolla bara om nyckeln finns
                            logger.info("Hittade Edge-installation (ingen version)")
                            return True
            except WindowsError:
                continue
                
        # Kontrollera även vanliga installationsplatser
        common_paths = [
            os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
            os.path.join(os.environ.get('ProgramFiles', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
            os.path.join(os.environ.get('LocalAppData', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),  # Win11 användarspecifik
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",  # Explicit sökväg
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"  # Explicit sökväg
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"Hittade Edge på: {path}")
                return True
                
        logger.warning("Kunde inte hitta Microsoft Edge installation")
        return False
        
    except Exception as e:
        logger.error(f"Fel vid sökning efter Edge: {str(e)}")
        return False

class BingScraper:
    """Klass för att hämta bilder från Bing via Selenium."""
    
    BASE_URL = "https://www.bing.com/images/search"
    
    def __init__(self, status_window=None):
        self.status_window = status_window
        
        # Hämta söktermer från konfiguration
        self.search_queries, self.excluded_words = load_search_queries()
        
        # Hämta alla sökvägar
        self.paths = get_app_paths()
        
        # Skapa mappar om de inte finns
        os.makedirs(self.paths['cache_dir'], exist_ok=True)
        
        # Ladda historik och räknare
        self.history = self._load_history()
        self.daily_search_count = self._load_daily_search_count()
        
        # Konfigurera Edge i headless-läge
        self.edge_options = Options()
        self.edge_options.add_argument('--headless')
        self.edge_options.add_argument('--no-sandbox')
        self.edge_options.add_argument('--disable-dev-shm-usage')
        self.edge_options.add_argument('--disable-gpu')
        self.edge_options.add_argument('--start-maximized')
        self.edge_options.add_argument('--force-device-scale-factor=1')
        self.edge_options.add_argument('--high-dpi-support=1')
        self.edge_options.add_argument('--window-size=1920,1080')

    def _load_history(self) -> list:
        """Läser in historiken över tidigare använda bilder."""
        if os.path.exists(self.paths['history_file']):
            with open(self.paths['history_file'], "r") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    return []
        return []

    def _save_history(self):
        """Sparar historiken till fil."""
        with open(self.paths['history_file'], "w") as file:
            json.dump(self.history[-50:], file)

    def _load_daily_search_count(self) -> Dict:
        """Läser in dagens sökräknare."""
        if os.path.exists(self.paths['daily_count_file']):
            with open(self.paths['daily_count_file'], "r") as file:
                try:
                    data = json.load(file)
                    if data.get("date") != time.strftime("%Y-%m-%d"):
                        return {"date": time.strftime("%Y-%m-%d"), "count": 0}
                    return data
                except json.JSONDecodeError:
                    pass
        return {"date": time.strftime("%Y-%m-%d"), "count": 0}

    def _save_daily_search_count(self):
        """Sparar dagens sökräknare."""
        with open(self.paths['daily_count_file'], "w") as file:
            json.dump(self.daily_search_count, file)

    def _increment_search_count(self) -> bool:
        """Ökar sökräknaren och kontrollerar gränsen."""
        if self.daily_search_count["count"] >= 50:
            logger.warning("Daglig sökgräns uppnådd")
            return False
        self.daily_search_count["count"] += 1
        self._save_daily_search_count()
        return True

    def _verify_image_dimensions(self, image_url: str) -> bool:
        """Verifierar att bilden uppfyller dimensionskraven."""
        try:
            session = requests.Session()
            # Öka timeout och lägg till headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/91.0.864.48'
            }
            response = session.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            
            # Kontrollera dimensioner och orientering
            if width < 1920 or height < 1080:
                logger.info(f"Bild för liten: {width}x{height}")
                return False
            
            if width < height:
                logger.info("Bild i porträttläge")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Fel vid verifiering av bild: {str(e)}")
            return False

    def _update_status(self, message):
        """Uppdaterar status om status_window finns."""
        if self.status_window:
            self.status_window.update_status(message)

    def get_random_image(self) -> Optional[Tuple[str, Dict]]:
        """Hämtar en slumpmässig bild från Bing."""
        if not self._increment_search_count():
            return None

        driver = None
        try:
            # Kontrollera först om Edge är installerad
            if not check_edge_installed():
                logger.error("Microsoft Edge är inte installerad")
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "Edge saknas",
                    "Microsoft Edge måste vara installerat för att använda detta program.\n\n" +
                    "Vänligen installera Microsoft Edge och försök igen."
                )
                root.destroy()
                return None

            query = random.choice(self.search_queries)
            search_url = f"{self.BASE_URL}?q={query}&qft=+filterui:aspect-wide+filterui:imagesize-wallpaper&first=1"
            
            try:
                self._update_status("Startar webbläsare...")
                service = EdgeService(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=self.edge_options)
            except Exception as edge_error:
                logger.error(f"Kunde inte starta Edge: {str(edge_error)}")
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "Edge-fel",
                    "Det gick inte att starta Microsoft Edge.\n\n" +
                    "Vänligen kontrollera att Edge är korrekt installerad och försök igen."
                )
                root.destroy()
                return None
            
            logger.info(f"Söker efter: {query}")
            self._update_status(f"Söker efter bilder med temat: {query}")
            driver.get(search_url)
            
            # Vänta på att bilderna ska laddas
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "iusc"))
            )
            
            # Hitta alla bildcontainers
            image_elements = driver.find_elements(By.CLASS_NAME, "iusc")
            
            if not image_elements:
                logger.warning("Inga bilder hittades")
                return None
                
            # Filtrera och processa bilderna
            self._update_status("Analyserar bilder...")
            valid_images = []
            for element in image_elements[:10]:  # Begränsa till första 10 bilderna
                try:
                    # Hämta bilddata från m-attributet
                    image_data = json.loads(element.get_attribute('m'))
                    image_url = image_data.get('murl', '')
                    
                    # Kontrollera exkluderade ord, historik och dimensioner
                    if (image_url and 
                        image_url not in self.history and
                        not any(word in image_url.lower() for word in self.excluded_words)):
                        
                        if self._verify_image_dimensions(image_url):
                            valid_images.append((image_url, image_data))
                            logger.info(f"Giltig bild hittad: {image_url}")
                            
                except Exception as e:
                    logger.error(f"Fel vid processering av bild: {str(e)}")
                    continue
            
            if not valid_images:
                logger.warning("Inga giltiga bilder hittades")
                return None
                
            # Välj en slumpmässig bild
            self._update_status("Väljer bild...")
            selected_url, metadata = random.choice(valid_images)
            
            # Uppdatera historik
            self.history.append(selected_url)
            self._save_history()
            
            return selected_url, {"source": "Bing Images", "query": query}
            
        except Exception as e:
            logger.error(f"Fel vid bildsökning: {str(e)}")
            return None
            
        finally:
            if driver:
                driver.quit()

    def get_cached_image(self) -> Optional[str]:
        """Returnerar en slumpmässig bild från cachen om tillgänglig."""
        try:
            cached_files = [f for f in os.listdir(self.paths['cache_dir']) if f.endswith(('.jpg', '.jpeg', '.png'))]
            if cached_files:
                return os.path.join(self.paths['cache_dir'], random.choice(cached_files))
        except Exception as e:
            logger.error(f"Fel vid hämtning från cache: {str(e)}")
        return None