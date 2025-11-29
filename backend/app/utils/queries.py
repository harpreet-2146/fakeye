import re

def generate_queries(claim: str):
    q = claim.strip()
    queries = [q]
    # basic templates
    templates = [
        "{} who did it",
        "{} evidence",
        "{} fact check",
        "{} true or false",
        "{} explanation",
        "{} news"
    ]
    for t in templates:
        queries.append(t.format(q))
    # short canonical (remove punctuation)
    short = re.sub(r"[^\w\s]", "", q)
    if short != q:
        queries.append(short)
    return queries[:8]
