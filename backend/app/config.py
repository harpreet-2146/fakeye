import os
from dotenv import load_dotenv

load_dotenv()

# Search API (SerpAPI/Bing). Set one of these in .env
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
BING_API_KEY = os.getenv("BING_API_KEY", "")

# FastAPI options
MAX_URLS = int(os.getenv("MAX_URLS", "20"))
TOP_SNIPPETS = int(os.getenv("TOP_SNIPPETS", "20"))

# Misc
USER_AGENT = "Mozilla/5.0 FakeyeBot/1.0"
