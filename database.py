"""Optional MySQL persistence for consented, pseudonymous language research data."""
from __future__ import annotations

import json
import os
import re
import uuid
from contextlib import contextmanager

from ml_local import normalize


def enabled():
    return os.getenv("DB_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}


def _config():
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "innerself_mbti"),
        "charset": "utf8mb4",
        "autocommit": False,
    }


@contextmanager
def connection():
    if not enabled():
        yield None
        return
    import pymysql
    conn = pymysql.connect(**_config())
    try:
        yield conn
    finally:
        conn.close()


def health_status():
    if not enabled():
        return "disabled"
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return "ready"
    except Exception:
        return "unavailable"


def language_flags(text: str):
    low = text.casefold()
    slang_tokens = re.findall(r"\b(?:gue|gua|gw|lu|lo|gak|ga|nggak|enggak|kalo|klo|krn|udh|udah|bgt|yg|dgn|utk|aja|bikin|pake|ngelist|mikirin|nyari|ngerti)\b", low)
    english_tokens = re.findall(r"\b(?:list|deadline|target|result|progress|option|approach|pattern|plan|check|compare|adjust|vibe|to\s*do)\b", low)
    negation = bool(re.search(r"\b(?:tidak|tak|bukan|jarang|gak|ga|nggak|enggak|belum|kurang)\b", low))
    situational = bool(re.search(r"\b(?:kadang|tergantung|bergantung|kalau|kalo|klo|kecuali|sesekali|tapi|tetapi|namun)\b", low))
    return {
        "has_slang": bool(slang_tokens),
        "slang_tokens": sorted(set(slang_tokens)),
        "has_code_mix": bool(english_tokens),
        "english_tokens": sorted(set(english_tokens)),
        "has_negation": negation,
        "has_situational_language": situational,
        "token_count": len(re.findall(r"(?u)\b\w+\b", text)),
    }


def save_submission(data, predictions, functions, decision, questionnaire_result):
    """Persist one consented test. Returns public session UUID or None."""
    if not enabled() or not getattr(data, "allow_research_storage", False):
        return None

    public_id = str(uuid.uuid4())
    with connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO test_sessions
                       (public_id, questionnaire_version, mbti_result, questionnaire_result,
                        age, gender, reason_count, neutral_count, consent_language_research)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1)""",
                    (public_id, data.version, decision.get("type"), questionnaire_result,
                     data.user_age, data.user_gender or None,
                     sum(bool(a.reason.strip()) for a in data.answers),
                     sum(a.choice == "neutral" for a in data.answers)),
                )
                session_id = cur.lastrowid

                for answer in data.answers:
                    reason = answer.reason.strip()
                    pred = predictions.get(answer.id, {})
                    flags = language_flags(reason) if reason else {
                        "has_slang": False, "slang_tokens": [], "has_code_mix": False,
                        "english_tokens": [], "has_negation": False,
                        "has_situational_language": False, "token_count": 0,
                    }
                    cur.execute(
                        """INSERT INTO answers
                           (session_id, question_id, choice_value, reason_raw, reason_normalized,
                            predicted_function, predicted_stance, raw_model_score, model_status,
                            token_count, has_slang, has_code_mix, has_negation,
                            has_situational_language, language_features_json)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (session_id, answer.id, str(answer.choice), reason,
                         normalize(reason) if reason else "",
                         pred.get("function"), pred.get("stance"), pred.get("raw_model_score", 0.0),
                         pred.get("status"), flags["token_count"], flags["has_slang"],
                         flags["has_code_mix"], flags["has_negation"],
                         flags["has_situational_language"], json.dumps(flags, ensure_ascii=False)),
                    )

                values = []
                for f in ("Te", "Ti", "Fe", "Fi", "Ne", "Ni", "Se", "Si"):
                    d = functions.get(f, {})
                    values.extend([d.get("questionnaire_index", 50.0), d.get("index", 50.0)])
                cur.execute(
                    """INSERT INTO function_scores
                       (session_id, te_questionnaire, te_final, ti_questionnaire, ti_final,
                        fe_questionnaire, fe_final, fi_questionnaire, fi_final,
                        ne_questionnaire, ne_final, ni_questionnaire, ni_final,
                        se_questionnaire, se_final, si_questionnaire, si_final)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (session_id, *values),
                )
            conn.commit()
            return public_id
        except Exception:
            conn.rollback()
            raise


def save_feedback(public_id: str, agrees: bool, comment: str = "", answer_id: int | None = None, corrected_function: str | None = None):
    if not enabled():
        return False
    with connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM test_sessions WHERE public_id=%s", (public_id,))
                row = cur.fetchone()
                if not row:
                    return False
                session_id = row[0]
                database_answer_id = None
                if answer_id is not None:
                    cur.execute("SELECT id FROM answers WHERE session_id=%s AND question_id=%s", (session_id, answer_id))
                    answer_row = cur.fetchone()
                    if not answer_row:
                        return False
                    database_answer_id = answer_row[0]
                cur.execute(
                    """INSERT INTO feedback
                       (session_id, answer_id, user_agrees, corrected_function, comment)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (session_id, database_answer_id, agrees, corrected_function, comment.strip()[:1000] or None),
                )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
