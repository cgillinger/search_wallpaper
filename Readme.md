# SearchWallpaper - Automatisk bakgrundsbildshanterare

## Vad gör programmet?

SearchWallpaper är ett program som automatiskt hämtar och sätter slumpmässiga bakgrundsbilder på din Windows-dator. Programmet söker på Bing efter bilder baserat på söktermer som du själv kan anpassa. Det är särskilt utformat för att hitta högkvalitativa bilder i rätt storlek för moderna skärmar.

## Systemkrav

För att köra programmet behöver du:
- Windows operativsystem
- Microsoft Edge webbläsare (kommer förinstallerad med Windows)
- Skrivbehörighet i programmappen

## Filstruktur och sökvägar

När du kör programmet första gången kommer det att skapa flera mappar och filer. Låt oss gå igenom var allt hamnar:

### Programmappen
När du kör exe-filen kommer följande att skapas i **samma mapp som exe-filen**:

```
SearchWallpaper.exe
├── search_queries.ini    # Konfigurationsfil för söktermer
├── history.json         # Historik över använda bilder
├── daily_search_count.json  # Räknare för dagliga sökningar
├── logs/                # Mapp för loggfiler
│   └── search_wallpaper.log
└── cache/              # Mapp för nedladdade bilder
    └── bing_wallpaper_[random].jpg
```

För att göra det tydligt, om du har lagt exe-filen i till exempel:
```
C:\Program\SearchWallpaper\SearchWallpaper.exe
```

Då kommer alla filer att skapas i:
```
C:\Program\SearchWallpaper\search_queries.ini
C:\Program\SearchWallpaper\logs\
C:\Program\SearchWallpaper\cache\
```

### Viktigt om sökvägar

Det är viktigt att förstå att:
1. Alla filer skapas i samma mapp som exe-filen
2. Programmet behöver ha skrivbehörighet i denna mapp
3. Det är därför rekommenderat att INTE lägga exe-filen i "Program Files" eller "Program Files (x86)"
4. Skapa istället en egen mapp för programmet där det har fulla rättigheter

Rekommenderad installation:
1. Skapa en mapp, till exempel: `C:\SearchWallpaper\`
2. Kopiera exe-filen dit
3. Kör programmet - alla filer kommer att skapas i denna mapp

## Konfiguration och anpassning

### Redigera söktermer och exkluderingar
Programmet styrs av konfigurationsfilen `search_queries.ini` som ligger i samma mapp som exe-filen. För att anpassa sökningen:

1. Öppna `search_queries.ini` i en textredigerare (till exempel Notepad)
2. Under [Search] hittar du två viktiga sektioner:
   - queries: Vad programmet ska söka efter
   - excluded_words: Vad som ska filtreras bort från resultaten
3. Lägg till eller ta bort rader för att ändra söktermerna
4. Spara filen

Exempel på hur filen ser ut:
```ini
[Search]
queries = 
    pet parrot beautiful wallpaper
    pet budgie colorful wallpaper
    pet cockatiel portrait wallpaper

excluded_words = 
    cartoon
    drawing
    sketch
    clipart
    vector
    illustration
    anime
    meme
```

Filen har två huvuddelar:
1. `queries`: Här lägger du till de söktermer du vill använda. Varje sökterm ska vara på en egen rad.
2. `excluded_words`: Här kan du lista ord som du vill exkludera från sökresultaten. Om något av dessa ord finns i bildlänken eller beskrivningen kommer bilden att ignoreras.

Detta ger dig fin kontroll över både vad du söker efter och vad du vill filtrera bort. Till exempel:
- Om du bara vill ha fotografier kan du exkludera ord som "cartoon", "drawing", "sketch"
- Om du vill undvika vissa typer av innehåll kan du lägga till relevanta exkluderingsord
- Om vissa söktermer ger oönskade resultat kan du filtrera bort specifika ord

### Hantera cache
Nedladdade bilder sparas i cache-mappen. Du kan:
- Radera enskilda bilder du inte vill ha
- Tömma hela cache-mappen för att börja om
- Behålla favoritbilder genom att flytta dem någon annanstans

### Loggfiler
Loggfilerna i logs-mappen hjälper dig att:
- Se vad programmet gör
- Felsöka om något inte fungerar
- Förstå vilka bilder som hittats och använts

## Utvecklingsmiljö

Projektet är strukturerat enligt följande:

```
projektrot/
├── src/
│   ├── api/
│   │   └── bing_scraper.py
│   ├── config/
│   │   ├── logging_config.py
│   │   └── search_config.py
│   └── utils/
│       ├── paths.py
│       └── wallpaper.py
├── resources/
│   └── icon.ico
├── requirements.txt
└── search_wallpaper.spec
```

### Bygga projektet

För att bygga en körbar fil:

1. Installera PyInstaller:
```bash
pip install pyinstaller
```

2. Kör build-kommandot från projektets rotmapp:
```bash
pyinstaller search_wallpaper.spec
```

3. Den färdiga exe-filen hamnar i:
```
projektrot/dist/SearchWallpaper.exe
```

## Testning och utveckling

För att testa under utveckling:

1. Installera alla beroenden:
```bash
pip install -r requirements.txt
```

2. Kör programmet direkt med Python:
```bash
python src/main.py
```

## Felsökning

Om programmet inte fungerar som det ska:

1. Kontrollera loggfilen i logs-mappen
2. Se till att programmet har skrivbehörighet i sin mapp
3. Om något verkar skadat kan du:
   - Radera search_queries.ini (ny skapas med standardvärden)
   - Radera daily_search_count.json (nollställer dagens räknare)
   - Tömma cache-mappen (tar bort gamla bilder)

## Begränsningar och inställningar

Programmet har följande inbyggda begränsningar:

- Max 50 sökningar per dag (sparas i daily_search_count.json)
- Sparar max 50 bilder i historiken (history.json)
- Behåller max 3 loggfiler (en aktiv, två backup)
- Kräver bilder som är minst 1920x1080 pixlar
- Använder endast bilder i landskapsformat

Dessa värden kan ändras i källkoden om du bygger om programmet själv.

## Säkerhet och prestanda

Programmet:
- Kör Edge i "headless" läge (ingen synlig webbläsare)
- Använder cachning för att minska belastningen på Bing
- Kontrollerar bilddimensioner innan nedladdning
- Roterar loggar för att spara diskutrymme
- Sparar historik för att undvika dubbletter

## Support och uppdateringar

Om du stöter på problem:
1. Kontrollera först loggfilerna i logs-mappen
2. Se till att alla systemkrav är uppfyllda
3. Verifiera att programmet har rätt behörigheter
4. Testa att radera konfigurationsfiler för att återställa till standardvärden

För utvecklare som vill bidra:
1. Gör en fork av repositoryt
2. Skapa en gren för din funktion eller buggfix
3. Följ kodstilar och konventioner
4. Skicka en pull request med tydlig beskrivning