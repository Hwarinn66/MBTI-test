"""Evidence-grounded Indonesian reflection; no network calls, no invented quotes."""
import hashlib
import re
from collections import Counter

from cognitive import FUNCTIONS
from questions import CHOICES, QUESTION_BY_ID

LABELS = {c["value"]: c["label"] for c in CHOICES}

# Deterministic language profiles for the non-Qwen path. The explanation is
# personalized from the user's actual choices/reasons, never from randomness.
FUNCTION_STYLE = {
    "Te": {
        "focus": "kamu cenderung mencari cara yang paling efektif untuk membawa sesuatu menuju hasil yang jelas",
        "daily": "pola ini biasanya terlihat saat kamu membuat urutan kerja, menetapkan prioritas, membagi tugas, atau mencari ukuran yang membuat kemajuan mudah dipantau",
        "strength": "kemampuan mengubah tujuan yang masih abstrak menjadi langkah yang bisa langsung dikerjakan",
        "watch": "perhatian pada efisiensi dapat membuat proses, perasaan, atau pertimbangan yang sulit diukur mendapat ruang lebih sedikit",
    },
    "Ti": {
        "focus": "kamu cenderung ingin memahami apakah sebuah penjelasan benar-benar masuk akal menurut kerangka logika yang konsisten",
        "daily": "pola ini sering muncul saat kamu membongkar cara kerja sesuatu, membandingkan definisi, mencari celah dalam argumen, atau memahami prinsip sebelum menerima kesimpulan",
        "strength": "ketelitian membedakan hal yang sekadar terdengar masuk akal dari hal yang benar-benar konsisten secara logis",
        "watch": "kebutuhan memahami semuanya secara rapi dapat membuat keputusan tertunda ketika informasi belum terasa lengkap",
    },
    "Fe": {
        "focus": "kamu cenderung memperhatikan bagaimana keputusan, ucapan, dan tindakanmu memengaruhi suasana serta orang-orang di sekitarmu",
        "daily": "pola ini biasanya terlihat saat kamu menyesuaikan cara berbicara, membaca kebutuhan kelompok, menjaga kesepahaman, atau mempertimbangkan dampak sosial sebelum bertindak",
        "strength": "kemampuan menangkap dinamika hubungan dan menciptakan interaksi yang terasa lebih terhubung",
        "watch": "menjaga kenyamanan bersama dapat membuat kebutuhan atau pendirian pribadi lebih sering ditempatkan di belakang kepentingan hubungan",
    },
    "Fi": {
        "focus": "kamu cenderung menilai keputusan berdasarkan apakah pilihan itu terasa selaras dengan nilai, prinsip, dan nurani pribadimu",
        "daily": "pola ini sering terlihat saat kamu mempertahankan sesuatu yang dianggap benar secara pribadi, memperhatikan keaslian sikap, atau merasa tidak nyaman dengan pilihan yang bertentangan dengan nilai diri",
        "strength": "keteguhan menjaga identitas dan konsistensi antara apa yang diyakini dengan apa yang dilakukan",
        "watch": "keyakinan pribadi yang sangat kuat dapat membuat sudut pandang lain lebih sulit diterima ketika bertabrakan dengan nilai yang sudah dianggap penting",
    },
    "Ne": {
        "focus": "kamu cenderung membuka banyak kemungkinan dan menghubungkan satu gagasan dengan gagasan lain yang pada awalnya tampak terpisah",
        "daily": "pola ini sering terlihat saat kamu cepat menemukan alternatif, memunculkan ide baru dari hal sederhana, melihat beberapa kemungkinan sekaligus, atau tertarik mencoba pendekatan berbeda",
        "strength": "keluwesan melihat jalan lain ketika satu cara terasa buntu dan kemampuan menemukan hubungan yang tidak langsung terlihat",
        "watch": "banyaknya kemungkinan dapat membuat fokus berpindah terlalu cepat sebelum satu pilihan selesai dikembangkan",
    },
    "Ni": {
        "focus": "kamu cenderung mencari benang merah di balik informasi yang tersebar lalu membentuk gambaran tentang arah yang paling masuk akal",
        "daily": "pola ini biasanya terlihat saat kamu menangkap pola jangka panjang, memikirkan konsekuensi ke depan, menyederhanakan banyak petunjuk menjadi satu arah, atau melihat tema besar di balik beberapa kejadian",
        "strength": "kemampuan menjaga pandangan jangka panjang dan memahami arah umum tanpa terpaku pada setiap detail",
        "watch": "keyakinan pada satu gambaran besar dapat membuat kemungkinan alternatif atau informasi baru yang tidak sesuai pola awal lebih mudah terlewat",
    },
    "Se": {
        "focus": "kamu cenderung membaca keadaan yang sedang terjadi dan merespons berdasarkan informasi konkret yang tersedia saat itu",
        "daily": "pola ini sering terlihat saat kamu cepat menangkap perubahan di lingkungan, belajar lewat pengalaman langsung, menikmati keterlibatan nyata, atau bertindak lalu menyesuaikan diri dari hasilnya",
        "strength": "kemampuan hadir pada situasi nyata dan bergerak cepat tanpa menunggu semua kemungkinan dianalisis terlebih dahulu",
        "watch": "dorongan merespons apa yang ada sekarang dapat membuat konsekuensi jangka panjang atau pola yang belum langsung terlihat kurang diperhatikan",
    },
    "Si": {
        "focus": "kamu cenderung memahami keadaan sekarang dengan membandingkannya pada pengalaman, detail, dan pola yang pernah kamu simpan sebelumnya",
        "daily": "pola ini sering terlihat saat kamu mengingat detail yang pernah terjadi, menyukai cara yang sudah terbukti, memperhatikan kestabilan rutinitas, atau memakai pengalaman terdahulu sebagai acuan situasi baru",
        "strength": "konsistensi, perhatian pada detail yang pernah terbukti penting, dan kemampuan belajar dari pengalaman yang sudah dilalui",
        "watch": "ketergantungan pada pola yang familiar dapat membuat perubahan mendadak atau pendekatan yang sama sekali baru terasa lebih sulit diterima",
    },
}


