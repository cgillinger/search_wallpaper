"""
BingScraper - Hämtar bilder från Bing med Selenium.
Fix v2: Tvingar Edge att köra 100% i bakgrunden (headless) utan att något Edge-fönster kan öppnas.
- Tar bort alla vägar som kan starta msedge.exe synligt
- Använder endast msedgedriver.exe via WebDriverManager/Selenium Manager
- Lägger till extra skydd (offscreen/minimize) OM headless skulle ignoreras i enstaka miljöer
Version: 2025-08-31
"""

import os
# Fix för WebDriver Manager SSL-problem
os.environ['WDM_SSL_VERIFY'] = '0'

import random
import json
import logging
import time
import subprocess
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


def get_edge_driver_service() -> EdgeService:
    """
    Returnerar en Edge WebDriver Service på ett sätt som inte öppnar ett synligt Edge-fönster.
    Viktigt: vi pekar ALDRIG på msedge.exe här (det skulle starta webbläsaren synligt).
    - Primärt: WebDriverManager hämtar rätt msedgedriver.exe för din Edge-version.
    - Sekundärt: Låt Selenium/Selenium Manager hitta msedgedriver automatiskt.
    Dessutom döljs drivarens konsolfönster i Windows.
    """
    try:
        logger.info("Försöker ladda Edge-driver via WebDriverManager...")
        driver_path = EdgeChromiumDriverManager().install()
        service = EdgeService(driver_path)
    except Exception as e:
        logger.warning(f"WebDriverManager misslyckades: {e}")
        logger.info("Försöker med systemets Edge-driver (Selenium Manager/OS PATH)...")
        service = EdgeService()

    # Döljer msedgedriver-konsolfönstret i Windows
    try:
        service.creationflags = subprocess.CREATE_NO_WINDOW  # Python 3.8+ och Selenium 4.x
    except Exception:
        pass

    return service


