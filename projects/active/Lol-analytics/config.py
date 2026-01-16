import os
from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY", "")

REGION = os.getenv("REGION", "euw1")
REGION_ROUTING = os.getenv("REGION_ROUTING", "europe")

DATABASE_PATH = os.getenv("DATABASE_PATH", "lol_meta.db")

RATE_LIMIT_PER_SECOND = 20
RATE_LIMIT_PER_2_MIN = 100

DATA_DRAGON_VERSION = "14.24.1"
DATA_DRAGON_BASE_URL = f"https://ddragon.leagueoflegends.com/cdn/{DATA_DRAGON_VERSION}"

RIOT_API_BASE_URL = f"https://{REGION}.api.riotgames.com"
RIOT_API_ROUTING_URL = f"https://{REGION_ROUTING}.api.riotgames.com"

QUEUE_RANKED_SOLO = 420
QUEUE_RANKED_FLEX = 440
