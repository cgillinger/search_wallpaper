# Projektbeskrivning - SearchWallpaper

## Projektöversikt

SearchWallpaper är en Python-baserad Windows-applikation som automatiserar processen att hämta och sätta bakgrundsbilder. Programmet använder Selenium med Microsoft Edge för att utföra bildsökningar på Bing, validerar bildernas kvalitet, och hanterar nedladdning och installation av bakgrundsbilder.

## Projektstruktur

```
projektrot/
├── src/                      # Källkodsmapp
│   ├── main.py              # Programmets huvudingång
│   ├── __init__.py          # Gör src till ett Python-paket
│   │
│   ├── api/                 # Externa API-interaktioner
│   │   ├── bing_scraper.py  # Hantering av Bing-bildsökning
│   │   └── __init__.py
│   │
│   ├── config/              # Konfigurationshantering
│   │   ├── logging_config.py # Loggningskonfiguration
│   │   ├── search_config.py # Hantering av söktermer
│   │   └── __init__.py
│   │
│   └── utils/               # Hjälpfunktioner
│       ├── paths.py         # Sökvägshantering
│       ├── wallpaper.py     # Bakgrundsbildshantering
│       └── __init__.py
│
├── resources/               # Statiska resurser
│   └── icon.ico            # Programmets ikon
│
├── search_wallpaper.spec    # PyInstaller specifikation
├── requirements.txt         # Projektberoenden
└── README.md               # Användardokumentation
```

## Kodbasens komponenter

### main.py
```python
"""
Huvudingång för programmet som:
- Initierar loggning
- Skapar BingScraper-instans
- Hanterar huvudprogramloopen
- Hanterar felhantering på toppnivå
"""
```

Viktiga ansvarsområden:
- Programflödeskontroll
- Felhantering och återhämtning
- Koordinering mellan komponenter

### api/bing_scraper.py
```python
"""
Hanterar all interaktion med Bing Images:
- Selenium-baserad webbskrapning
- Bildverifiering och filtrering
- Historikhantering
- Daglig användningsbegränsning
"""
```

Nyckelklasser:
- `BingScraper`: Huvudklass för bildsökning
  - Använder Edge i headless-läge
  - Hanterar sökhistorik
  - Verifierar bildkvalitet

### config/search_config.py
```python
"""
Hanterar inläsning och validering av söktermer:
- Läser search_queries.ini
- Hanterar standardvärden
- Validerar konfiguration
"""
```

Konfigurationsformat:
```ini
[Search]
queries = 
    sökterm1
    sökterm2
excluded_words = 
    ord1,ord2,ord3
```

### config/logging_config.py
```python
"""
Konfigurerar loggningssystem:
- Roterar loggar efter 50 körningar
- Hanterar både fil- och konsolloggning
- Konfigurerar loggnivåer för externa bibliotek
"""
```

### utils/paths.py
```python
"""
Central hantering av sökvägar:
- Detekterar körläge (utveckling/exe)
- Hanterar sökvägsgenerering
- Skapar nödvändiga mappar
"""
```

Viktiga funktioner:
- `get_executable_dir()`: Hanterar sökvägsskillnader mellan utveckling och produktion
- `get_app_paths()`: Genererar alla nödvändiga sökvägar
- `needs_admin()`: Kontrollerar behörighetskrav

### utils/wallpaper.py
```python
"""
Hanterar bakgrundsbildsfunktionalitet:
- Nedladdning av bilder
- Verifiering av bildformat
- Systeminteraktion för att sätta bakgrundsbild
"""
```

## Dataflöde

1. Användarinput:
   - Konfigurationsfil (search_queries.ini)
   - Kommandoradsargument (framtida möjlighet)

2. Programflöde:
   ```
   main.py
   ├── Initiering av loggning (logging_config.py)
   ├── Laddning av sökvägar (paths.py)
   ├── Laddning av söktermer (search_config.py)
   ├── Bildsökning (bing_scraper.py)
   │   ├── Selenium/Edge-interaktion
   │   ├── Bildvalidering
   │   └── Nedladdning
   └── Bakgrundsbildshantering (wallpaper.py)
   ```

## Statisk filstruktur vid körning

När programmet körs som exe skapas följande struktur:
```
programmapp/
├── SearchWallpaper.exe
├── search_queries.ini    # Konfiguration
├── history.json         # Sökhistorik
├── daily_search_count.json
├── logs/
│   └── search_wallpaper.log
└── cache/
    └── bing_wallpaper_*.jpg
```

## Utvecklingsöverväganden

### Beroenden
- Selenium: Webbskrapning
- Pillow: Bildhantering
- WebDriver Manager: Edge-driverhantering
- Requests: HTTP-nedladdningar
- PyInstaller: Exe-byggande

### Tekniska begränsningar
1. Windows-specifik implementering av bakgrundsbildshantering
2. Krav på Microsoft Edge
3. Behörighetskrav för filsystemåtkomst

### Utökningsområden
1. Stöd för flera bildkällor
2. Schemaläggning av uppdateringar
3. GUI för konfiguration
4. Mer avancerad bildfiltrering
5. Stöd för flera skärmar

## Build-process

PyInstaller-konfiguration (search_wallpaper.spec):
```python
"""
Byggkonfiguration som:
- Inkluderar alla nödvändiga moduler
- Hanterar resursfiler
- Konfigurerar exe-egenskaper
"""
```

Build-kommandon:
```bash
# Utvecklingstestning
python src/main.py

# Bygga exe
pyinstaller search_wallpaper.spec
```

## Felhantering och loggning

Loggningsnivåer:
- INFO: Normal operation
- WARNING: Icke-kritiska problem
- ERROR: Kritiska fel
- DEBUG: Utvecklingsinformation

Loggrotation:
- Max 3 loggfiler
- Rotation efter 50 körningar
- Tidsstämplade backuper

## Prestandaöverväganden

1. Cachning:
   - Bilder cachas lokalt
   - Historik förhindrar duplicering
   - Daglig användningsbegränsning

2. Resursanvändning:
   - Headless browser minimerar minnesanvändning
   - Bildverifiering före nedladdning
   - Begränsad historikstorlek

## Säkerhetsaspekter

1. Filsystemsäkerhet:
   - Använder användarmappen för temporära filer
   - Verifierar filrättigheter vid start
   - Säker hantering av externa resurser

2. Webbinteraktion:
   - Validerar bildURLs
   - Timeout-hantering
   - User-Agent-headers

## Framtida utvecklingsmöjligheter

1. Arkitekturella utökningar:
   - Pluginsystem för bildkällor
   - Konfigurationsvalidering
   - Händelsehanteringssystem

2. Funktionella tillägg:
   - GUI-gränssnitt
   - Automatisk schemaläggning
   - Bildbehandling/filtrering
   - Multi-monitor-stöd

3. Tekniska förbättringar:
   - Asynkron nedladdning
   - Parallell bildvalidering
   - Cacheoptimering

## Testning

Rekommenderade testområden:
1. Bildvalidering
2. Söktermhantering
3. Felåterhämtning
4. Filsysteminteraktion
5. Webbskrapningsrobusthet

## Byggmiljö

Utvecklingsmiljökrav:
- Python 3.12+
- Virtualenv rekommenderas
- Windows-miljö för full funktionalitet

Build-verktyg:
- PyInstaller för exe-generering
- Utvecklarverktyg enligt requirements.txt