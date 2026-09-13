"""Evidence-grounded Indonesian reflection; no network calls, no invented quotes."""
import re
from collections import Counter
from cognitive import FUNCTIONS
from questions import CHOICES, QUESTION_BY_ID

LABELS = {c["value"]: c["label"] for c in CHOICES}


def question_insight(answer, prediction):
    q = QUESTION_BY_ID[answer.id]
    reason = answer.reason.strip()
    f = q["function"]
    neutral = answer.choice == "neutral"
    effective = 0 if neutral else answer.choice * q["direction"]
    relationship = "empty"

    if not reason:
        paragraphs = [f"Pada soal {q['id']}, kamu memilih {LABELS[answer.choice].lower()}."]
        if neutral:
            paragraphs.append("Pilihan netral tetap dihitung sebagai dua sisi yang tersimpan terpisah: dukungan dan penolakan. Karena tidak ada alasan tertulis, analisis bagian ini memakai pilihan jawaban saja.")
        else:
            action = "mendukung" if effective > 0 else "kurang mendukung"
            paragraphs.append(f"Dengan arah pernyataan soal ini, pilihanmu {action} pola {f}. Karena tidak ada alasan tertulis, fungsi tambahan tidak ditetapkan dari teks.")
    else:
        paragraphs = [f"Di soal {q['id']}, kamu memilih {LABELS[answer.choice].lower()}, lalu menulis: “{reason}”"]
        qualified = bool(re.search(r"\b(tapi|tetapi|namun|tergantung|kadang|kalau|kecuali)\b", reason, re.I))

        if prediction.get("accepted") and prediction.get("function") in FUNCTIONS:
            pf, stance = prediction["function"], prediction["stance"]
            info = FUNCTIONS[pf]
            prefix = f"Fungsi kognitif paling dekat dari alasan ini: {pf} ({info['name']}) — {info['title']}."
            if stance == "support":
                explanation = f"Isi alasanmu menunjukkan pola {pf}, yaitu {info['meaning']}."
            elif stance == "oppose":
                explanation = f"Isi alasanmu paling dekat dengan tema {pf}, tetapi melalui sikap yang berlawanan terhadap pola {info['meaning']}."
            else:
                explanation = f"Isi alasanmu paling dekat dengan {pf} dalam bentuk yang situasional atau bercampur, yaitu {info['meaning']}."
            paragraphs.append(f"{prefix} {explanation}")

            relationship = "qualified" if neutral or qualified or stance == "mixed" else "other_function" if pf != f else "aligned"
            if pf == f and not neutral and stance != "mixed":
                agrees = (effective > 0) == (stance == "support")
                if not agrees:
                    relationship = "contradictory"
                    paragraphs.append("Arah pilihan dan alasanmu berbeda, jadi sistem menyimpan keduanya sebagai dua sumber informasi yang tidak identik. Fungsi dari alasan tetap ditetapkan berdasarkan isi teks yang kamu tulis.")
            if pf != f:
                paragraphs.append(f"Soal ini terutama memeriksa {f}, sedangkan alasanmu diklasifikasikan paling dekat dengan {pf}. Karena itu alasanmu menambah konteks fungsi yang berbeda dari fungsi utama soal.")
        else:
            relationship = "unclear"
            paragraphs.append(f"Alasan ini belum dapat diklasifikasikan oleh model teks, sehingga pembahasan sementara mengikuti fungsi utama soal, yaitu {f}.")

        if neutral:
            paragraphs.append("Pilihan netralmu tetap membawa dukungan dan penolakan secara terpisah, sedangkan alasan tertulis menentukan fungsi kognitif yang paling dekat dari konteks yang kamu berikan.")

    return {"question_id": q["id"], "question": q["text"], "choice": answer.choice,
            "choice_label": LABELS[answer.choice], "question_function": f,
            "reason": reason, "relationship": relationship,
            "text_function": prediction.get("function") if prediction.get("accepted") else None,
            "text_stance": prediction.get("stance", "unknown"),
            "text_recognized": bool(prediction.get("accepted")),
            "text_score": prediction.get("model_score", 0.0),
            "paragraphs": paragraphs, "evidence": [reason] if reason else []}