def _stable_variant(*parts, modulo=4):
    """Stable wording choice derived from evidence, never runtime randomness."""
    raw = "|".join(str(part) for part in parts).encode("utf-8", errors="ignore")
    return int.from_bytes(hashlib.sha256(raw).digest()[:4], "big") % modulo


def _reason_depth(reason):
    words = re.findall(r"(?u)\b\w+\b", reason)
    if len(words) >= 35:
        return "panjang"
    if len(words) >= 14:
        return "sedang"
    return "singkat"


def _function_explanation(pf, stance, reason, question_id, choice):
    info = FUNCTIONS[pf]
    style = FUNCTION_STYLE[pf]
    depth = _reason_depth(reason)
    variant = _stable_variant(question_id, choice, pf, stance, reason, modulo=5)

    if stance == "oppose":
        opening = (
            f"Fungsi kognitif paling dekat dari alasan ini adalah {pf} ({info['name']}) — {info['title']}. "
            f"Tema alasanmu tetap paling dekat dengan {pf}, tetapi kamu menggambarkan sikap yang berlawanan terhadap kecenderungan utamanya."
        )
    elif stance == "mixed":
        opening = (
            f"Fungsi kognitif paling dekat dari alasan ini adalah {pf} ({info['name']}) — {info['title']}. "
            f"Pola {pf} terlihat situasional: kamu menggunakannya pada keadaan tertentu, tetapi tidak menjadikannya respons yang sama untuk semua situasi."
        )
    else:
        openings = (
            f"Fungsi kognitif paling dekat dari alasan ini adalah {pf} ({info['name']}) — {info['title']}. Dari cara kamu menjelaskannya, {style['focus']}.",
            f"Alasan ini paling kuat mengarah ke {pf} ({info['name']}). Yang terlihat bukan hanya pilihan akhirnya; arah pertimbanganmu menunjukkan bahwa {style['focus']}.",
            f"Pada alasan ini, pola yang paling dekat adalah {pf} ({info['name']}) — {info['title']}. Cara kamu menyusun alasan memperlihatkan bahwa {style['focus']}.",
            f"Jika alasan ini dibaca sebagai proses berpikir, fungsi yang paling dekat adalah {pf} ({info['name']}). Di sini terlihat bahwa {style['focus']}.",
            f"Dari delapan fungsi yang dibandingkan, alasan ini paling mendekati {pf} ({info['name']}). Inti pertimbangannya menunjukkan bahwa {style['focus']}.",
        )
        opening = openings[variant]

    middles = (
        f"Dalam keseharian, {style['daily']}. Sisi kuat yang biasanya muncul adalah {style['strength']}.",
        f"Pola ini membantu menjelaskan proses sebelum kamu sampai pada keputusan. Dalam praktiknya, {style['daily']}, dengan kekuatan utama pada {style['strength']}.",
        f"Yang khas dari pola ini adalah bukan hanya apa yang kamu pilih, tetapi cara kamu sampai ke pilihan itu. Dalam banyak situasi, {style['daily']}.",
        f"Dari sudut fungsi kognitif, pola ini memberi petunjuk tentang kebiasaan memproses informasi. Dalam keseharian, {style['daily']}.",
        f"Cara berpikir seperti ini biasanya memberi keuntungan berupa {style['strength']}. Pada aktivitas sehari-hari, {style['daily']}.",
    )
    middle = middles[variant]

    if depth == "panjang":
        details = (
            "Alasanmu cukup rinci, sehingga pembacaan ini tidak bergantung pada satu kata kunci; hubungan antara sebab, prioritas, dan konsekuensi ikut membentuk klasifikasinya.",
            "Karena kamu memberi konteks yang panjang, sistem bisa membaca bukan hanya topiknya, tetapi juga bagaimana kamu menimbang penyebab dan akibat di dalam alasan tersebut.",
        )
    elif depth == "sedang":
        details = (
            "Alasanmu sudah memberi konteks yang cukup untuk melihat arah pertimbangan yang digunakan, jadi fungsi ini dibaca dari cara kamu menjelaskan pilihan, bukan dari jawabannya saja.",
            "Panjang alasanmu cukup untuk menunjukkan pola pertimbangan, sehingga klasifikasi fungsi berasal dari hubungan antaride di dalam kalimat, bukan sekadar satu kata.",
        )
    else:
        details = (
            "Alasanmu cukup singkat, jadi sistem mengambil fungsi yang paling dekat dari informasi yang tersedia. Contoh yang lebih konkret biasanya membuat penjelasan semakin spesifik.",
            "Karena konteksnya singkat, penilaian memakai pola terdekat yang tersedia. Menambahkan situasi nyata, alasan, atau konsekuensi biasanya membuat pembacaan lebih tajam.",
        )
    detail = details[variant % 2]

    closings = (
        f"Sisi yang perlu dijaga adalah bahwa jika pola ini mengambil terlalu banyak ruang, {style['watch']}.",
        f"Dalam kadar yang seimbang pola ini berguna, tetapi jika menjadi terlalu dominan, {style['watch']}.",
        f"Titik rawannya muncul ketika kecenderungan ini digunakan terus-menerus tanpa fungsi lain sebagai penyeimbang; pada kondisi itu, {style['watch']}.",
        f"Pola ini bukan masalah dengan sendirinya. Tantangannya muncul saat intensitasnya terlalu tinggi, karena {style['watch']}.",
        f"Karena itu, kekuatan fungsi ini paling efektif ketika tetap diimbangi pola lain; tanpa keseimbangan tersebut, {style['watch']}.",
    )
    return f"{opening} {middle} {detail} {closings[variant]}"


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
                "Pilihan netral tetap dihitung sebagai dua sisi: dukungan dan penolakan. Karena kamu tidak menuliskan alasan, bagian ini hanya menunjukkan kecenderungan dari pilihan tanpa menebak motivasi di baliknya."
            )
        else:
            action = "mendukung" if effective > 0 else "kurang mendukung"
            info = FUNCTIONS[f]
            paragraphs.append(
                f"Dengan arah pernyataan soal ini, pilihanmu {action} pola {f} ({info['name']}). Fungsi ini berkaitan dengan kecenderungan untuk {info['meaning']}. Karena tidak ada alasan tertulis, sistem tidak menambahkan interpretasi tentang penyebab pilihanmu."
            )
    else:
        paragraphs = [f"Di soal {q['id']}, kamu memilih {LABELS[answer.choice].lower()}, lalu menulis: “{reason}”"]
        qualified = bool(re.search(r"\b(tapi|tetapi|namun|tergantung|kadang|kalau|kecuali)\b", reason, re.I))

        if prediction.get("accepted") and prediction.get("function") in FUNCTIONS:
            pf, stance = prediction["function"], prediction["stance"]
            paragraphs.append(_function_explanation(pf, stance, reason, q["id"], answer.choice))

            relationship = "qualified" if neutral or qualified or stance == "mixed" else "other_function" if pf != f else "aligned"
            if pf == f and not neutral and stance != "mixed":
                agrees = (effective > 0) == (stance == "support")
                if not agrees:
                    relationship = "contradictory"
                    paragraphs.append(
                        "Arah pilihan dan cara kamu menjelaskan alasan tidak sama. Pilihan jawaban menggambarkan posisi akhirnya, sedangkan alasan menunjukkan proses pertimbangan yang membawamu ke sana; keduanya tetap disimpan sebagai informasi berbeda."
                    )
            if pf != f:
                qinfo = FUNCTIONS[f]
                pinfo = FUNCTIONS[pf]
                paragraphs.append(
                    f"Soal ini dirancang terutama untuk memeriksa {f} ({qinfo['title']}), tetapi alasanmu lebih dekat dengan {pf} ({pinfo['title']}). Artinya, cara kamu menjelaskan keputusan membawa konteks kognitif yang berbeda dari fungsi utama pertanyaan."
                )
        else:
            relationship = "unclear"
            info = FUNCTIONS[f]
            paragraphs.append(
                f"Model teks tidak dapat menggunakan hasil klasifikasi alasan ini, sehingga pembahasan sementara mengikuti fungsi utama soal: {f} ({info['name']}), yang berkaitan dengan kecenderungan untuk {info['meaning']}."
            )

        if neutral:
            paragraphs.append(
                "Pilihan netral menunjukkan bahwa posisi akhirnya tidak mutlak ke satu sisi. Alasan tertulis tetap memberi informasi tentang proses yang kamu gunakan, sehingga fungsi dari teks tetap dipakai untuk memperkaya gambaran keseluruhan."
            )

    return {
        "question_id": q["id"], "question": q["text"], "choice": answer.choice,
        "choice_label": LABELS[answer.choice], "question_function": f,
        "reason": reason, "relationship": relationship,
        "text_function": prediction.get("function") if prediction.get("accepted") else None,
        "text_stance": prediction.get("stance", "unknown"),
        "text_recognized": bool(prediction.get("accepted")),
        "text_score": prediction.get("model_score", 0.0),
        "paragraphs": paragraphs, "evidence": [reason] if reason else [],
    }


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
            f"Kamu menuliskan alasan pada {reason_count} soal. Karena itu hasilmu tidak dibaca hanya dari pilihan setuju atau tidak setuju; setiap alasan juga dipetakan ke fungsi kognitif yang paling dekat."
        )
    else:
        parts.append("Kamu belum menuliskan alasan, jadi gambaran utama dibangun dari pola pilihan dan susunan delapan fungsi kognitif.")
    return " ".join(parts)


