"""InnerSelf cognitive-function explorer: entirely local inference."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cognitive import FUNCTIONS, match_stacks, score_answers
from database import health_status as database_health, save_feedback, save_submission
from local_llm import availability, enhance_reflection
from ml_local import analyze_reasons, load_classifier
from narrative import build_reflection
from questions import CHOICES, QUESTIONS, QUESTION_BY_ID, QUESTIONNAIRE_VERSION, SECTIONS

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
logger = logging.getLogger(__name__)
app = FastAPI(title="InnerSelf Cognitive", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
if (BASE_DIR / "famous-people").is_dir():
    app.mount("/famous-people", StaticFiles(directory=BASE_DIR / "famous-people"), name="famous-people")


@app.middleware("http")
async def response_headers(request: Request, call_next):
    if request.url.path == "/submit":
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                return JSONResponse({"detail": "Jawaban terlalu panjang. Maksimum 64 KB."}, status_code=413)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://commons.wikimedia.org https://upload.wikimedia.org https://thumb.wikimedia.org; "
        "font-src 'self'; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )
    if request.url.path in ("/submit", "/feedback", "/questions", "/health", "/famous_people.json"):
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
    return {"version": QUESTIONNAIRE_VERSION, "sections": SECTIONS, "choices": CHOICES,
            "questions": [{k: q[k] for k in ("id", "section", "text")} for q in QUESTIONS],
            "local_llm_status": availability(), "database_status": database_health(),
            "analysis": "local_only"}


@app.get("/health")
def health():
    try:
        load_classifier()
        status = "ready"
    except (OSError, ValueError, EOFError, KeyError):
        status = "unavailable"
    return {"status": "ok", "questionnaire_version": QUESTIONNAIRE_VERSION,
            "classifier": status, "narrator": availability(), "database": database_health(),
            "external_ai": False, "training_data": "synthetic", "real_world_validation": "not_performed"}


@app.get("/famous_people.json")
def famous_people():
    try:
        data = json.loads((BASE_DIR / "famous_people.json").read_text(encoding="utf-8"))
        for people in data.values():
            for person in people:
                image = person.get("image", "")
                path = (BASE_DIR / image).resolve()
                local = "/" + image if image and path.is_relative_to(BASE_DIR / "famous-people") and path.is_file() else None
                remote = person.get("image_url", "")
                parsed = urlparse(remote)
                trusted_remote = remote if (
                    parsed.scheme == "https"
                    and parsed.hostname == "commons.wikimedia.org"
                    and parsed.path.startswith("/wiki/Special:Redirect/file/")
                ) else None
                person["image"] = local or trusted_remote
                person.pop("image_url", None)
        return data
    except (OSError, ValueError, TypeError):
        return {}


class AnswerItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int = Field(strict=True, ge=1)
    choice: int | str
    reason: str = Field(default="", max_length=600)

    @field_validator("choice", mode="before")
    @classmethod
    def validate_choice(cls, value):
        if value == "neutral" or (type(value) is int and value in (-3, -2, -1, 1, 2, 3)):
            return value
        raise ValueError("Pilih -3,-2,-1,neutral,1,2,3; netral bukan angka 0.")


class Submission(BaseModel):
    version: str
    answers: list[AnswerItem] = Field(min_length=len(QUESTIONS), max_length=len(QUESTIONS))
    user_name: str = Field(default="", max_length=60)
    user_age: int | None = Field(default=None, strict=True, ge=13, le=100)
    user_gender: Literal["", "Perempuan", "Laki-laki", "Nonbiner"] = ""
    use_local_llm: bool = Field(default=False, strict=True)
    allow_research_storage: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def complete_questionnaire(self):
        if self.version != QUESTIONNAIRE_VERSION:
            raise ValueError("Versi tes berubah. Muat ulang dan isi pertanyaan fungsi kognitif yang baru.")
        if {a.id for a in self.answers} != set(QUESTION_BY_ID):
            raise ValueError("Jawab setiap pertanyaan tepat satu kali.")
        return self


class FeedbackSubmission(BaseModel):
    session_id: str = Field(min_length=36, max_length=36)
    agrees: bool = Field(strict=True)
    answer_id: int | None = Field(default=None, strict=True, ge=1, le=len(QUESTIONS))
    corrected_function: Literal["Te", "Ti", "Fe", "Fi", "Ne", "Ni", "Se", "Si"] | None = None
    comment: str = Field(default="", max_length=1000)


@app.post("/feedback")
def submit_feedback(data: FeedbackSubmission):
    try:
        saved = save_feedback(data.session_id, data.agrees, data.comment,
                              answer_id=data.answer_id, corrected_function=data.corrected_function)
    except Exception:
        logger.exception("Feedback database write failed")
        return JSONResponse({"success": False, "detail": "Database belum tersedia."}, status_code=503)
    if not saved:
        return JSONResponse({"success": False, "detail": "Sesi tidak ditemukan atau database tidak aktif."}, status_code=404)
    return {"success": True}


@app.post("/submit")
def submit_test(data: Submission):
    predictions, model_status = analyze_reasons(data.answers)
    functions, contributions = score_answers(data.answers, predictions)
    scoring = match_stacks({f: d["questionnaire_index"] for f, d in functions.items()})
    decision = match_stacks({f: d["index"] for f, d in functions.items()})
    reflection = build_reflection(data.answers, predictions, functions, decision,
                                  name=data.user_name, age=data.user_age, gender=data.user_gender)
    if data.use_local_llm:
        reflection = enhance_reflection(reflection, decision)

    stored_session_id = None
    storage_status = "not_requested"
    if data.allow_research_storage:
        try:
            stored_session_id = save_submission(data, predictions, functions, decision, scoring["type"])
            storage_status = "saved" if stored_session_id else "disabled"
        except Exception:
            logger.exception("MySQL research storage failed")
            storage_status = "unavailable"

    warnings = ["Model dilatih pada data sintetis. Belum ada pengukuran akurasi pada responden nyata."]
    if model_status != "ready":
        warnings.append("Model teks lokal belum dapat dimuat. Hasil ini memakai pilihan jawaban; analisis alasan tidak memengaruhi skor.")
    if data.allow_research_storage and storage_status == "unavailable":
        warnings.append("Hasil tes berhasil dihitung, tetapi data riset belum dapat disimpan ke database lokal.")

    return {
        "success": True, "schema_version": 3, "questionnaire_version": QUESTIONNAIRE_VERSION,
        "user_name": data.user_name.strip(), "final_result": decision["type"],
        "user_age": data.user_age, "user_gender": data.user_gender,
        "questionnaire_result": scoring["type"], "is_adjusted": scoring["type"] != decision["type"],
        "decision": decision, "function_stack": decision["stack"],
        "functions": {f: {**FUNCTIONS[f], **value} for f, value in functions.items()},
        "answer_contributions": contributions, "reflection": reflection,
        "neutral_count": sum(a.choice == "neutral" for a in data.answers),
        "reason_count": sum(bool(a.reason.strip()) for a in data.answers),
        "recognized_reason_count": sum(p["accepted"] for p in predictions.values()),
        "model_status": model_status, "training_data_source": "synthetic", "warnings": warnings,
        "research_storage": storage_status, "research_session_id": stored_session_id,
        "external_ai": False, "total_questions": len(data.answers),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
