"""Portable TF-IDF + logistic model inference, using only the Python stdlib.

JSON coefficients are data, not executable pickle. No networking or downloads.
For every non-empty written reason, runtime returns the closest supported
cognitive-function class. Scores are retained for debugging/weighting only;
they no longer act as an abstention threshold.
"""
import gzip
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent / "models" / "cognitive_text.json.gz"
TOKEN_RE = re.compile(r"(?u)\b\w\w+\b")
VALID_FUNCTIONS = {"Te", "Ti", "Fe", "Fi", "Ne", "Ni", "Se", "Si"}
VALID_STANCES = {"support", "oppose", "mixed"}


def normalize(text):
    text = text.casefold()
    for informal, standard in ((r"\b(gak|nggak|ga|enggak)\b", "tidak"), (r"\bbgt\b", "banget"), (r"\bkrn\b", "karena")):
        text = re.sub(informal, standard, text)
    return text


def features(text):
    tokens = TOKEN_RE.findall(normalize(text))
    # Subword features help Indonesian affixes without fetching a language model.
    grams = []
    for token in tokens:
        word = " " + token + " "
        grams.extend("char:" + word[i:i+n] for n in (3, 4) for i in range(len(word)-n+1))
    return tokens + [a + " " + b for a, b in zip(tokens, tokens[1:])] + grams


class LocalClassifier:
    def __init__(self, model):
        if model.get("format") != "innerself-linear-v1":
            raise ValueError("Unsupported classifier")
        self.model = model

    def probabilities(self, text):
        counts = Counter(features(text))
        vocab = self.model["vocabulary"]
        weights = {vocab[token]: (1 + math.log(n)) * self.model["idf"][vocab[token]]
                   for token, n in counts.items() if token in vocab}
        norm = math.sqrt(sum(v*v for v in weights.values())) or 1
        weights = {i: v/norm for i, v in weights.items()}
        logits = [bias + sum(coeff[i]*v for i, v in weights.items())
                  for bias, coeff in zip(self.model["intercept"], self.model["coef"])]
        peak = max(logits)
        exp = [math.exp(x-peak) for x in logits]
        denom = sum(exp)
        return dict(zip(self.model["classes"], [x/denom for x in exp]))

    @staticmethod
    def _valid_label(label):
        parts = label.split(":", 1)
        return len(parts) == 2 and parts[0] in VALID_FUNCTIONS and parts[1] in VALID_STANCES

    def predict(self, reason):
        reason = reason.strip()
        empty = {"accepted": False, "function": None, "stance": "unknown", "model_score": 0.0,
                 "evidence": reason, "status": "empty" if not reason else "invalid_label"}
        if not reason:
            return empty

        probs = self.probabilities(reason)
        # Unknown remains useful during training/evaluation, but the product
        # behaviour requested here is best-match classification: every written
        # reason receives the closest one of the eight cognitive functions.
        candidates = [(label, score) for label, score in probs.items() if self._valid_label(label)]
        if not candidates:
            return empty
        label, score = max(candidates, key=lambda p: p[1])
        f, stance = label.split(":", 1)

        return {**empty, "accepted": True, "function": f, "stance": stance,
                "model_score": round(score, 4), "status": "best_match"}


@lru_cache(maxsize=1)
def load_classifier():
    with gzip.open(MODEL_PATH, "rt", encoding="utf-8") as handle:
        return LocalClassifier(json.load(handle))


def analyze_reasons(answers):
    try:
        classifier = load_classifier()
    except (OSError, ValueError, KeyError, EOFError):
        return {}, "unavailable"
    return {a.id: classifier.predict(a.reason) for a in answers}, "ready"