def profile_opening(name, age, gender, reason_count):
    greeting = f"Halo {name.strip()}," if name.strip() else "Halo,"
    parts = [f"{greeting} aku asisten AI lokal yang akan menemanimu memahami hasil tes ini."]
    if gender and age is not None:
        parts.append(f"Kamu memperkenalkan diri sebagai {gender.lower()} berusia {age} tahun.")
    elif age is not None:
        parts.append(f"Kamu menyebut usiamu {age} tahun.")
    elif gender:
        parts.append(f"Kamu memperkenalkan diri sebagai {gender.lower()}.")
    if reason_count:
        parts.append(f"Kamu menuliskan alasan pada {reason_count} soal. Setiap alasan akan diklasifikasikan ke fungsi kognitif yang paling dekat, lalu dibaca bersama pola pilihan jawabanmu.")
    else:
        parts.append("Kamu belum menuliskan alasan, jadi hasil utama akan dibaca dari pola pilihan jawabanmu.")
    return " ".join(parts)


def _overall_conclusion(meaningful, functions, decision):
    counts = Counter(i["text_function"] for i in meaningful if i["text_function"] in FUNCTIONS)
    reason_ranked = [f for f, _ in counts.most_common()]

    if functions and all(f in functions and isinstance(functions[f], dict) and "index" in functions[f] for f in FUNCTIONS):
        ranked = sorted(FUNCTIONS, key=lambda f: (-functions[f]["index"], f))
    elif reason_ranked:
        ranked = reason_ranked + [f for f in FUNCTIONS if f not in reason_ranked]
    else:
        ranked = list(FUNCTIONS)
    first, second = ranked[:2]

    parts = [
        "Kesimpulan utama:",
        f"secara keseluruhan, pola terkuatmu berada pada {first} ({FUNCTIONS[first]['title']}) dan {second} ({FUNCTIONS[second]['title']}).",
        f"Ini menggambarkan kecenderungan untuk {FUNCTIONS[first]['meaning']}, sambil juga {FUNCTIONS[second]['meaning']}.",
    ]

    top_reason = reason_ranked[0] if reason_ranked else None
    if top_reason:
        parts.append(
            f"Dari alasan yang kamu tulis, fungsi yang paling sering muncul adalah {top_reason} ({FUNCTIONS[top_reason]['name']}), sehingga cara kamu menjelaskan keputusan paling sering bergerak di sekitar pola {FUNCTIONS[top_reason]['meaning']}."
        )
        if len(reason_ranked) > 1:
            second_reason = reason_ranked[1]
            parts.append(f"Pola pendamping yang juga terlihat adalah {second_reason}, yaitu {FUNCTIONS[second_reason]['meaning']}.")

    if decision.get("type"):
        parts.append(f"Dalam kerangka MBTI berbasis fungsi yang dipakai tes ini, susunan keseluruhanmu paling dekat dengan {decision['type']} ({'–'.join(decision.get('stack', []))}).")

    if top_reason and top_reason in {first, second}:
        parts.append("Pilihan jawaban dan cara kamu menjelaskan alasan saling menguatkan pada pola utama yang sama, sehingga gambaran keseluruhannya terlihat cukup konsisten.")
    elif top_reason:
        parts.append(f"Pilihan jawaban menonjolkan {first} dan {second}, sedangkan alasan tertulismu lebih sering menonjolkan {top_reason}. Ini menunjukkan bahwa pilihan akhir dan cara kamu menjelaskan keputusan memperlihatkan sisi kepribadian yang berbeda namun tetap dapat berjalan bersamaan.")
    else:
        parts.append("Karena tidak ada alasan tertulis, gambaran keseluruhan terutama berasal dari pola pilihan jawaban dan susunan fungsi yang dihasilkan tes.")
    return " ".join(parts)