def _profile_metrics(answers, meaningful, functions):
    ranked = sorted(FUNCTIONS, key=lambda f: (-functions.get(f, {}).get("index", 50), f))
    scores = {f: float(functions.get(f, {}).get("index", 50)) for f in FUNCTIONS}
    counts = Counter(i["text_function"] for i in meaningful if i["text_function"] in FUNCTIONS)
    stances = Counter(i["text_stance"] for i in meaningful if i["text_function"] in FUNCTIONS)
    reason_words = [len(re.findall(r"(?u)\b\w+\b", i["reason"])) for i in meaningful]
    neutral_count = sum(a.choice == "neutral" for a in answers)
    strong_count = sum(type(a.choice) is int and abs(a.choice) == 3 for a in answers)
    contradiction_count = sum(i["relationship"] == "contradictory" for i in meaningful)
    qualified_count = sum(i["relationship"] == "qualified" for i in meaningful)
    return {
        "ranked": ranked,
        "scores": scores,
        "counts": counts,
        "stances": stances,
        "neutral_count": neutral_count,
        "strong_count": strong_count,
        "contradiction_count": contradiction_count,
        "qualified_count": qualified_count,
        "reason_count": len(meaningful),
        "average_reason_words": (sum(reason_words) / len(reason_words)) if reason_words else 0,
    }


