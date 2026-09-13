"""Evidence-grounded Indonesian reflection; no network calls, no invented quotes."""
import re
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
            paragraphs.append("Pilihan ini tetap dihitung: +1 sebagai dukungan dan −1 sebagai penolakan disimpan terpisah. Aku membacanya sebagai kadang iya, kadang tidak, bukan jawaban yang diabaikan.")
        else:
            action = "mendukung" if effective > 0 else "kurang mendukung"
            paragraphs.append(f"Dengan arah pernyataan soal ini, pilihanmu {action} pola {f}. Karena belum ada alasan tertulis, aku tidak akan menebak situasi atau motivasimu.")
    else:
        paragraphs = [f"Di soal {q['id']}, kamu memilih {LABELS[answer.choice].lower()}, lalu menulis: “{reason}”"]
        qualified = bool(re.search(r"\b(tapi|tetapi|namun|tergantung|kadang|kalau|kecuali)\b", reason, re.I))
        if prediction.get("accepted"):
            pf, stance = prediction["function"], prediction["stance"]
            meaning = FUNCTIONS[pf]["meaning"]
            if stance == "support":
                paragraphs.append(f"Yang menarik di sini adalah cara kamu menjelaskan pertimbanganmu. Pola bahasanya mendekati {pf}: {meaning}. Ini petunjuk dari tulisanmu, belum kesimpulan tentang dirimu secara utuh.")
            elif stance == "oppose":
                paragraphs.append(f"Model membaca alasan ini sebagai kurang mendukung pola {pf}, yaitu {meaning}. Tidak memilih cara itu dalam satu keadaan bukan berarti kamu tidak pernah menggunakannya.")
            else:
                paragraphs.append(f"Alasanmu memberi ruang bagi penggunaan {pf} yang bergantung situasi, yaitu {meaning}. Jadi aku tidak membacanya sebagai iya atau tidak yang mutlak.")
            relationship = "qualified" if neutral or qualified or stance == "mixed" else "other_function" if pf != f else "aligned"
            if pf == f and not neutral and stance != "mixed":
                agrees = (effective > 0) == (stance == "support")
                if not agrees:
                    relationship = "contradictory"
                    paragraphs.append("Ada perbedaan antara arah pilihanmu dan pola yang terbaca dari alasanmu. Keduanya tetap dicatat; model tidak otomatis menganggap pilihanmu salah. Bisa jadi konteks soal dan situasi yang kamu bayangkan berbeda.")
            if pf != f:
                paragraphs.append(f"Soal ini terutama memeriksa {f}, sedangkan alasanmu memberi petunjuk tentang {pf}. Ini tambahan konteks, bukan otomatis pertentangan.")
        else:
            relationship = "qualified" if qualified else "unclear"
            # A factual, narrow observation; quiet social behavior is NOT Si.
            if re.search(r"berkumpul|keramaian", reason, re.I) and re.search(r"jarang (?:berbicara|bicara)|diam|tidak banyak (?:bicara|berbicara)", reason, re.I):
                paragraphs.append("Kamu membedakan menikmati kebersamaan dengan seberapa banyak kamu berbicara. Keduanya memang tidak harus sama. Kalimat ini saja belum cukup untuk menyebut Si, Fe, atau fungsi tertentu; aku perlu tahu apa yang kamu perhatikan dan pertimbangkan saat berkumpul.")
            elif qualified:
                paragraphs.append("Ada konteks atau pengecualian dalam alasanmu. Aku tidak ingin mengubahnya menjadi label yang terlalu tegas: model belum menemukan petunjuk fungsi yang cukup jelas pada kalimat ini.")
            else:
                paragraphs.append("Terima kasih sudah memberi konteks. Dari kalimat ini, model belum cukup yakin mengenali pola fungsi tertentu. Jadi alasannya tetap ditampilkan, tetapi tidak ditambahkan sebagai bukti fungsi kognitif.")
        if neutral:
            paragraphs.append("Jawaban netralmu tetap membawa +1 dukungan dan −1 penolakan secara terpisah. Alasanmu membantu menjelaskan kapan masing-masing sisi muncul.")
    return {"question_id": q["id"], "question": q["text"], "choice": answer.choice,
            "choice_label": LABELS[answer.choice], "question_function": f,
            "reason": reason, "relationship": relationship,
            "text_function": prediction.get("function") if prediction.get("accepted") else None,
            "text_stance": prediction.get("stance", "unknown"),
            "text_recognized": bool(prediction.get("accepted")),
            "paragraphs": paragraphs, "evidence": [reason] if reason else []}