class BingScraper:
    """Klass för att hämta bilder från Bing via Selenium (headless Edge)."""

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

        # Headless-läge med robust fallback + "osynliga" fönsterinställningar
        self.headless_mode = "new"  # "new" eller "classic"
        self.edge_options = self._build_edge_options(self.headless_mode)

    # --- Hjälpmetoder för konfiguration och state ---

    def _build_edge_options(self, headless_mode: str) -> Options:
        """
        Bygger en Options-instans för Edge.
        headless_mode: "new" -> '--headless=new', "classic" -> '--headless'
        Innehåller även offscreen/minimize som sista skydd om headless skulle ignoreras i enstaka miljöer.
        """
        opts = Options()
        # Säkerställ Chromium-baserad Edge (vissa miljöer kräver detta explicit)
        try:
            opts.use_chromium = True  # typer kräver ibland attributet
        except Exception:
            pass

        # Headless
        if headless_mode == "new":
            opts.add_argument('--headless=new')
        else:
            opts.add_argument('--headless')

        # Stabilitet/prestanda
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-gpu')

        # Undvik störande funktioner/UI
        opts.add_argument('--no-first-run')
        opts.add_argument('--no-default-browser-check')
        opts.add_argument('--disable-features=msEdgeSidebar,TranslateUI')
        opts.add_argument('--disable-blink-features=AutomationControlled')

        # Offscreen/minimize som sista skydd om headless mot förmodan ignoreras
        opts.add_argument('--start-minimized')
        opts.add_argument('--window-position=-32000,-32000')

        # Mindre "Selenium is controlled" brus
        try:
            opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            opts.add_experimental_option('useAutomationExtension', False)
        except Exception:
            pass

        return opts

    def _load_history(self) -> list:
        """Läser in historiken över tidigare använda bilder."""
        if os.path.exists(self.paths['history_file']):
            with open(self.paths['history_file'], "r", encoding="utf-8") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    return []
        return []

    def _save_history(self):
        """Sparar historiken till fil (max 50 senaste)."""
        with open(self.paths['history_file'], "w", encoding="utf-8") as file:
            json.dump(self.history[-50:], file, ensure_ascii=False)

    def _load_daily_search_count(self) -> Dict:
        """Läser in dagens sökräknare."""
        if os.path.exists(self.paths['daily_count_file']):
            with open(self.paths['daily_count_file'], "r", encoding="utf-8") as file:
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
        with open(self.paths['daily_count_file'], "w", encoding="utf-8") as file:
            json.dump(self.daily_search_count, file, ensure_ascii=False)

    def _increment_search_count(self) -> bool:
        """Ökar sökräknaren och kontrollerar gränsen (50/dag)."""
        if self.daily_search_count["count"] >= 50:
            logger.warning("Daglig sökgräns uppnådd")
            return False
        self.daily_search_count["count"] += 1
        self._save_daily_search_count()
        return True

    def _verify_image_dimensions(self, image_url: str) -> bool:
        """Verifierar att bilden uppfyller dimensionskraven (min 1920x1080 och landskap)."""
        try:
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = session.get(image_url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))
            width, height = img.size

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

    # --- Huvudflöde ---

    def get_random_image(self) -> Optional[Tuple[str, Dict]]:
        """
        Hämtar en slumpmässig bild från Bing.
        Kör Edge i headless-läge och undviker att öppna ett synligt Edge-fönster.
        Faller tillbaka från '--headless=new' till klassiska '--headless' om det behövs.
        OBS: Vi kör inte msedge.exe manuellt någonstans (ingen versionscheck) för att undvika UI-triggers.
        """
        if not self._increment_search_count():
            return None

        driver = None
        max_retries = 3
        used_headless_fallback = False

        for attempt in range(max_retries):
            try:
                query = random.choice(self.search_queries)
                search_url = f"{self.BASE_URL}?q={query}&qft=+filterui:aspect-wide+filterui:imagesize-wallpaper&first=1"

                # Starta WebDriver headless
                self._update_status("Startar webbläsare...")
                logger.info(f"Försök {attempt + 1}/{max_retries} - Startar Edge WebDriver...")

                service = get_edge_driver_service()

                try:
                    driver = webdriver.Edge(service=service, options=self.edge_options)
                    # Verifiera att WebDriver fungerar
                    driver.execute_script("return navigator.userAgent;")
                    logger.info("Edge WebDriver startad framgångsrikt i headless-läge")
                except Exception as start_error:
                    # Om modern headless inte stöds, fall tillbaka till klassisk headless en gång
                    if self.headless_mode == "new" and not used_headless_fallback:
                        logger.warning(f"Start i '--headless=new' misslyckades: {start_error}")
                        logger.info("Försöker igen med klassiska '--headless'...")
                        used_headless_fallback = True
                        self.headless_mode = "classic"
                        self.edge_options = self._build_edge_options(self.headless_mode)
                        # Försök igen direkt i samma försök
                        if driver:
                            try:
                                driver.quit()
                            except Exception:
                                pass
                        time.sleep(1)
                        driver = webdriver.Edge(service=service, options=self.edge_options)
                        driver.execute_script("return navigator.userAgent;")
                        logger.info("Edge WebDriver startad med klassiska '--headless'")
                    else:
                        raise

                logger.info(f"Söker efter: {query}")
                self._update_status(f"Söker efter bilder med temat: {query}")

                # Navigera till Bing Images med timeout
                driver.set_page_load_timeout(30)
                driver.get(search_url)

                # Vänta på att bilderna ska laddas
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "iusc"))
                )

                # Hitta alla bildcontainers
                image_elements = driver.find_elements(By.CLASS_NAME, "iusc")

                if not image_elements:
                    logger.warning("Inga bilder hittades")
                    if driver:
                        driver.quit()
                    return None

                # Filtrera och processa bilderna
                self._update_status("Analyserar bilder...")
                valid_images = []
                for element in image_elements[:12]:  # Begränsa för snabbhet/stabilitet
                    try:
                        image_data = json.loads(element.get_attribute('m'))
                        image_url = image_data.get('murl', '')

                        if (
                            image_url
                            and image_url not in self.history
                            and not any(word in image_url.lower() for word in self.excluded_words)
                        ):
                            if self._verify_image_dimensions(image_url):
                                valid_images.append((image_url, image_data))
                                logger.info(f"Giltig bild hittad: {image_url}")

                    except Exception as e:
                        logger.error(f"Fel vid processering av bild: {str(e)}")
                        continue

                if not valid_images:
                    logger.warning("Inga giltiga bilder hittades")
                    if driver:
                        driver.quit()
                    return None

                # Välj en slumpmässig bild
                self._update_status("Väljer bild...")
                selected_url, metadata = random.choice(valid_images)

                # Uppdatera historik
                self.history.append(selected_url)
                self._save_history()

                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        # Om quit() misslyckas, försök forcera stängning
                        try:
                            driver.close()
                            driver.quit()
                        except Exception:
                            pass

                return selected_url, {"source": "Bing Images", "query": query}

            except Exception as e:
                logger.error(f"Försök {attempt + 1} - Fel vid bildsökning: {str(e)}")

                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = None

                # Om det inte är sista försöket, försök igen
                if attempt < max_retries - 1:
                    self._update_status("Försöker igen...")
                    time.sleep(3)
                    continue
                else:
                    logger.error(f"Alla {max_retries} försök misslyckades")
                    return None

        return None

    def _show_edge_error(self, message):
        """Visar felmeddelande för Edge-problem."""
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Edge-fel", message)
            root.destroy()
        except Exception:
            logger.error(f"Edge-fel: {message}")

    def get_cached_image(self) -> Optional[str]:
        """Returnerar en slumpmässig bild från cachen om tillgänglig."""
        try:
            cached_files = [
                f for f in os.listdir(self.paths['cache_dir'])
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ]
            if cached_files:
                return os.path.join(self.paths['cache_dir'], random.choice(cached_files))
        except Exception as e:
            logger.error(f"Fel vid hämtning från cache: {str(e)}")
        return None