def _personal_pattern(answers, meaningful, functions, decision):
    m = _profile_metrics(answers, meaningful, functions)
    ranked, scores = m["ranked"], m["scores"]
    first, second, third = ranked[:3]
    gap12 = scores[first] - scores[second]
    gap23 = scores[second] - scores[third]
    fingerprint = _stable_variant(
        decision.get("type"),
        ",".join(f"{f}:{scores[f]:.2f}" for f in ranked),
        ",".join(f"{i['question_id']}:{i['text_function']}:{i['text_stance']}:{i['reason']}" for i in meaningful),
        modulo=4,
    )

    if gap12 >= 12:
        balance = f"{first} terlihat jauh lebih dominan daripada fungsi lain, sehingga pola {FUNCTION_STYLE[first]['focus']} menjadi warna paling kuat pada hasilmu."
    elif gap12 <= 3 and gap23 <= 4:
        balance = f"{first}, {second}, dan {third} berada cukup berdekatan. Profilmu terlihat lebih berlapis karena tidak ada satu fungsi yang mengambil jarak sangat besar dari dua fungsi berikutnya."
    else:
        balance = f"{first} memimpin, tetapi {second} masih cukup dekat. Ini membuat pola utamamu terlihat sebagai kombinasi {FUNCTIONS[first]['title'].lower()} dan {FUNCTIONS[second]['title'].lower()}, bukan satu fungsi yang bekerja sendirian."

    if m["neutral_count"] >= 10:
        choice_style = f"Kamu memakai jawaban netral cukup sering ({m['neutral_count']} dari {len(answers)} soal), jadi banyak keputusanmu dalam tes tampak bergantung pada konteks daripada selalu berada di salah satu ujung skala."
    elif m["strong_count"] >= 16:
        choice_style = f"Kamu cukup sering memilih jawaban paling tegas ({m['strong_count']} soal pada tingkat ±3), sehingga profil pilihanmu memiliki banyak posisi yang jelas dan kuat."
    else:
        choice_style = "Pola pilihanmu berada di antara jawaban tegas dan jawaban moderat, sehingga profilnya tidak hanya dibentuk oleh respons ekstrem ataupun netral saja."

    if m["counts"]:
        reason_top = [f for f, _ in m["counts"].most_common(3)]
        reason_text = f"Ketika dilihat dari alasan tertulis, fungsi yang paling sering muncul adalah {', '.join(reason_top)}."
        if m["average_reason_words"] >= 25:
            reason_text += " Alasanmu rata-rata cukup rinci, sehingga banyak pembahasan dapat mengambil konteks dari proses berpikir yang kamu tulis sendiri."
        elif m["average_reason_words"] < 9:
            reason_text += " Sebagian besar alasanmu singkat, jadi hasil tetap personal tetapi lebih banyak bergantung pada best-match dari informasi yang terbatas."
    else:
        reason_text = "Tidak ada alasan tertulis yang bisa dipakai untuk membandingkan pola bahasa dengan pola pilihan jawaban."

    extras = []
    if m["contradiction_count"]:
        extras.append(f"Ada {m['contradiction_count']} alasan yang arahnya berbeda dari fungsi utama pertanyaannya, sehingga proses berpikirmu tidak selalu identik dengan posisi akhir yang kamu pilih.")
    if m["qualified_count"] >= 3:
        extras.append(f"Ada {m['qualified_count']} alasan yang bersifat situasional atau bernuansa, jadi beberapa kecenderunganmu jelas berubah menurut konteks.")

    leads = (
        "Kalau hasil ini dibaca sebagai profil individual,",
        "Yang membuat hasilmu berbeda dari orang lain dengan tipe yang sama adalah komposisi skornya:",
        "Di balik empat huruf MBTI, pola personalmu terlihat dari jarak antar-fungsi dan cara kamu menjelaskan jawaban:",
        "Empat hurufnya hanya ringkasan; ciri yang lebih spesifik terlihat pada susunan skor dan alasanmu:",
    )
    return " ".join([leads[fingerprint], balance, choice_style, reason_text, *extras])


