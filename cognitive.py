"""Exploratory scoring. Indices and stack fits are NOT probabilities.

Eight functions are scored FIRST. Letters label the closest canonical stack.
"""
import math
from questions import QUESTION_BY_ID

FUNCTIONS = {
    "Te": {"name": "Extraverted Thinking", "title": "Mengatur hasil", "meaning": "menilai efektivitas lewat hasil, ukuran, dan pengaturan langkah kerja"},
    "Ti": {"name": "Introverted Thinking", "title": "Memeriksa logika", "meaning": "memeriksa konsistensi penjelasan, definisi, dan cara kerja di baliknya"},
    "Fe": {"name": "Extraverted Feeling", "title": "Merawat kesepahaman", "meaning": "mempertimbangkan kebutuhan bersama dan menyesuaikan komunikasi dalam hubungan"},
    "Fi": {"name": "Introverted Feeling", "title": "Menjaga nilai pribadi", "meaning": "menimbang keselarasan pilihan dengan nilai dan nurani pribadi"},
    "Ne": {"name": "Extraverted Intuition", "title": "Membuka kemungkinan", "meaning": "menghubungkan gagasan dan menjelajahi beberapa alternatif"},
    "Ni": {"name": "Introverted Intuition", "title": "Merangkai arah", "meaning": "merangkum petunjuk menjadi benang merah dan gambaran arah jangka panjang"},
    "Se": {"name": "Extraverted Sensing", "title": "Menanggapi keadaan", "meaning": "memperhatikan keadaan konkret saat ini dan belajar lewat tindakan langsung"},
    "Si": {"name": "Introverted Sensing", "title": "Menautkan pengalaman", "meaning": "membandingkan keadaan sekarang dengan detail pengalaman yang pernah dialami"},
}
FUNCTION_STACKS = {
    "INTJ": ["Ni", "Te", "Fi", "Se"], "INTP": ["Ti", "Ne", "Si", "Fe"],
    "ENTJ": ["Te", "Ni", "Se", "Fi"], "ENTP": ["Ne", "Ti", "Fe", "Si"],
    "INFJ": ["Ni", "Fe", "Ti", "Se"], "INFP": ["Fi", "Ne", "Si", "Te"],
    "ENFJ": ["Fe", "Ni", "Se", "Ti"], "ENFP": ["Ne", "Fi", "Te", "Si"],
    "ISTJ": ["Si", "Te", "Fi", "Ne"], "ISFJ": ["Si", "Fe", "Ti", "Ne"],
    "ESTJ": ["Te", "Si", "Ne", "Fi"], "ESFJ": ["Fe", "Si", "Ne", "Ti"],
    "ISTP": ["Ti", "Se", "Ni", "Fe"], "ISFP": ["Fi", "Se", "Ni", "Te"],
    "ESTP": ["Se", "Ti", "Fe", "Ni"], "ESFP": ["Se", "Fi", "Te", "Ni"],
}
STACK_LEVELS = (0.90, 0.75, 0.45, 0.20)
TEXT_WEIGHT = 1.5  # at most half of one strong questionnaire response per reason


def prototype(type_name):
    scores = dict.fromkeys(FUNCTIONS, 0.30)
    scores.update(zip(FUNCTION_STACKS[type_name], STACK_LEVELS))
    return scores


def score_contributions(choice, direction=1):
    """Retain BOTH observations for neutral, never reduce (-1,+1) to zero."""
    if choice == "neutral":
        return [-1, 1]
    if type(choice) is not int or choice not in (-3, -2, -1, 1, 2, 3):
        raise ValueError("Gunakan kategori neutral, bukan angka 0.")
    return [choice * direction]


def score_answers(answers, text_predictions=None):
    totals = {f: {"support": 0.0, "opposition": 0.0, "neutral_count": 0,
                  "text_support": 0.0, "text_opposition": 0.0} for f in FUNCTIONS}
    evidence, seen_text = [], set()
    for answer in answers:
        q = QUESTION_BY_ID[answer.id]
        values = score_contributions(answer.choice, q["direction"])
        target = totals[q["function"]]
        for value in values:
            target["support" if value > 0 else "opposition"] += abs(value)
        target["neutral_count"] += answer.choice == "neutral"
        evidence.append({"id": answer.id, "function": q["function"], "contributions": values})
        pred = (text_predictions or {}).get(answer.id, {})
        normalized = " ".join(answer.reason.casefold().split())
        if pred.get("accepted") and normalized and normalized not in seen_text:
            seen_text.add(normalized)
            f, stance = pred["function"], pred["stance"]
            weight = TEXT_WEIGHT * pred["model_score"]
            if stance in ("support", "mixed"):
                totals[f]["text_support"] += weight
            if stance in ("oppose", "mixed"):
                totals[f]["text_opposition"] += weight
    detail = {}
    for f, t in totals.items():
        s, o = t["support"], t["opposition"]
        ts, to = t["text_support"], t["text_opposition"]
        base = 100 * s / (s + o) if s + o else 50.0
        combined = 100 * (s + ts) / (s + o + ts + to) if s + o + ts + to else 50.0
        detail[f] = {**{k: round(v, 4) for k, v in t.items()},
                     "questionnaire_index": round(base, 2), "index": round(combined, 2),
                     "situational_ratio": round(t["neutral_count"] / 4, 2)}
    return detail, evidence


def match_stacks(indices):
    """Centered cosine over all eight values, not merely sorted top four."""
    values = [indices[f] for f in FUNCTIONS]
    mean = sum(values) / len(values)
    centered = [x - mean for x in values]
    norm = math.sqrt(sum(x*x for x in centered))
    candidates = []
    for name, stack in FUNCTION_STACKS.items():
        p = prototype(name)
        pm = sum(p.values()) / len(p)
        vector = [p[f] - pm for f in FUNCTIONS]
        similarity = sum(a*b for a, b in zip(centered, vector)) / (norm * math.sqrt(sum(x*x for x in vector))) if norm else 0
        candidates.append({"type": name, "stack": stack, "fit": round((similarity + 1) * 50, 2)})
    candidates.sort(key=lambda c: (-c["fit"], c["type"]))
    gap = round(candidates[0]["fit"] - candidates[1]["fit"], 2)
    flat = max(values) - min(values) < 3
    tied = gap < 0.01
    result = None if flat or tied else candidates[0]["type"]
    status = "undetermined" if result is None else "tentative" if gap < 3 or candidates[0]["fit"] < 75 else "exploratory"
    return {"type": result, "status": status, "gap": gap,
            "candidates": candidates, "stack": FUNCTION_STACKS.get(result, [])}
