from app.models.nli import NLIModel

nli = NLIModel()

def predict_stance(claim: str, snippet: str):
    """
    Returns dict with keys: entailment, neutral, contradiction (probabilities)
    NOTE: model label mapping is handled in NLIModel (see models/nli.py)
    """
    return nli.predict_entailment(claim, snippet)