def _overall_conclusion(answers, meaningful, functions, decision):
    m = _profile_metrics(answers, meaningful, functions)
    ranked, scores, counts = m["ranked"], m["scores"], m["counts"]
    first, second, third = ranked[:3]
    first_style, second_style = FUNCTION_STYLE[first], FUNCTION_STYLE[second]
    top_reason = counts.most_common(1)[0][0] if counts else None
    variant = _stable_variant(
        decision.get("type"), first, second, third,
        scores[first], scores[second], scores[third],
        top_reason, m["neutral_count"], m["strong_count"],
        modulo=4,
    )

    intros = (
        "Kesimpulan utama: jika seluruh pola pilihan dan alasanmu digabungkan,",
        "Kesimpulan utama: setelah delapan fungsi dan alasan tertulismu dibaca bersama,",
        "Kesimpulan utama: gambaran yang paling konsisten dari profilmu adalah bahwa",
        "Kesimpulan utama: di luar label empat huruf, pola pribadimu menunjukkan bahwa",
    )
    parts = [
        intros[variant],
        f"{first} ({FUNCTIONS[first]['name']}) dan {second} ({FUNCTIONS[second]['name']}) menjadi dua fungsi terkuatmu, dengan {third} sebagai pola berikutnya.",
        f"Dalam banyak situasi {first_style['focus']}, sedangkan {second} menambahkan sisi bahwa {second_style['focus']}.",
    ]

    gap = scores[first] - scores[second]
    if gap >= 12:
        parts.append(f"Jarak {first} terhadap {second} cukup besar ({gap:.1f} poin), jadi {first} memberi warna yang jauh lebih dominan pada cara kamu memproses keputusan.")
    elif gap <= 3:
        parts.append(f"Skor {first} dan {second} hanya terpaut sekitar {gap:.1f} poin. Artinya, dua fungsi ini hampir seimbang dan kemungkinan besar saling bergantian sesuai konteks.")
    else:
        parts.append(f"{first} memang berada di atas {second}, tetapi jaraknya tidak terlalu ekstrem. Profilmu lebih tepat dibaca sebagai kerja sama dua fungsi daripada dominasi tunggal.")

    if top_reason:
        parts.append(
            f"Dari alasan yang kamu tulis, fungsi yang paling sering muncul adalah {top_reason}. Saat diberi ruang menjelaskan dengan kata-katamu sendiri, pola yang paling sering terlihat adalah bahwa {FUNCTION_STYLE[top_reason]['focus']}."
        )
        if top_reason in {first, second}:
            parts.append("Ini membuat pilihan jawaban dan cara kamu menjelaskan keputusan saling menguatkan pada pola utama yang sama.")
        else:
            parts.append(f"Menariknya, fungsi dari alasan lebih sering menonjolkan {top_reason}, sementara skor keseluruhan lebih menonjolkan {first} dan {second}. Jadi proses penjelasanmu membawa sisi yang tidak sepenuhnya terlihat dari pilihan akhir saja.")

    if decision.get("type"):
        stack = "–".join(decision.get("stack", []))
        parts.append(f"Dalam kerangka MBTI berbasis fungsi, susunan keseluruhan ini paling dekat dengan {decision['type']} ({stack}). Empat huruf itu adalah ringkasan, sedangkan keunikan hasilmu berada pada besar-kecilnya skor fungsi dan pola alasan yang menyertainya.")

    if m["neutral_count"] >= 8:
        parts.append(f"Banyaknya pilihan netral ({m['neutral_count']}) juga membuat profilmu lebih kontekstual: beberapa kecenderungan tampaknya berubah cukup kuat menurut keadaan.")
    elif m["strong_count"] >= 16:
        parts.append(f"Banyaknya jawaban sangat tegas ({m['strong_count']}) membuat sejumlah kecenderungan terlihat lebih mantap dan tidak terlalu bergantung pada posisi tengah skala.")

    endings = (
        f"Secara sederhana, kamu terlihat sebagai orang yang {first_style['focus']}, tetapi tetap membawa sisi {second_style['focus']}. Kekuatan profilmu ada pada cara dua pola itu saling melengkapi.",
        f"Jika diringkas sebagai karakter, kamu cenderung {first_style['focus']}; pada saat yang sama, {second} membuatmu juga memiliki kecenderungan bahwa {second_style['focus']}. Kombinasi inilah yang membedakanmu dari orang lain yang memperoleh tipe MBTI sama.",
        f"Jadi, label tipemu bukan seluruh cerita. Yang lebih khas adalah kombinasi bahwa {first_style['focus']} dan {second_style['focus']}, dengan intensitas yang tercermin pada skor serta alasanmu sendiri.",
        f"Gambaran akhirnya bukan sekadar '{decision.get('type') or 'satu tipe'}', tetapi profil fungsi yang spesifik: {first} paling menonjol, {second} menjadi pendamping utama, dan alasanmu menunjukkan bagaimana fungsi-fungsi itu benar-benar muncul saat kamu menjelaskan keputusan.",
    )
    parts.append(endings[variant])
    return " ".join(parts)


