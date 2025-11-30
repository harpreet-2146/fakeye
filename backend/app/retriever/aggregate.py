# app/retriever/aggregate.py
import math
from typing import List, Dict, Tuple

def _is_death_query(claim: str) -> bool:
    c = claim.lower()
    keywords = ["dead", "died", "die", "killed", "assassinated", "murdered"]
    return any(k in c for k in keywords)

def _snippet_has_death_evidence(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    kws = [
        "died", "dies", "dead", "death", "passed away", "obituary",
        "killed", "assassinated", "assassination", "murdered", "shot"
    ]
    return any(kw in t for kw in kws)

def _map_avg_conf_to_label(avg_conf: float) -> str:
    if math.isnan(avg_conf):
        return "Unverifiable"
    if abs(avg_conf) < 0.10:
        return "Mixture"
    if avg_conf >= 0.10:
        return "True"
    if avg_conf <= -0.10:
        return "False"
    return "Mixture"

def aggregate_verdict(claim: str, evidence: List[Dict], verbose: bool = False) -> Tuple[str, float, str, Dict]:
    """
    Returns (raw_label, percent, summary, breakdown). When verbose=False, breakdown will be {}.
    breakdown contains: items (per-evidence weight/signed), total_weight, signed_sum, avg_conf,
    counts (support/contradict/neutral), top_support/top_contradict (short info).
    """
    breakdown = {"items": []}

    if not evidence:
        raw, pct, summ = "Unverifiable", 25.0, "No evidence items found."
        if verbose:
            breakdown.update({"total_weight": 0.0, "signed_sum": 0.0, "avg_conf": float("nan"),
                              "support_count": 0, "contradict_count": 0, "neutral_count": 0})
            return raw, pct, summ, breakdown
        return raw, pct, summ, {}

    total_weight = 0.0
    signed_sum = 0.0

    for e in evidence:
        sim = float(e.get("semantic_sim", 0.0) or 0.0)
        conf = float(e.get("stance_conf", sim) or sim or 0.0)
        weight = sim * conf
        stance = (e.get("stance") or "").lower()

        if stance == "support":
            signed = +1.0 * (sim * conf)
        elif stance == "contradict":
            signed = -1.0 * (sim * conf)
        else:
            signed = 0.0

        breakdown["items"].append({
            "url": e.get("url"),
            "publisher": e.get("publisher"),
            "snippet": (e.get("snippet") or e.get("text") or "")[:300],
            "semantic_sim": sim,
            "stance": stance,
            "stance_conf": conf,
            "weight": weight,
            "signed": signed
        })

        total_weight += abs(weight)
        signed_sum += signed

    # Degenerate fallback
    if total_weight <= 1e-12:
        support_count = sum(1 for it in breakdown["items"] if it["stance"] == "support")
        contradict_count = sum(1 for it in breakdown["items"] if it["stance"] == "contradict")
        total = max(1, len(breakdown["items"]))
        avg_conf = (support_count - contradict_count) / total
    else:
        avg_conf = signed_sum / total_weight
        avg_conf = max(-1.0, min(1.0, avg_conf))

    # Death/murder nudge
    try:
        if _is_death_query(claim):
            death_strength = 0.0
            for it in breakdown["items"]:
                txt = (it.get("snippet") or "").lower()
                if _snippet_has_death_evidence(txt):
                    death_strength += float(it.get("semantic_sim", 0.0) or 0.0)
            if death_strength > 0:
                nudge = min(0.25, death_strength * 0.15)
                avg_conf = min(1.0, avg_conf + nudge)
    except Exception:
        pass

    percent = float((avg_conf + 1.0) / 2.0) * 100.0
    percent = max(0.0, min(100.0, percent))
    raw_label = _map_avg_conf_to_label(avg_conf)

    # Produce short picks
    support_items = [it for it in breakdown["items"] if it["signed"] > 0]
    contradict_items = [it for it in breakdown["items"] if it["signed"] < 0]
    neutral_items = [it for it in breakdown["items"] if it["signed"] == 0]

    def pick_top(list_items):
        if not list_items:
            return None
        # choose by abs(signed) * weight
        best = max(list_items, key=lambda it: abs(it["signed"]) * it["weight"])
        return {"publisher": best.get("publisher"), "url": best.get("url"), "snippet": best.get("snippet")}

    top_support = pick_top(support_items)
    top_contradict = pick_top(contradict_items)

    s_count = len(support_items)
    c_count = len(contradict_items)
    n_count = len(neutral_items)
    total_count = len(breakdown["items"])

    parts = []
    parts.append(f"{s_count} supporting, {c_count} contradicting, {n_count} neutral items (total {total_count}).")
    parts.append(f"Average confirmation across links: {avg_conf:+.3f} → {percent:.1f}% confidence.")
    if raw_label == "True":
        parts.append("Overall: evidence leans towards the claim being true.")
    elif raw_label == "False":
        parts.append("Overall: evidence leans towards the claim being false.")
    else:
        parts.append("Overall: mixed or insufficient evidence — inspect top links.")
    if top_support:
        parts.append(f"Top support: {top_support.get('publisher') or top_support.get('url')}: \"{top_support.get('snippet')}\"")
    if top_contradict:
        parts.append(f"Top contradict: {top_contradict.get('publisher') or top_contradict.get('url')}: \"{top_contradict.get('snippet')}\"")

    summary = " ".join(parts)

    breakdown.update({
        "total_weight": total_weight,
        "signed_sum": signed_sum,
        "avg_conf": avg_conf,
        "support_count": s_count,
        "contradict_count": c_count,
        "neutral_count": n_count,
        "top_support": top_support,
        "top_contradict": top_contradict,
    })

    # Conservative remap when degenerate
    if total_weight <= 1e-12 and abs(avg_conf) < 0.05:
        if verbose:
            return "Unverifiable", 25.0, "No strong evidence found across returned links.", breakdown
        return "Unverifiable", 25.0, "No strong evidence found across returned links.", {}

    if verbose:
        return raw_label, percent, summary, breakdown
    return raw_label, percent, summary, {}


# def aggregate_verdict(claim: str, evidence: list):
#     support_score = 0.0
#     contradict_score = 0.0
#     for e in evidence:
#         weight = e.get("semantic_sim", 0.0) * e.get("stance_conf", 0.0)
#         if e["stance"] == "support":
#             support_score += weight
#         elif e["stance"] == "contradict":
#             contradict_score += weight

#     total = support_score + contradict_score + 1e-8
#     if support_score > contradict_score * 1.2:
#         verdict = "True"
#         confidence = 60 + 40 * (support_score / (total + 1e-8))
#     elif contradict_score > support_score * 1.2:
#         verdict = "False"
#         confidence = 60 + 40 * (contradict_score / (total + 1e-8))
#     elif max(support_score, contradict_score) < 0.02:
#         verdict = "Unverifiable"
#         confidence = 25
#     else:
#         verdict = "Mixture"
#         confidence = 50

#     # choose top evidence for summary
#     top = None
#     best_val = 0.0
#     for e in evidence:
#         val = e.get("semantic_sim", 0.0) * e.get("stance_conf", 0.0)
#         if val > best_val:
#             best_val = val
#             top = e
#     if top:
#         summary = f"Top evidence from {top.get('publisher') or top.get('url')}: \"{top.get('snippet')[:200]}...\" (stance: {top.get('stance')})"
#     else:
#         summary = "No clear evidence found."
#     return verdict, min(100, confidence), summary
