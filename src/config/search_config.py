"""
Hantering av söktermer från extern konfigurationsfil.
"""
import os
import configparser
import logging
from utils.paths import get_app_paths

logger = logging.getLogger(__name__)

def get_default_queries():
    """Returnerar standardsöktermer om ingen konfigurationsfil hittas."""
    return [
        "pet parrot beautiful wallpaper",
        "pet budgie colorful wallpaper",
        "pet cockatiel portrait wallpaper",
        "pet amazon parrot wallpaper",
        "pet parakeet wallpaper",
        "pet conure bird wallpaper",
        "pet quaker parrot",
        "pet macaw colorful wallpaper",
        "pet canary bird wallpaper",
        "pet finch beautiful wallpaper",
        "pet lovebird colorful wallpaper",
        "african grey parrot pet wallpaper",
        "indian ring neck parrot wallpaper",
        "pet pigeon wallpaper",
        "cockatoo pet portrait wallpaper"
    ]

def load_search_queries():
    """
    Läser in söktermer från konfigurationsfilen.
    Om filen inte finns, skapas den med standardvärden.
    """
    paths = get_app_paths()
    config_file = os.path.join(paths['program_data'], 'search_queries.ini')
    
    config = configparser.ConfigParser()
    config.optionxform = str  # Behåll skiftläge i söktermer
    
    # Om filen inte finns, skapa den med standardvärden och instruktioner
    if not os.path.exists(config_file):
        instructions = """\
# Instruktioner för att lägga till eller ändra söktermer:
# 1. Varje sökterm ska vara på en egen rad under [Search]
# 2. Lägg gärna till 'wallpaper' i slutet av söktermen för bästa resultat
# 3. Spara filen efter ändringar - programmet läser in ändringarna vid nästa start
#
# Exempel på hur du lägger till en ny sökterm:
# queries = 
#     colorful macaw wallpaper
#     blue budgie wallpaper
#     
# OBS: Lägg inte till några citattecken (") runt söktermerna!
"""
        
        config['Instructions'] = {'info': instructions}
        config['Search'] = {
            'queries': '\n    ' + '\n    '.join(get_default_queries()),  # Indentera för läsbarhet
            'excluded_words': 'chicken,rooster,hen,poultry,turkey,duck,geese'
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            logger.info(f"Skapade ny konfigurationsfil: {config_file}")
        except Exception as e:
            logger.error(f"Kunde inte skapa konfigurationsfil: {str(e)}")
            return get_default_queries(), []
    
    # Läs konfigurationen
    try:
        config.read(config_file, encoding='utf-8')
        queries = [q.strip() for q in config['Search']['queries'].split('\n') if q.strip()]
        excluded = [w.strip() for w in config['Search'].get('excluded_words', '').split(',') if w.strip()]
        
        logger.info(f"Läste in {len(queries)} söktermer från konfiguration")
        return queries, excluded
    except Exception as e:
        logger.error(f"Fel vid läsning av konfigurationsfil: {str(e)}")
        return get_default_queries(), []