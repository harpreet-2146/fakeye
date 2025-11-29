import re
from bs4 import BeautifulSoup
import httpx
from newspaper import Article
from app.config import USER_AGENT

async def fetch_raw_http(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text

async def extract_with_newspaper(url: str):
    try:
        art = Article(url)
        art.download()
        art.parse()
        text = art.text
        paras = [p.strip() for p in text.split("\n") if p.strip()]
        if paras:
            return paras
    except Exception:
        return []

async def extract_paragraphs(url: str):
    # Try newspaper first (synchronous) — may block; call as wrapper
    try:
        paras = await extract_with_newspaper(url)
        if paras:
            return paras
    except Exception:
        pass

    # Fallback to http + bs4
    try:
        html = await fetch_raw_http(url)
    except Exception:
        return []

    soup = BeautifulSoup(html, "html.parser")
    ps = soup.find_all("p")
    paras = []
    for p in ps:
        t = p.get_text().strip()
        t = re.sub(r"\s+", " ", t)
        if len(t) > 30:
            paras.append(t)
    return paras

# public wrapper
async def fetch_and_extract(url: str):
    return await extract_paragraphs(url)
