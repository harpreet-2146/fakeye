import re

def clean_text(s: str):
    if not s:
        return s
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    return s
