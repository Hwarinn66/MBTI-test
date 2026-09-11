"""InnerSelf: same-origin FastAPI application and canonical questionnaire scoring."""
from __future__ import annotations

import itertools
import json
import logging
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from questions import DIMENSIONS, QUESTIONS, QUESTION_BY_ID, QUESTIONNAIRE_VERSION

BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)
app = FastAPI(title="InnerSelf", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
if (BASE_DIR / "famous-people").is_dir():
    app.mount("/famous-people", StaticFiles(directory=BASE_DIR / "famous-people"), name="famous-people")


@app.middleware("http")
async def response_headers(request: Request, call_next):
    # Reject oversized submissions before schema validation.
    if request.url.path == "/submit":
        body = await request.body()
        if len(body) > 65536:
            return JSONResponse({"detail": "Jawaban terlalu panjang. Maksimum 64 KB."}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )
    if request.url.path in ("/submit", "/questions", "/famous_people.json"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
@app.get("/index.html", include_in_schema=False)
def index():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/result.html")
def result_page():
    return FileResponse(BASE_DIR / "result.html")


@app.get("/questions")
def questionnaire():
    return {
        "version": QUESTIONNAIRE_VERSION,
        "dimensions": DIMENSIONS,
        "questions": [{k: q[k] for k in ("id", "dimension", "text")} for q in QUESTIONS],
    }


@app.get("/famous_people.json")
def famous_people():
    try:
        data = json.loads((BASE_DIR / "famous_people.json").read_text(encoding="utf-8"))
        for people in data.values():
            for person in people:
                image_path = person.get("image", "")
                path = (BASE_DIR / image_path).resolve()
                # Return only present local assets; initials work without photos.
                person["image"] = "/" + image_path if image_path and path.is_relative_to(BASE_DIR / "famous-people") and path.is_file() else None
        return data
    except (OSError, ValueError, TypeError):
        logger.warning("Famous people data unavailable")
        return {}


class AnswerItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int = Field(strict=True, ge=1)
    score: int = Field(strict=True, ge=-3, le=3)
    reason: str = Field(default="", max_length=600)


class Submission(BaseModel):
    version: str
    answers: list[AnswerItem] = Field(min_length=len(QUESTIONS), max_length=len(QUESTIONS))
    user_name: str = Field(default="", max_length=60)
    user_age: int | None = Field(default=None, strict=True, ge=13, le=100)
    user_gender: Literal["", "Perempuan", "Laki-laki", "Tidak disebutkan"] = ""
    use_ai: bool = False

    @model_validator(mode="after")
    def complete_questionnaire(self):
        if self.version != QUESTIONNAIRE_VERSION:
            raise ValueError("Versi pertanyaan berubah. Muat ulang tes sebelum mengirim.")
        if {a.id for a in self.answers} != set(QUESTION_BY_ID):
            raise ValueError("Jawab setiap pertanyaan tepat satu kali.")
        return self


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


def calculate_math_score(answers):
    scores = dict.fromkeys("EISNTFJP", 0.0)
    neutrals = 0
    for answer in answers:
        question = QUESTION_BY_ID[answer.id]
        first, second = question["dimension"]
        if answer.score == 0:
            scores[first] += 0.5
            scores[second] += 0.5
            neutrals += 1
        else:
            agree = question["agree_letter"]
            letter = agree if answer.score > 0 else (second if agree == first else first)
            scores[letter] += abs(answer.score)
    margins = {d: abs(scores[d[0]] - scores[d[1]]) for d in DIMENSIONS}
    result = "".join("X" if margins[d] == 0 else (d[0] if scores[d[0]] > scores[d[1]] else d[1]) for d in DIMENSIONS)
    return result, scores, 100 * neutrals / len(answers) if answers else 0, margins


def calculate_cognitive_functions(mbti_type, scores):
    stack = FUNCTION_STACKS.get(mbti_type, [])
    if not stack:
        return {}, []
    base = dict(zip(stack, [45, 38, 22, 12]))
    # N preference increases intuitive functions; S increases sensing functions.
    ei = (scores["E"] - scores["I"]) / 1.8
    sn = (scores["N"] - scores["S"]) / 1.95
    tf = (scores["T"] - scores["F"]) / 1.95
    adjustments = {
        "Ne": sn + max(ei, 0), "Ni": sn + max(-ei, 0),
        "Se": -sn + max(ei, 0), "Si": -sn + max(-ei, 0),
        "Te": tf + max(ei, 0), "Ti": tf + max(-ei, 0),
        "Fe": -tf + max(ei, 0), "Fi": -tf + max(-ei, 0),
    }
    return {f: round(max(5, min(50, base.get(f, 8) + value)), 1) for f, value in adjustments.items()}, stack


def basic_analysis(result, scores, name):
    opening = f"Halo {name.strip()}!" if name.strip() else "Ini gambaran dari jawabanmu."
    paragraphs = [opening]
    for dim, info in DIMENSIONS.items():
        first, second = dim
        if scores[first] == scores[second]:
            paragraphs.append(f"Pada dimensi {info['title'].lower()}, kedua sisi masih seimbang. Kamu belum menunjukkan kecenderungan yang lebih kuat pada salah satunya.")
        else:
            side = info['first'] if scores[first] > scores[second] else info['second']
            paragraphs.append(f"Pada dimensi {info['title'].lower()}, jawabanmu lebih mengarah ke {side}. Perhatikan kapan pola ini terasa sesuai dengan keseharianmu dan kapan kamu menggunakan sisi lainnya.")
    paragraphs.append("Gunakan hasil ini sebagai bahan refleksi. Preferensi bisa bergantung pada situasi; tes ini bukan diagnosis psikologis atau tes MBTI resmi.")
    return "\n\n".join(paragraphs)


@app.post("/submit")
def submit_test(data: Submission):
    result, scores, neutral, margins = calculate_math_score(data.answers)
    percentages = {d: round(100 * scores[d[0]] / (scores[d[0]] + scores[d[1]]), 1) for d in DIMENSIONS}
    borderline = [d for d in DIMENSIONS if abs(percentages[d] - 50) < 10]
    candidates = ["".join(t) for t in itertools.product(*[d if result[i] == "X" else result[i] for i, d in enumerate(DIMENSIONS)])]
    cognitive, stack = calculate_cognitive_functions(result, scores)
    analysis = {
        "analysis_note": basic_analysis(result, scores, data.user_name),
        "ai_status": "not_requested", "dataset_similarity": None,
    }
    if data.use_ai:
        try:
            from psychologist import analyze_with_ai
            reasons = [{"id": a.id, "question_topic": QUESTION_BY_ID[a.id]["text"], "score": a.score, "reason": a.reason} for a in data.answers]
            analysis.update(analyze_with_ai(result, reasons, dimension_scores=scores, user_name=data.user_name, user_age=data.user_age, user_gender=data.user_gender))
        except Exception:
            # Optional integrations must never prevent a valid scored result.
            logger.warning("Optional AI analysis unavailable")
            analysis["ai_status"] = "unavailable"
    return {
        "success": True, "schema_version": 1, "questionnaire_version": QUESTIONNAIRE_VERSION,
        "math_result": result, "final_result": result, "is_corrected": False,
        "user_name": data.user_name.strip(), "ai_note": analysis["analysis_note"],
        "ai_status": analysis["ai_status"], "dataset_similarity": analysis.get("dataset_similarity"),
        "dimension_scores": scores, "dimension_percentages": percentages,
        "preference_clarity": round(sum(abs(percentages[d] - 50) * 2 for d in DIMENSIONS) / 4, 1),
        "neutral_percentage": neutral, "margins": margins, "borderline_dimensions": borderline,
        "candidate_types": candidates, "cognitive_scores": cognitive, "function_stack": stack,
        "total_questions": len(data.answers),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
