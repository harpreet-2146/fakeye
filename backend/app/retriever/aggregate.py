# app/retriever/aggregate.py
"""
Aggregates evidence to produce a final verdict.
Key improvements:
- Better distinction between FALSE and UNVERIFIABLE
- Geographic claims are treated as factual (no support = FALSE)
- Stricter thresholds for TRUE verdicts
"""

import math
import re
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

def _is_geographic_claim(claim: str) -> bool:
    """Check if this is a geographic/location claim"""
    claim_lower = claim.lower()
    geo_patterns = [
        r'is\s+\w+\s+in\s+\w+',
        r'is\s+\w+\s+part\s+of\s+\w+',
        r'is\s+\w+\s+located\s+in\s+\w+',
        r'does\s+\w+\s+belong\s+to\s+\w+',
    ]
    return any(re.search(pattern, claim_lower) for pattern in geo_patterns)

def _is_factual_claim(claim: str) -> bool:
    """Check if this is a verifiable factual claim (should be TRUE or FALSE, not Unverifiable)"""
    claim_lower = claim.lower()
    
    # Geographic claims are factual
    if _is_geographic_claim(claim):
        return True
    
    # "Is X a Y" type claims
    if re.search(r'\bis\s+\w+\s+(a|an|the)\s+\w+', claim_lower):
        return True
    
    # "Does X have/contain Y" type claims
    if re.search(r'\bdoes\s+\w+\s+(have|contain|include)', claim_lower):
        return True
    
    return False

def _map_avg_conf_to_label(avg_conf: float, is_factual: bool = False) -> str:
    """
    Map average confidence to a label.
    For factual claims: no support = FALSE (not Unverifiable)
    """
    if math.isnan(avg_conf):
        return "Unverifiable"
    
    # For factual claims, tighten the mixture range
    if is_factual:
        if avg_conf <= -0.05:  # Any lean toward contradict = FALSE
            return "False"
        elif avg_conf >= 0.15:  # Need more evidence for TRUE
            return "True"
        else:
            return "False"  # Factual claims with no support = FALSE
    
    # For non-factual claims (opinions, predictions, etc.)
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
    is_factual = _is_factual_claim(claim)
    is_geographic = _is_geographic_claim(claim)

    if not evidence:
        if is_factual:
            # Factual claims with no evidence = likely FALSE
            raw, pct, summ = "False", 20.0, "No evidence found supporting this claim."
        else:
            raw, pct, summ = "Unverifiable", 25.0, "No evidence found. Unable to verify claim."
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
            # For factual claims, neutral with high similarity = slight negative
            # (the evidence exists but doesn't support the claim)
            if is_factual and sim > 0.5:
                signed = -0.1 * sim  # Slight negative push
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

        total_weight += abs(weight) if weight != 0 else 0.01  # Avoid zero division
        signed_sum += signed

    # Calculate average confidence
    if total_weight <= 1e-12:
        support_count = sum(1 for it in breakdown["items"] if it["stance"] == "support")
        contradict_count = sum(1 for it in breakdown["items"] if it["stance"] == "contradict")
        neutral_count = sum(1 for it in breakdown["items"] if it["stance"] == "neutral")
        total = max(1, len(breakdown["items"]))
        
        # For factual claims with all neutral = lean toward FALSE
        if is_factual and neutral_count == total:
            avg_conf = -0.3  # Push toward FALSE
        else:
            avg_conf = (support_count - contradict_count) / total
    else:
        avg_conf = signed_sum / total_weight
        avg_conf = max(-1.0, min(1.0, avg_conf))
        
        # For factual claims, if no support found, push toward FALSE
        support_count = sum(1 for it in breakdown["items"] if it["stance"] == "support")
        if is_factual and support_count == 0:
            avg_conf = min(avg_conf, -0.2)  # Push toward FALSE

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

    # Calculate percent
    percent = float((avg_conf + 1.0) / 2.0) * 100.0
    percent = max(0.0, min(100.0, percent))
    
    raw_label = _map_avg_conf_to_label(avg_conf, is_factual)

    # Separate by stance
    support_items = [it for it in breakdown["items"] if it["signed"] > 0]
    contradict_items = [it for it in breakdown["items"] if it["signed"] < 0]
    neutral_items = [it for it in breakdown["items"] if abs(it["signed"]) < 0.01]

    def pick_top(list_items):
        if not list_items:
            return None
        best = max(list_items, key=lambda it: abs(it["signed"]) * it["weight"])
        return {"publisher": best.get("publisher"), "url": best.get("url"), "snippet": best.get("snippet")}

    top_support = pick_top(support_items)
    top_contradict = pick_top(contradict_items)

    s_count = len(support_items)
    c_count = len(contradict_items)
    n_count = len(neutral_items)

    # === CLEAN SUMMARY GENERATION ===
    if raw_label == "True":
        if s_count >= 5:
            summary = f"Found {s_count} supporting sources confirming this claim."
        elif s_count >= 2:
            summary = f"Multiple sources ({s_count}) support this claim."
        else:
            summary = "Evidence suggests this claim is likely true."
    
    elif raw_label == "False":
        if c_count >= 3:
            summary = f"Found {c_count} sources contradicting this claim."
        elif c_count >= 1:
            summary = f"{c_count} source(s) contradict this claim."
        elif is_geographic:
            summary = "This geographic claim appears to be incorrect."
        elif is_factual:
            summary = "No credible evidence supports this factual claim."
        else:
            summary = "Limited or no credible evidence supporting this claim."
    
    else:  # Mixture or Unverifiable
        if s_count > 0 and c_count > 0:
            summary = f"Mixed evidence: {s_count} supporting, {c_count} contradicting. Review sources carefully."
        elif n_count >= 5:
            summary = "Insufficient evidence. Sources are unclear or off-topic."
        else:
            summary = "Unable to verify. Limited relevant sources found."
    
    # Add confidence indicator
    if percent >= 80:
        confidence_text = "High confidence"
    elif percent >= 60:
        confidence_text = "Moderate confidence"
    elif percent <= 20:
        confidence_text = "High confidence (FALSE)"
    elif percent <= 40:
        confidence_text = "Low confidence"
    else:
        confidence_text = "Uncertain"
    
    summary = f"{confidence_text}. {summary}"

    breakdown.update({
        "total_weight": total_weight,
        "signed_sum": signed_sum,
        "avg_conf": avg_conf,
        "support_count": s_count,
        "contradict_count": c_count,
        "neutral_count": n_count,
        "top_support": top_support,
        "top_contradict": top_contradict,
        "is_factual": is_factual,
        "is_geographic": is_geographic,
    })

    # Conservative remap when degenerate
    if total_weight <= 1e-12 and abs(avg_conf) < 0.05:
        if is_factual:
            summary = "No evidence supports this factual claim."
            if verbose:
                return "False", 20.0, summary, breakdown
            return "False", 20.0, summary, {}
        else:
            summary = "No strong evidence found. Unable to verify claim."
            if verbose:
                return "Unverifiable", 25.0, summary, breakdown
            return "Unverifiable", 25.0, summary, {}

    if verbose:
        return raw_label, percent, summary, breakdown
    return raw_label, percent, summary, {}