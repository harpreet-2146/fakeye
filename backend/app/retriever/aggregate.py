def aggregate_verdict(claim: str, evidence: list):
    support_score = 0.0
    contradict_score = 0.0
    for e in evidence:
        weight = e.get("semantic_sim", 0.0) * e.get("stance_conf", 0.0)
        if e["stance"] == "support":
            support_score += weight
        elif e["stance"] == "contradict":
            contradict_score += weight

    total = support_score + contradict_score + 1e-8
    if support_score > contradict_score * 1.2:
        verdict = "True"
        confidence = 60 + 40 * (support_score / (total + 1e-8))
    elif contradict_score > support_score * 1.2:
        verdict = "False"
        confidence = 60 + 40 * (contradict_score / (total + 1e-8))
    elif max(support_score, contradict_score) < 0.02:
        verdict = "Unverifiable"
        confidence = 25
    else:
        verdict = "Mixture"
        confidence = 50

    # choose top evidence for summary
    top = None
    best_val = 0.0
    for e in evidence:
        val = e.get("semantic_sim", 0.0) * e.get("stance_conf", 0.0)
        if val > best_val:
            best_val = val
            top = e
    if top:
        summary = f"Top evidence from {top.get('publisher') or top.get('url')}: \"{top.get('snippet')[:200]}...\" (stance: {top.get('stance')})"
    else:
        summary = "No clear evidence found."
    return verdict, min(100, confidence), summary
