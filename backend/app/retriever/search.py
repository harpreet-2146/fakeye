import os
import httpx
from app.config import SERPAPI_KEY, BING_API_KEY, USER_AGENT, MAX_URLS
from urllib.parse import urlencode

# Minimal SerpAPI usage (if you have SERPAPI_KEY). If not, use Bing (BING_API_KEY).
SERPAPI_URL = "https://serpapi.com/search.json"
BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"

async def search_urls(query: str, num: int = 5):
    headers = {"User-Agent": USER_AGENT}
    urls = []
    if SERPAPI_KEY:
        params = {"q": query, "api_key": SERPAPI_KEY, "num": num}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            r = await client.get(SERPAPI_URL, params=params)
            r.raise_for_status()
            data = r.json()
        for item in data.get("organic_results", []):
            u = item.get("link") or item.get("url")
            if u:
                urls.append(u)
                if len(urls) >= num:
                    break
    elif BING_API_KEY:
        headers["Ocp-Apim-Subscription-Key"] = BING_API_KEY
        params = {"q": query, "count": num}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            r = await client.get(BING_SEARCH_URL, params=params)
            r.raise_for_status()
            data = r.json()
        # Bing returns webPages.value
        for item in data.get("webPages", {}).get("value", []):
            urls.append(item.get("url"))
            if len(urls) >= num:
                break
    else:
        # Fallback: basic DuckDuckGo HTML scraping via ddg (httpx) — light and unreliable
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            r = await client.get(f"https://duckduckgo.com/html/?q={query}")
            if r.status_code == 200:
                text = r.text
                # extract links naively (not robust)
                import re
                matches = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)"', text)
                for m in matches[:num]:
                    urls.append(m)
    return urls[:num]