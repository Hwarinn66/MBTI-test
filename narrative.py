"""Evidence-grounded Indonesian reflection; no network calls, no invented quotes."""
import re
from collections import Counter
from cognitive import FUNCTIONS
from questions import CHOICES, QUESTION_BY_ID

LABELS = {c["value"]: c["label"] for c in CHOICES}

# Deterministic language profiles used when Qwen is disabled. They make the
# local fallback read like an explanation rather than a classifier dump while
# still staying tied to the function that the text model selected.
FUNCTION_STYLE = {
    "Te": {
        "focus": "kamu cenderung mencari cara yang paling efektif untuk membawa sesuatu menuju hasil yang jelas",
        "daily": "Dalam keseharian, pola ini biasanya terlihat saat seseorang membuat urutan kerja, menetapkan prioritas, membagi tugas, atau mencari ukuran yang membuat kemajuan lebih mudah dipantau",
        "strength": "Sisi kuatnya adalah kemampuan mengubah tujuan yang masih abstrak menjadi langkah yang bisa langsung dikerjakan",
        "watch": "Jika terlalu dominan, perhatian pada efisiensi dapat membuat proses, perasaan, atau pertimbangan yang tidak mudah diukur menjadi kurang mendapat ruang",
    },
    "Ti": {
        "focus": "kamu cenderung ingin memahami apakah sebuah penjelasan benar-benar masuk akal menurut kerangka logika yang konsisten",
        "daily": "Dalam keseharian, pola ini sering muncul saat seseorang membongkar cara kerja sesuatu, membandingkan definisi, mencari celah dalam argumen, atau ingin memahami prinsip sebelum menerima kesimpulan",
        "strength": "Sisi kuatnya adalah ketelitian dalam membedakan hal yang sekadar terdengar masuk akal dengan hal yang benar-benar konsisten secara logis",
        "watch": "Jika terlalu dominan, kebutuhan untuk memahami semuanya secara rapi dapat membuat keputusan tertunda ketika informasi yang tersedia belum terasa lengkap",
    },
    "Fe": {
        "focus": "kamu cenderung memperhatikan bagaimana keputusan, ucapan, dan tindakanmu memengaruhi suasana serta orang-orang di sekitarmu",
        "daily": "Dalam keseharian, pola ini biasanya terlihat ketika seseorang menyesuaikan cara berbicara, membaca kebutuhan kelompok, menjaga kesepahaman, atau mempertimbangkan dampak sosial sebelum bertindak",
        "strength": "Sisi kuatnya adalah kemampuan menangkap dinamika hubungan dan menciptakan interaksi yang terasa lebih terhubung bagi banyak orang",
        "watch": "Jika terlalu dominan, menjaga kenyamanan bersama dapat membuat kebutuhan atau pendirian pribadi lebih sering ditempatkan di belakang kepentingan hubungan",
    },
    "Fi": {
        "focus": "kamu cenderung menilai keputusan berdasarkan apakah pilihan itu terasa selaras dengan nilai, prinsip, dan nurani pribadimu",
        "daily": "Dalam keseharian, pola ini sering terlihat ketika seseorang mempertahankan sesuatu yang dianggap benar secara pribadi, sangat memperhatikan keaslian sikap, atau sulit nyaman dengan pilihan yang bertentangan dengan nilai dirinya",
        "strength": "Sisi kuatnya adalah keteguhan menjaga identitas dan konsistensi antara apa yang diyakini dengan apa yang dilakukan",
        "watch": "Jika terlalu dominan, keyakinan pribadi yang sangat kuat dapat membuat sudut pandang lain terasa lebih sulit diterima ketika bertabrakan dengan nilai yang sudah dianggap penting",
    },
    "Ne": {
        "focus": "kamu cenderung membuka banyak kemungkinan dan menghubungkan satu gagasan dengan gagasan lain yang pada awalnya tampak terpisah",
        "daily": "Dalam keseharian, pola ini sering terlihat saat seseorang cepat menemukan alternatif, memunculkan ide baru dari hal sederhana, melihat beberapa kemungkinan sekaligus, atau tertarik mencoba pendekatan yang berbeda",
        "strength": "Sisi kuatnya adalah keluwesan melihat jalan lain ketika satu cara terasa buntu dan kemampuan menemukan hubungan yang tidak langsung terlihat",
        "watch": "Jika terlalu dominan, banyaknya kemungkinan dapat membuat fokus berpindah terlalu cepat sebelum satu pilihan benar-benar selesai dikembangkan",
    },
    "Ni": {
        "focus": "kamu cenderung mencari benang merah di balik informasi yang tersebar lalu membentuk gambaran tentang arah yang paling masuk akal",
        "daily": "Dalam keseharian, pola ini biasanya terlihat ketika seseorang menangkap pola jangka panjang, memikirkan konsekuensi ke depan, menyederhanakan banyak petunjuk menjadi satu arah, atau merasa ada tema besar yang menghubungkan beberapa kejadian",
        "strength": "Sisi kuatnya adalah kemampuan menjaga pandangan jangka panjang dan memahami arah umum tanpa harus terpaku pada setiap detail yang muncul",
        "watch": "Jika terlalu dominan, keyakinan pada satu gambaran besar dapat membuat kemungkinan alternatif atau informasi baru yang tidak sesuai pola awal menjadi lebih mudah terlewat",
    },
    "Se": {
        "focus": "kamu cenderung membaca keadaan yang sedang terjadi dan merespons berdasarkan informasi konkret yang tersedia pada saat itu",
        "daily": "Dalam keseharian, pola ini sering terlihat ketika seseorang cepat menangkap perubahan di lingkungan, belajar lewat pengalaman langsung, menikmati keterlibatan nyata, atau memilih bertindak lalu menyesuaikan diri dari hasil yang didapat",
        "strength": "Sisi kuatnya adalah kemampuan hadir pada situasi nyata dan bergerak cepat tanpa harus menunggu semua kemungkinan dianalisis terlebih dahulu",
        "watch": "Jika terlalu dominan, dorongan untuk merespons apa yang ada sekarang dapat membuat konsekuensi jangka panjang atau pola yang belum langsung terlihat menjadi kurang diperhatikan",
    },
    "Si": {
        "focus": "kamu cenderung memahami keadaan sekarang dengan membandingkannya pada pengalaman, detail, dan pola yang pernah kamu simpan sebelumnya",
        "daily": "Dalam keseharian, pola ini sering terlihat ketika seseorang mengingat detail yang pernah terjadi, menyukai cara yang sudah terbukti, memperhatikan kestabilan rutinitas, atau menggunakan pengalaman terdahulu sebagai acuan untuk menilai situasi baru",
        "strength": "Sisi kuatnya adalah konsistensi, perhatian pada detail yang pernah terbukti penting, dan kemampuan belajar dari pengalaman yang sudah dilalui",
        "watch": "Jika terlalu dominan, ketergantungan pada pola yang familiar dapat membuat perubahan mendadak atau pendekatan yang sama sekali baru terasa lebih sulit diterima",
    },
}


