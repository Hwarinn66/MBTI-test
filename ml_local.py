"""Portable TF-IDF + logistic model inference, using only the Python stdlib.

JSON coefficients are data, not executable pickle. No networking or downloads.
Scores describe synthetic class recognition; not real-person confidence.
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

    def predict(self, reason):
        reason = reason.strip()
        empty = {"accepted": False, "function": None, "stance": "unknown", "model_score": 0.0,
                 "evidence": reason, "status": "empty" if not reason else "unclear"}
        if len(TOKEN_RE.findall(reason)) < 4:
            return empty
        # Typing assertions / prompt commands are not behavioral evidence.
        if re.search(r"\b(?:INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)\b|abaikan (?:instruksi|aturan)|system prompt", reason, re.I):
            return {**empty, "status": "unsupported"}
        probs = self.probabilities(reason)
        label, score = max(probs.items(), key=lambda p: p[1])

        # Be defensive with older/newer datasets that may encode unknown either
        # as "unknown" or "unknown:unknown". Unknown is always an abstention,
        # never a cognitive function to feed into scoring.
        if label == "unknown" or label.startswith("unknown:") or score < self.model["threshold"]:
            return {**empty, "model_score": round(score, 4)}

        parts = label.split(":", 1)
        if len(parts) != 2:
            return {**empty, "status": "invalid_label", "model_score": round(score, 4)}
        f, stance = parts
        if f not in {"Te", "Ti", "Fe", "Fi", "Ne", "Ni", "Se", "Si"} or stance not in {"support", "oppose", "mixed"}:
            return {**empty, "status": "invalid_label", "model_score": round(score, 4)}

        negative = bool(re.search(r"\b(tidak|tak|bukan|jarang|enggan|belum|kurang)\b", normalize(reason)))
        situational = bool(re.search(r"\b(kadang|tergantung|bergantung|kalau|kecuali|sesekali|tapi|tetapi)\b", normalize(reason)))
        # Conservative guards: a bag-of-ngrams model cannot reliably resolve
        # the scope of negation. Abstain instead of reversing the user's words.
        if (stance == "support" and negative) or (stance == "oppose" and not negative) or (stance == "mixed" and not situational):
            return {**empty, "status": "ambiguous_language", "model_score": round(score, 4)}
        return {**empty, "accepted": True, "function": f, "stance": stance,
                "model_score": round(score, 4), "status": "recognized"}


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