def build_reflection(answers, predictions, functions, decision, name="", age=None, gender=""):
    insights = [question_insight(a, predictions.get(a.id, {})) for a in sorted(answers, key=lambda a: a.id)]
    meaningful = [i for i in insights if i["reason"]]
    opening = profile_opening(name, age, gender, len(meaningful))
    paragraphs = [opening]

    if decision["type"]:
        stack = "–".join(decision["stack"])
        paragraphs.append(f"Dari pola delapan fungsi pada tes ini, kandidat utamamu adalah {decision['type']} dengan susunan {stack}. Tipe ini diperoleh setelah skor seluruh fungsi dihitung, bukan dari penjumlahan pasangan huruf.")
    else:
        candidates = decision.get("candidates") or []
        if candidates:
            top_candidate = candidates[0]
            paragraphs.append(f"Pola fungsi terdekatmu saat ini adalah {top_candidate['type']} dengan susunan {'–'.join(top_candidate['stack'])}. Sistem tetap menampilkan kandidat terdekat berdasarkan skor delapan fungsi meskipun profil keseluruhannya sangat berimbang.")
        else:
            paragraphs.append("Pola fungsi utama dibaca langsung dari delapan skor fungsi kognitif yang tersedia.")

    if decision.get("status") == "tentative" and decision.get("type"):
        paragraphs.append(f"Kandidat utama tetap {decision['type']}; kandidat lain berada cukup dekat pada skor kecocokan, tetapi hasil yang digunakan sebagai acuan utama tetap tipe tersebut.")

    reason_paragraph_indices = {}
    for insight in meaningful:
        reason_paragraph_indices[insight["question_id"]] = len(paragraphs)
        paragraphs.append(" ".join(insight["paragraphs"]))

    if not meaningful:
        paragraphs.append("Karena tidak ada alasan tertulis, pembahasan personal terutama memakai pola pilihan jawaban dan skor delapan fungsi kognitif.")

    grouped = {}
    for insight in meaningful:
        if insight["text_function"]:
            grouped.setdefault(insight["text_function"], []).append(insight["question_id"])
    repeat = [(f, ids) for f, ids in grouped.items() if len(ids) > 1]
    for f, ids in sorted(repeat, key=lambda item: (-len(item[1]), item[0])):
        paragraphs.append(f"Fungsi {f} muncul berulang pada alasan soal {', '.join(map(str, ids))}. Pengulangan ini menunjukkan bahwa pola {FUNCTIONS[f]['meaning']} cukup sering muncul dalam cara kamu menjelaskan pilihan.")

    neutral_count = sum(a.choice == "neutral" for a in answers)
    if neutral_count:
        paragraphs.append(f"Ada {neutral_count} pilihan netral. Pilihan tersebut tetap menyimpan dua sisi kontribusi, sementara alasan tertulis tetap diklasifikasikan ke fungsi kognitif yang paling dekat.")

    paragraphs.append("Model teks ini belajar dari contoh sintetis dan belum divalidasi pada responden nyata. Karena setiap alasan nonkosong dipaksa ke fungsi best-match, alasan yang sangat pendek atau kurang relevan dapat menghasilkan klasifikasi yang kurang tepat. Semakin jelas dan konkret alasan yang ditulis, semakin berguna interpretasinya.")
    overall_conclusion_index = len(paragraphs)
    paragraphs.append(_overall_conclusion(meaningful, functions, decision))

    return {"paragraphs": paragraphs, "question_insights": insights,
            "reason_paragraph_indices": reason_paragraph_indices,
            "overall_conclusion_index": overall_conclusion_index,
            "discussed_reason_count": len(meaningful), "generated_reason_count": 0,
            "mode": "evidence_local", "local_llm_status": "not_requested"}