def _reason_depth(reason):
    words = re.findall(r"(?u)\b\w+\b", reason)
    if len(words) >= 35:
        return "panjang"
    if len(words) >= 14:
        return "sedang"
    return "singkat"


def _function_explanation(pf, stance, reason, question_id):
    info = FUNCTIONS[pf]
    style = FUNCTION_STYLE[pf]
    depth = _reason_depth(reason)

    if stance == "oppose":
        opening = (
            f"Fungsi kognitif paling dekat dari alasan ini adalah {pf} ({info['name']}) — {info['title']}. "
            f"Alasanmu tetap berkaitan paling kuat dengan tema {pf}, tetapi kamu menggambarkan dirimu dengan cara yang berlawanan terhadap kecenderungan utamanya."
        )
    elif stance == "mixed":
        opening = (
            f"Fungsi kognitif paling dekat dari alasan ini adalah {pf} ({info['name']}) — {info['title']}. "
            f"Cara kamu menjelaskannya menunjukkan bahwa pola {pf} muncul secara situasional: ada keadaan ketika kamu menggunakannya dengan jelas, dan ada keadaan ketika kamu mengambil pendekatan lain."
        )
    else:
        opening = (
            f"Fungsi kognitif paling dekat dari alasan ini adalah {pf} ({info['name']}) — {info['title']}. "
            f"Dari cara kamu menjelaskan keputusanmu, {style['focus']}."
        )

    # Rotate a few human-sounding transitions so many written reasons do not read
    # like the exact same template repeated 20 times.
    variant = question_id % 3
    if variant == 0:
        middle = f"{style['daily']}. {style['strength']}."
    elif variant == 1:
        middle = f"Yang membuat pola ini terlihat adalah arah pertimbanganmu, bukan sekadar pilihan akhirnya. {style['daily']}."
    else:
        middle = f"Pola ini memberi gambaran tentang proses yang terjadi sebelum kamu mengambil keputusan. {style['strength']}."

    if depth == "panjang":
        detail = (
            "Karena alasanmu cukup rinci, konteks yang kamu berikan membuat penilaian ini tidak hanya bergantung pada satu kata kunci; "
            "cara kamu menjelaskan sebab, prioritas, dan konsekuensi ikut membentuk pembacaan fungsi tersebut."
        )
    elif depth == "sedang":
        detail = (
            "Alasanmu sudah memberi konteks yang cukup untuk melihat arah pertimbangan yang kamu gunakan, sehingga fungsi ini dibaca dari cara kamu menjelaskan pilihan, bukan dari jawabannya saja."
        )
    else:
        detail = (
            "Alasanmu cukup singkat, jadi sistem mengambil pola yang paling dekat dari informasi yang tersedia. Penjelasan yang lebih konkret biasanya membuat gambaran fungsi menjadi lebih kaya."
        )

    closing = f"{style['watch']}."
    return f"{opening} {middle} {detail} {closing}"


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
            paragraphs.append(
                "Pilihan netral tetap dihitung sebagai dua sisi yang tersimpan terpisah: dukungan dan penolakan. "
                "Karena kamu tidak menuliskan alasan, bagian ini hanya menunjukkan kecenderungan dari pilihan jawaban tanpa menebak motivasi di baliknya."
            )
        else:
            action = "mendukung" if effective > 0 else "kurang mendukung"
            info = FUNCTIONS[f]
            paragraphs.append(
                f"Dengan arah pernyataan soal ini, pilihanmu {action} pola {f} ({info['name']}). "
                f"Fungsi ini berhubungan dengan kecenderungan untuk {info['meaning']}. Karena tidak ada alasan tertulis, sistem tidak menambahkan interpretasi tentang penyebab pilihanmu."
            )
    else:
        paragraphs = [f"Di soal {q['id']}, kamu memilih {LABELS[answer.choice].lower()}, lalu menulis: “{reason}”"]
        qualified = bool(re.search(r"\b(tapi|tetapi|namun|tergantung|kadang|kalau|kecuali)\b", reason, re.I))

        if prediction.get("accepted") and prediction.get("function") in FUNCTIONS:
            pf, stance = prediction["function"], prediction["stance"]
            paragraphs.append(_function_explanation(pf, stance, reason, q["id"]))

            relationship = "qualified" if neutral or qualified or stance == "mixed" else "other_function" if pf != f else "aligned"
            if pf == f and not neutral and stance != "mixed":
                agrees = (effective > 0) == (stance == "support")
                if not agrees:
                    relationship = "contradictory"
                    paragraphs.append(
                        "Ada perbedaan antara arah pilihanmu dan cara kamu menjelaskan alasan. Ini bukan kesalahan: pilihan jawaban menggambarkan posisi akhirnya, sedangkan alasan menunjukkan proses pertimbangan yang membawamu ke sana. "
                        "Karena itu keduanya tetap disimpan sebagai informasi yang berbeda."
                    )
            if pf != f:
                qinfo = FUNCTIONS[f]
                pinfo = FUNCTIONS[pf]
                paragraphs.append(
                    f"Soal ini awalnya dirancang untuk memeriksa {f} ({qinfo['title']}), tetapi alasan yang kamu tulis lebih dekat dengan {pf} ({pinfo['title']}). "
                    "Ini menunjukkan bahwa alasanmu membawa konteks tambahan yang tidak sepenuhnya sama dengan fungsi yang diuji oleh pertanyaannya."
                )
        else:
            relationship = "unclear"
            info = FUNCTIONS[f]
            paragraphs.append(
                f"Model teks tidak dapat menggunakan hasil klasifikasi alasan ini, sehingga pembahasan sementara mengikuti fungsi utama soal, yaitu {f} ({info['name']}). "
                f"Dalam kerangka tes ini, fungsi tersebut berkaitan dengan kecenderungan untuk {info['meaning']}."
            )

        if neutral:
            paragraphs.append(
                "Pilihan netralmu menunjukkan bahwa posisi akhirnya tidak mutlak ke satu sisi. Namun alasan tertulis tetap memberi informasi tentang cara kamu memproses situasi, sehingga fungsi dari teks tetap dipakai untuk memperkaya gambaran keseluruhan."
            )

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
    parts = [f"{greeting} aku asisten AI lokal yang akan menemanimu membaca pola dari hasil tes ini."]
    if gender and age is not None:
        parts.append(f"Kamu memperkenalkan diri sebagai {gender.lower()} berusia {age} tahun.")
    elif age is not None:
        parts.append(f"Kamu menyebut usiamu {age} tahun.")
    elif gender:
        parts.append(f"Kamu memperkenalkan diri sebagai {gender.lower()}.")
    if reason_count:
        parts.append(
            f"Kamu menuliskan alasan pada {reason_count} soal. Itu membuat hasil ini bisa dibaca lebih dalam daripada sekadar melihat pilihan setuju atau tidak setuju, karena setiap alasan juga dipetakan ke fungsi kognitif yang paling dekat."
        )
    else:
        parts.append("Kamu belum menuliskan alasan, jadi gambaran utama di bawah akan dibangun dari pola pilihan jawaban dan susunan delapan fungsi kognitif.")
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

    first_style = FUNCTION_STYLE[first]
    second_style = FUNCTION_STYLE[second]
    parts = [
        "Kesimpulan utama:",
        f"secara keseluruhan, dua pola yang paling menonjol dalam hasilmu adalah {first} ({FUNCTIONS[first]['name']}) dan {second} ({FUNCTIONS[second]['name']}).",
        f"Ini berarti dalam banyak situasi {first_style['focus']}, sementara {second} menambahkan kecenderungan bahwa {second_style['focus']}.",
        f"Kombinasi keduanya membuat cara berpikirmu tidak hanya terlihat dari apa yang kamu pilih, tetapi juga dari bagaimana kamu menyusun alasan sebelum sampai pada pilihan tersebut.",
    ]

    top_reason = reason_ranked[0] if reason_ranked else None
    if top_reason:
        top_style = FUNCTION_STYLE[top_reason]
        parts.append(
            f"Dari alasan yang kamu tulis, fungsi yang paling sering muncul adalah {top_reason}. Artinya, saat kamu diberi ruang untuk menjelaskan dengan kata-katamu sendiri, pola yang paling sering muncul adalah bahwa {top_style['focus']}."
        )
        if len(reason_ranked) > 1:
            second_reason = reason_ranked[1]
            parts.append(
                f"Fungsi {second_reason} juga muncul sebagai pola pendamping. Ini menambah sisi bahwa {FUNCTION_STYLE[second_reason]['focus']}."
            )

    if decision.get("type"):
        stack = "–".join(decision.get("stack", []))
        parts.append(
            f"Ketika seluruh skor fungsi disusun menjadi pola MBTI, profilmu paling dekat dengan {decision['type']} dengan susunan {stack}. "
            "Empat huruf itu dipakai sebagai ringkasan dari susunan fungsi, bukan sebagai sumber penilaian utama."
        )

    if top_reason and top_reason in {first, second}:
        parts.append(
            "Pilihan jawaban dan cara kamu menjelaskan alasan saling menguatkan pada pola yang sama. Karena itu, gambaran keseluruhannya terlihat cukup konsisten antara keputusan yang kamu ambil dan proses berpikir yang kamu ceritakan."
        )
    elif top_reason:
        parts.append(
            f"Pilihan jawaban lebih menonjolkan {first} dan {second}, sedangkan cara kamu menjelaskan keputusan lebih sering menonjolkan {top_reason}. "
            "Perbedaan ini menunjukkan bahwa hasil akhir dan proses berpikirmu dapat menampilkan sisi yang berbeda: kamu bisa mengambil keputusan dengan satu kecenderungan, tetapi menjelaskannya melalui pola kognitif lain."
        )
    else:
        parts.append(
            "Karena tidak ada alasan tertulis, kesimpulan ini terutama menggambarkan pola pilihan jawaban. Menambahkan alasan pada beberapa soal biasanya membuat gambaran tentang proses berpikir menjadi jauh lebih personal."
        )

    parts.append(
        f"Secara sederhana, hasil ini menggambarkan seseorang yang {first_style['focus']}, tetapi pada saat yang sama juga membawa sisi {second_style['focus']}. "
        "Kekuatan utamanya terletak pada cara dua kecenderungan itu saling melengkapi, sementara tantangannya biasanya muncul ketika salah satunya mengambil terlalu banyak ruang dibanding yang lain."
    )
    return " ".join(parts)