def build_reflection(answers, predictions, functions, decision, name=""):
    insights = [question_insight(a, predictions.get(a.id, {})) for a in sorted(answers, key=lambda a: a.id)]
    opening = f"Halo {name.strip()}, terima kasih sudah bercerita." if name.strip() else "Terima kasih sudah meluangkan waktu untuk melihat kembali cara kamu berpikir."
    paragraphs = [opening]
    if decision["type"]:
        stack = "–".join(decision["stack"])
        paragraphs.append(f"Dari pola delapan fungsi pada tes ini, kandidat terdekatmu adalah {decision['type']} dengan susunan {stack}. Tipe ini diperoleh setelah skor fungsi dihitung, bukan dari penjumlahan pasangan huruf. Anggap ini titik awal refleksi, bukan label yang harus selalu cocok denganmu.")
    else:
        paragraphs.append("Aku belum bisa memilih satu susunan fungsi yang cukup berbeda dari kandidat lainnya. Jawaban yang seimbang atau bergantung situasi tetap bermakna; kamu tidak perlu mengubahnya hanya agar memperoleh empat huruf.")
    if decision["status"] == "tentative":
        paragraphs.append("Pola ini belum cukup tegas. Perhatikan juga kandidat pembanding di bawah, terutama bagian alasan yang memberi pengecualian. Skor kecocokan bukan peluang bahwa tipemu pasti benar.")
    meaningful = [i for i in insights if i["reason"]]
    # One discussion per written reason, in question order. Keep the locations so
    # the optional LLM can replace individual discussions without losing context.
    reason_paragraph_indices = {}
    for insight in meaningful:
        reason_paragraph_indices[insight["question_id"]] = len(paragraphs)
        paragraphs.append(" ".join(insight["paragraphs"]))
    if not meaningful:
        paragraphs.append("Kali ini kamu belum menuliskan alasan. Aku bisa menunjukkan pola pilihanmu, tetapi belum bisa menjelaskan motivasi di baliknya. Kalau ingin refleksi lebih personal, ceritakan satu kejadian nyata pada beberapa soal yang paling terasa dekat.")
    grouped = {}
    for insight in meaningful:
        if insight["text_function"] and insight["text_stance"] == "support":
            grouped.setdefault(insight["text_function"], []).append(insight["question_id"])
    repeat = [(f, ids) for f, ids in grouped.items() if len(ids) > 1]
    for f, ids in sorted(repeat, key=lambda item: (-len(item[1]), item[0])):
        paragraphs.append(f"Model menemukan petunjuk {f} pada alasan soal {', '.join(map(str, ids))}. Menarik untuk melihat apakah cara ini juga muncul di luar situasi tes. Pengulangan tulisan yang sama tetap dihitung satu kali, agar tidak membesar-besarkan bukti.")
    neutral_count = sum(a.choice == "neutral" for a in answers)
    if neutral_count:
        paragraphs.append(f"Ada {neutral_count} pilihan netral dalam jawabanmu. Semuanya menyimpan dua kontribusi, bukan nol. Untuk mengenal pola itu lebih jauh, coba pikirkan satu keadaan ketika kamu setuju dan satu keadaan ketika kamu tidak setuju.")
    paragraphs.append("Model teks ini belajar dari contoh sintetis, belum divalidasi pada responden nyata. Interpretasi fungsi adalah hipotesis dalam kerangka tipologi, bukan diagnosis atau pengukuran kemampuan kognitif. Ambil bagian yang membantu, dan pertanyakan bagian yang belum cocok dengan pengalamanmu.")
    return {"paragraphs": paragraphs, "question_insights": insights,
            "reason_paragraph_indices": reason_paragraph_indices,
            "discussed_reason_count": len(meaningful), "generated_reason_count": 0,
            "mode": "evidence_local", "local_llm_status": "not_requested"}