def build_reflection(answers, predictions, functions, decision, name="", age=None, gender=""):
    insights = [question_insight(a, predictions.get(a.id, {})) for a in sorted(answers, key=lambda a: a.id)]
    meaningful = [i for i in insights if i["reason"]]
    opening = profile_opening(name, age, gender, len(meaningful))
    paragraphs = [opening]

    if decision.get("type"):
        stack = "–".join(decision["stack"])
        dominant = decision["stack"][0]
        auxiliary = decision["stack"][1] if len(decision["stack"]) > 1 else None
        intro = (
            f"Dari pola delapan fungsi pada tes ini, kandidat utamamu adalah {decision['type']} dengan susunan {stack}. Fungsi teratasnya adalah {dominant} ({FUNCTIONS[dominant]['name']}), yang berkaitan dengan kecenderungan untuk {FUNCTIONS[dominant]['meaning']}."
        )
        if auxiliary:
            intro += f" Fungsi pendampingnya, {auxiliary} ({FUNCTIONS[auxiliary]['name']}), menambahkan kecenderungan untuk {FUNCTIONS[auxiliary]['meaning']}."
        intro += " Tipe ini diperoleh setelah skor seluruh fungsi dihitung, bukan dari penjumlahan pasangan huruf."
        paragraphs.append(intro)
    else:
        candidates = decision.get("candidates") or []
        if candidates:
            top_candidate = candidates[0]
            paragraphs.append(
                f"Pola fungsi terdekatmu adalah {top_candidate['type']} dengan susunan {'–'.join(top_candidate['stack'])}. Profilmu cukup berimbang, tetapi kandidat ini tetap menjadi susunan yang paling dekat ketika delapan fungsi dibandingkan secara keseluruhan."
            )
        else:
            paragraphs.append("Pola fungsi utama dibaca langsung dari delapan skor fungsi kognitif yang tersedia.")

    # This paragraph is what differentiates two users who happen to end with the
    # same MBTI label: exact function gaps, response intensity, reason functions,
    # and contradictions/qualifiers all shape the wording and content.
    paragraphs.append(_personal_pattern(answers, meaningful, functions, decision))

    if decision.get("status") == "tentative" and decision.get("type"):
        paragraphs.append(
            f"Kandidat utama tetap {decision['type']}. Kandidat lain berada cukup dekat pada skor kecocokan, jadi perbedaannya terutama ada pada urutan dan intensitas fungsi, bukan pada kebutuhan untuk mengganti hasil utama."
        )

    reason_paragraph_indices = {}
    for insight in meaningful:
        reason_paragraph_indices[insight["question_id"]] = len(paragraphs)
        paragraphs.append(" ".join(insight["paragraphs"]))

    if not meaningful:
        paragraphs.append(
            "Karena tidak ada alasan tertulis, pembahasan personal terutama memakai pola pilihan dan skor delapan fungsi. Hasilnya tetap bisa membedakan profil berdasarkan jarak antar-skor, jumlah jawaban tegas, dan banyaknya jawaban netral."
        )

    grouped = {}
    for insight in meaningful:
        if insight["text_function"]:
            grouped.setdefault(insight["text_function"], []).append(insight["question_id"])
    repeat = [(f, ids) for f, ids in grouped.items() if len(ids) > 1]
    for f, ids in sorted(repeat, key=lambda item: (-len(item[1]), item[0])):
        style = FUNCTION_STYLE[f]
        paragraphs.append(
            f"Ada pola berulang pada alasan soal {', '.join(map(str, ids))}: semuanya paling dekat dengan {f} ({FUNCTIONS[f]['name']}). Pengulangan ini menunjukkan bahwa {style['focus']} bukan hanya muncul pada satu jawaban, tetapi beberapa kali dalam cara kamu menjelaskan keputusan. Sisi kuat yang berkaitan dengan pola ini adalah {style['strength']}."
        )

    neutral_count = sum(a.choice == "neutral" for a in answers)
    if neutral_count:
        paragraphs.append(
            f"Ada {neutral_count} pilihan netral dalam jawabanmu. Netral tidak berarti tidak punya pendirian; di sini ia dibaca sebagai keadaan ketika dukungan dan penolakan sama-sama punya tempat, sementara alasan tertulis tetap menentukan fungsi yang paling dekat dengan konteksnya."
        )

    paragraphs.append(
        "Model teks ini belajar dari contoh sintetis dan belum divalidasi pada responden nyata. Setiap alasan nonkosong dipetakan ke fungsi best-match, jadi kualitas penjelasan sangat dipengaruhi oleh seberapa konkret alasan yang ditulis. Alasan yang memuat situasi, pertimbangan, dan konsekuensi biasanya menghasilkan analisis yang lebih spesifik."
    )
    overall_conclusion_index = len(paragraphs)
    paragraphs.append(_overall_conclusion(answers, meaningful, functions, decision))

    return {
        "paragraphs": paragraphs,
        "question_insights": insights,
        "reason_paragraph_indices": reason_paragraph_indices,
        "overall_conclusion_index": overall_conclusion_index,
        "discussed_reason_count": len(meaningful),
        "generated_reason_count": 0,
        "mode": "evidence_local",
        "local_llm_status": "not_requested",
    }