def build_reflection(answers, predictions, functions, decision, name="", age=None, gender=""):
    insights = [question_insight(a, predictions.get(a.id, {})) for a in sorted(answers, key=lambda a: a.id)]
    meaningful = [i for i in insights if i["reason"]]
    opening = profile_opening(name, age, gender, len(meaningful))
    paragraphs = [opening]

    if decision["type"]:
        stack = "–".join(decision["stack"])
        dominant = decision["stack"][0]
        auxiliary = decision["stack"][1] if len(decision["stack"]) > 1 else None
        intro = (
            f"Dari pola delapan fungsi pada tes ini, kandidat utamamu adalah {decision['type']} dengan susunan {stack}. "
            f"Fungsi teratasnya adalah {dominant} ({FUNCTIONS[dominant]['name']}), yang berkaitan dengan kecenderungan untuk {FUNCTIONS[dominant]['meaning']}."
        )
        if auxiliary:
            intro += (
                f" Fungsi pendampingnya, {auxiliary} ({FUNCTIONS[auxiliary]['name']}), menambahkan kecenderungan untuk {FUNCTIONS[auxiliary]['meaning']}."
            )
        intro += " Tipe ini diperoleh setelah skor seluruh fungsi dihitung, bukan dari penjumlahan pasangan huruf."
        paragraphs.append(intro)
    else:
        candidates = decision.get("candidates") or []
        if candidates:
            top_candidate = candidates[0]
            paragraphs.append(
                f"Pola fungsi terdekatmu saat ini adalah {top_candidate['type']} dengan susunan {'–'.join(top_candidate['stack'])}. "
                "Profilmu cukup berimbang, tetapi kandidat ini tetap menjadi susunan yang paling dekat ketika delapan fungsi dibandingkan secara keseluruhan."
            )
        else:
            paragraphs.append("Pola fungsi utama dibaca langsung dari delapan skor fungsi kognitif yang tersedia.")

    if decision.get("status") == "tentative" and decision.get("type"):
        paragraphs.append(
            f"Kandidat utama tetap {decision['type']}. Beberapa kandidat lain memiliki pola yang cukup dekat, jadi perbedaannya terutama berada pada urutan dan kekuatan fungsi, bukan berarti hasil utamamu tidak dapat digunakan."
        )

    reason_paragraph_indices = {}
    for insight in meaningful:
        reason_paragraph_indices[insight["question_id"]] = len(paragraphs)
        paragraphs.append(" ".join(insight["paragraphs"]))

    if not meaningful:
        paragraphs.append(
            "Karena tidak ada alasan tertulis, pembahasan personal terutama memakai pola pilihan jawaban dan skor delapan fungsi. Hasilnya tetap dapat menunjukkan susunan umum, tetapi belum bisa menjelaskan proses berpikir di balik setiap pilihan."
        )

    grouped = {}
    for insight in meaningful:
        if insight["text_function"]:
            grouped.setdefault(insight["text_function"], []).append(insight["question_id"])
    repeat = [(f, ids) for f, ids in grouped.items() if len(ids) > 1]
    for f, ids in sorted(repeat, key=lambda item: (-len(item[1]), item[0])):
        style = FUNCTION_STYLE[f]
        paragraphs.append(
            f"Ada pola yang berulang pada alasan soal {', '.join(map(str, ids))}: semuanya paling dekat dengan {f} ({FUNCTIONS[f]['name']}). "
            f"Pengulangan ini penting karena menunjukkan bahwa {style['focus']} bukan hanya muncul pada satu jawaban, tetapi beberapa kali dalam cara kamu menjelaskan keputusan. {style['strength']}."
        )

    neutral_count = sum(a.choice == "neutral" for a in answers)
    if neutral_count:
        paragraphs.append(
            f"Ada {neutral_count} pilihan netral dalam jawabanmu. Di sistem ini, netral tidak berarti tidak punya pendirian; ia dibaca sebagai keadaan ketika dukungan dan penolakan sama-sama punya tempat. "
            "Alasan tertulismu tetap digunakan untuk melihat fungsi kognitif apa yang paling dekat dengan konteks di balik pilihan netral tersebut."
        )

    paragraphs.append(
        "Model teks ini belajar dari contoh sintetis dan belum divalidasi pada responden nyata. Setiap alasan nonkosong dipetakan ke fungsi best-match, jadi kualitas penjelasan sangat dipengaruhi oleh seberapa konkret alasan yang ditulis. "
        "Alasan yang menjelaskan situasi, pertimbangan, dan penyebab biasanya memberi gambaran yang lebih berguna daripada jawaban yang hanya terdiri dari beberapa kata."
    )
    overall_conclusion_index = len(paragraphs)
    paragraphs.append(_overall_conclusion(meaningful, functions, decision))

    return {"paragraphs": paragraphs, "question_insights": insights,
            "reason_paragraph_indices": reason_paragraph_indices,
            "overall_conclusion_index": overall_conclusion_index,
            "discussed_reason_count": len(meaningful), "generated_reason_count": 0,
            "mode": "evidence_local", "local_llm_status": "not_requested"}
