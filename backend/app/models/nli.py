from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

class NLIModel:
    def __init__(self, model_name: str = "roberta-large-mnli"):
        # roberta-large-mnli label order is [entailment, neutral, contradiction] for some wrappers,
        # but HuggingFace mapping for many models is: 0->entailment, 1->neutral, 2->contradiction.
        # We will assume standard HF mapping but check if you swap models.
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()
        self.label_map = {0: "entailment", 1: "neutral", 2: "contradiction"}

    def predict_entailment(self, premise: str, hypothesis: str):
        # premise = claim, hypothesis = snippet
        inputs = self.tokenizer.encode_plus(premise, hypothesis, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        # map to dict
        res = {}
        for i, lab in self.label_map.items():
            res[lab] = float(probs[i])
        # return in keys: entailment, neutral, contradiction
        return {"entailment": res.get("entailment", 0.0), "neutral": res.get("neutral", 0.0), "contradiction": res.get("contradiction", 0.0)}
