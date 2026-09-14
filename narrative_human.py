"""Expressive deterministic narration for the non-Qwen path.

This module deliberately does not use an LLM. It combines evidence-grounded
language fragments deterministically from the user's actual answers/reasons so
identical input stays stable while different users can receive substantially
different wording even when their final MBTI type is the same.
"""
import re

from cognitive import FUNCTIONS
from questions import CHOICES, QUESTION_BY_ID
from narrative import (
    FUNCTION_STYLE,
    _overall_conclusion,
    _personal_pattern,
    _stable_variant,
    profile_opening,
)

LABELS = {c["value"]: c["label"] for c in CHOICES}

SUPPORT_OPENINGS = (
    "Fungsi kognitif yang paling dekat dengan alasan ini adalah {pf} ({name}) — {title}. Dari cara kamu menjelaskannya, {focus}.",
    "Alasanmu paling kuat mengarah ke {pf} ({name}). Yang menonjol bukan cuma keputusan akhirnya, tetapi proses yang menunjukkan bahwa {focus}.",
    "Pada bagian ini, pola yang paling terasa adalah {pf} ({name}) — {title}. Cara kamu menyusun alasan memberi gambaran bahwa {focus}.",
    "Kalau alasan ini dibaca sebagai jejak proses berpikir, fungsi terdekatnya adalah {pf} ({name}). Di sini terlihat bahwa {focus}.",
    "Dari delapan fungsi yang dibandingkan, alasan ini paling dekat dengan {pf} ({name}). Inti pertimbangannya menunjukkan bahwa {focus}.",
    "Ada satu pola yang cukup jelas dari alasanmu: {pf} ({name}). Pola itu terlihat karena {focus}.",
    "Cara kamu memberi alasan di sini terasa paling selaras dengan {pf} ({name}). Dengan kata lain, {focus}.",
    "Jika fokusnya bukan pada jawaban akhir tetapi pada cara kamu sampai ke sana, {pf} ({name}) paling menonjol. Itu tampak dari kecenderungan bahwa {focus}.",
    "Alasan ini membawa warna {pf} ({name}) cukup kuat. Yang membuatnya menonjol adalah kecenderungan bahwa {focus}.",
    "Dari struktur alasanmu, {pf} ({name}) muncul sebagai fungsi yang paling dekat. Polanya terlihat ketika {focus}.",
    "Yang paling menonjol dari alasan ini adalah pola {pf} ({name}) — {title}. Ini mengarah pada gambaran bahwa {focus}.",
    "Alasanmu memberi petunjuk kuat ke {pf} ({name}). Bukan karena satu kata tertentu, melainkan karena arah pertimbangannya menunjukkan bahwa {focus}.",
    "Pada konteks ini, {pf} ({name}) terasa paling pas untuk menggambarkan cara kamu memproses keputusan. Artinya, {focus}.",
    "Jejak cara berpikirmu di alasan ini paling dekat dengan {pf} ({name}). Hal itu terlihat dari pola bahwa {focus}.",
    "Jika diterjemahkan ke bahasa fungsi kognitif, alasan ini paling dekat dengan {pf} ({name}) — {title}. Di baliknya terlihat bahwa {focus}.",
    "Alasan ini tidak hanya memberi tahu apa yang kamu pilih, tetapi juga bagaimana kamu menimbangnya. Pola itu paling dekat dengan {pf} ({name}), karena {focus}.",
    "Dari cara kamu menghubungkan alasan dan keputusan, {pf} ({name}) muncul sebagai fungsi yang paling dekat. Di sini, {focus}.",
    "Pola kognitif yang paling terasa dari alasan ini adalah {pf} ({name}). Arah pikirnya menunjukkan bahwa {focus}.",
    "Kalau alasanmu dipetakan ke delapan fungsi, titik terdekatnya ada pada {pf} ({name}). Itu selaras dengan kecenderungan bahwa {focus}.",
    "Alasan ini memberi kesan proses berpikir yang khas {pf} ({name}). Intinya, {focus}.",
)

OPPOSE_OPENINGS = (
    "Fungsi yang paling dekat dengan tema alasan ini tetap {pf} ({name}), tetapi kamu menggambarkan sikap yang berlawanan dengan kecenderungan utamanya.",
    "Alasanmu masih paling dekat dengan ranah {pf} ({name}), hanya saja posisimu terhadap pola itu cenderung menolak atau tidak mengandalkannya.",
    "Tema yang sedang kamu bicarakan paling dekat dengan {pf} ({name}), tetapi isi alasan justru menunjukkan bahwa cara itu bukan pendekatan yang biasa kamu pilih.",
    "Kalau dilihat dari topiknya, alasan ini mengarah ke {pf} ({name}); kalau dilihat dari sikapmu, kamu justru mengambil jarak dari pola tersebut.",
    "Pola yang paling relevan di sini adalah {pf} ({name}), namun alasanmu menunjukkan kecenderungan untuk tidak memakai pola itu sebagai cara utama.",
    "Alasan ini tetap berada paling dekat dengan wilayah {pf} ({name}), tetapi arah yang kamu ceritakan adalah kebalikan dari dukungan langsung terhadap fungsi tersebut.",
    "Fungsi terdekatnya adalah {pf} ({name}), namun bukan karena kamu menggunakannya secara kuat; justru karena alasanmu menjelaskan kapan atau mengapa pola itu tidak kamu pilih.",
    "Secara tema, {pf} ({name}) paling cocok untuk membaca alasan ini, tetapi cara kamu menempatkan diri menunjukkan penolakan terhadap kecenderungan utamanya.",
    "Alasanmu menyentuh wilayah {pf} ({name}), tetapi dengan nada yang berlawanan: pola itu bukan sesuatu yang biasanya kamu andalkan.",
    "Dari delapan fungsi, tema alasan ini paling dekat dengan {pf} ({name}); hanya saja sikap yang muncul lebih banyak menunjukkan ketidakcocokan dengan pola tersebut.",
)

MIXED_OPENINGS = (
    "Fungsi yang paling dekat dengan alasan ini adalah {pf} ({name}), tetapi pola itu muncul secara situasional, bukan sebagai respons yang selalu sama.",
    "Alasanmu paling dekat dengan {pf} ({name}), namun kamu menggambarkannya sebagai pola yang aktif pada kondisi tertentu dan melemah pada kondisi lain.",
    "Di sini {pf} ({name}) tetap menjadi fungsi terdekat, tetapi alasanmu menunjukkan bahwa konteks sangat menentukan kapan pola tersebut muncul.",
    "Tema alasan ini paling dekat dengan {pf} ({name}), hanya saja cara kamu menggunakannya tidak mutlak; ada keadaan yang memunculkan pola itu dan ada yang tidak.",
    "Pola {pf} ({name}) terlihat, tetapi bukan dalam bentuk yang kaku. Alasanmu menunjukkan bahwa kecenderungan tersebut berubah mengikuti situasi.",
    "Alasan ini membawa ciri {pf} ({name}), tetapi dengan nuansa yang cukup kuat: kamu tidak menggunakannya dengan intensitas yang sama di semua keadaan.",
    "Fungsi terdekatnya adalah {pf} ({name}), namun pola yang kamu ceritakan lebih bersifat kondisional daripada tetap.",
    "Jika dipetakan ke fungsi kognitif, alasan ini paling dekat dengan {pf} ({name}), sementara isi kalimatmu menunjukkan bahwa penggunaannya sangat bergantung pada konteks.",
    "Alasanmu memberi sinyal {pf} ({name}), tetapi sinyalnya bukan hitam-putih; ada kondisi yang mendukung pola itu dan ada kondisi yang membuatmu memilih cara lain.",
    "{pf} ({name}) menjadi fungsi yang paling dekat dengan alasan ini, tetapi bentuknya fleksibel dan berubah sesuai situasi yang kamu hadapi.",
)

PROCESS_LINES = (
    "Yang menarik, pola ini membantu menjelaskan apa yang terjadi sebelum keputusan akhirnya muncul. {daily}.",
    "Dalam keseharian, pola seperti ini sering terlihat karena {daily}.",
    "Bukan hanya hasil akhirnya yang penting di sini; cara kamu memproses situasi juga terlihat. {daily}.",
    "Kalau dibawa ke situasi sehari-hari, gambaran ini biasanya muncul ketika {daily}.",
    "Pola ini memberi petunjuk tentang kebiasaan memproses informasi. Dalam praktiknya, {daily}.",
    "Cara berpikir semacam ini biasanya tidak berdiri sendiri; ia tampak lewat kebiasaan konkret. Misalnya, {daily}.",
    "Dari sudut proses kognitif, alasanmu menunjukkan arah yang cukup khas. Dalam kehidupan sehari-hari, {daily}.",
    "Kalau pola ini muncul berulang, bentuk nyatanya sering seperti ini: {daily}.",
    "Yang terasa manusiawi dari pola ini adalah ia muncul lewat kebiasaan kecil sehari-hari. Biasanya, {daily}.",
    "Dalam tindakan nyata, kecenderungan ini sering mengambil bentuk bahwa {daily}.",
    "Pola ini biasanya baru terasa jelas ketika dilihat dari kebiasaan, bukan label. Di keseharian, {daily}.",
    "Jika diterjemahkan dari konsep ke perilaku, pola ini sering berarti bahwa {daily}.",
    "Yang bisa terlihat dari luar bukan nama fungsinya, melainkan kebiasaannya. Dalam banyak situasi, {daily}.",
    "Pada level perilaku, kecenderungan ini sering tampak melalui pola bahwa {daily}.",
    "Alasanmu memberi petunjuk tentang proses yang cukup konsisten: {daily}.",
    "Kalau fungsi ini sedang aktif, salah satu bentuk yang paling mudah terlihat adalah bahwa {daily}.",
    "Cara memproses seperti ini sering muncul secara halus. Salah satu bentuknya adalah bahwa {daily}.",
    "Dalam praktik, pola tersebut biasanya tidak terasa seperti 'menggunakan fungsi', tetapi lebih seperti kebiasaan bahwa {daily}.",
)

STRENGTH_LINES = (
    "Kekuatan yang sering lahir dari pola ini adalah {strength}.",
    "Sisi positifnya terletak pada {strength}.",
    "Kalau digunakan dengan proporsional, pola ini mendukung {strength}.",
    "Bagian yang paling berguna dari kecenderungan ini adalah {strength}.",
    "Pola ini bisa menjadi aset karena memberi ruang pada {strength}.",
    "Ketika berada pada situasi yang tepat, kecenderungan ini membantu lewat {strength}.",
    "Nilai praktis dari pola ini banyak datang dari {strength}.",
    "Salah satu keuntungan terbesarnya adalah {strength}.",
    "Di sisi yang konstruktif, pola ini biasanya memperkuat {strength}.",
    "Jika diarahkan dengan baik, kecenderungan ini membuat {strength} menjadi salah satu kekuatanmu.",
    "Pola ini sering terasa membantu karena mendukung {strength}.",
    "Kekuatan alaminya bukan sekadar pada hasil akhir, tetapi pada {strength}.",
    "Dalam bentuk yang sehat, kecenderungan ini memperbesar kemampuan berupa {strength}.",
    "Salah satu alasan pola ini berguna adalah karena ia mendorong {strength}.",
    "Saat tidak berlebihan, fungsi ini memberi keuntungan lewat {strength}.",
)

SHORT_DEPTH = (
    "Alasanmu cukup singkat, jadi sistem mengambil fungsi yang paling dekat dari informasi yang tersedia. Contoh yang lebih konkret akan membuat pembacaan lebih spesifik.",
    "Karena konteksnya masih ringkas, pembacaan ini memakai pola terdekat yang tersedia. Menambahkan situasi nyata biasanya membuat hasil lebih tajam.",
    "Informasi yang kamu berikan belum panjang, tetapi tetap cukup untuk menentukan best-match. Semakin konkret konteksnya, semakin kaya penjelasan yang bisa dibentuk.",
    "Alasan pendek tetap bisa memberi arah, hanya saja detail prosesnya belum banyak terlihat. Sistem karena itu memilih pola yang paling dekat.",
    "Konteks yang tersedia masih terbatas. Fungsi tetap dipilih secara tegas, sementara kedalaman penjelasan mengikuti banyaknya informasi yang kamu tulis.",
    "Kalimatmu memberi petunjuk utama, tetapi belum banyak rincian tentang situasi atau akibatnya. Karena itu interpretasi berfokus pada inti pola yang paling dekat.",
    "Walaupun singkat, alasanmu tetap membawa satu arah pertimbangan. Sistem menggunakan arah tersebut sebagai dasar klasifikasi fungsi.",
    "Alasan ini langsung ke inti, sehingga pembacaan terutama berangkat dari pola utamanya tanpa banyak konteks tambahan.",
)

MEDIUM_DEPTH = (
    "Alasanmu sudah memberi konteks yang cukup untuk melihat arah pertimbangan, jadi fungsi ini dibaca dari cara kamu menjelaskan pilihan, bukan jawabannya saja.",
    "Panjang alasanmu cukup untuk menunjukkan pola proses berpikir. Hubungan antaride di dalam kalimat ikut membentuk pembacaan fungsi.",
    "Konteks yang kamu berikan sudah cukup membantu membedakan topik alasan dari cara kamu benar-benar mempertimbangkan keputusan.",
    "Alasan ini memiliki konteks yang memadai, sehingga penilaian tidak hanya bertumpu pada kata-kata yang muncul, tetapi juga arah hubungan antarbagian kalimat.",
    "Dari panjang dan struktur alasanmu, sistem mendapat cukup bahan untuk membaca kecenderungan proses, bukan sekadar mencocokkan satu istilah.",
    "Kamu memberi cukup informasi untuk melihat bukan hanya apa yang kamu pikirkan, tetapi juga alasan mengapa pilihan itu terasa masuk akal bagimu.",
    "Alasanmu punya cukup detail untuk memperlihatkan hubungan antara situasi dan keputusan. Itu membuat penjelasannya lebih personal daripada sekadar membaca skor.",
    "Konteksnya tidak terlalu pendek dan tidak terlalu panjang; cukup untuk melihat pola yang melandasi keputusanmu dengan jelas.",
)

LONG_DEPTH = (
    "Alasanmu cukup rinci, sehingga pembacaan tidak bergantung pada satu kata kunci; sebab, prioritas, pengecualian, dan konsekuensi ikut membentuk interpretasinya.",
    "Karena kamu memberi konteks yang panjang, sistem bisa membaca bukan hanya topiknya, tetapi juga bagaimana kamu menghubungkan penyebab dan akibat.",
    "Detail yang kamu tulis memberi lebih banyak jejak proses berpikir. Itu membuat pembahasan bisa menyoroti pola yang tidak akan terlihat dari pilihan jawaban saja.",
    "Alasan panjang seperti ini membantu karena beberapa lapisan pertimbangan bisa terlihat sekaligus: situasi, motif, pengecualian, dan akibatnya.",
    "Konteksmu cukup kaya untuk menunjukkan bahwa keputusan ini bukan hasil satu pertimbangan sederhana. Beberapa hubungan antaride ikut memperkuat pembacaan fungsi.",
    "Banyaknya detail membuat interpretasi lebih spesifik terhadap alasanmu sendiri. Sistem tidak hanya melihat kata yang dominan, tetapi juga alur pertimbangannya.",
    "Kamu memberi cukup banyak konteks sehingga pembahasan bisa membaca pola dari keseluruhan alur kalimat, bukan dari potongan istilah tertentu.",
    "Alasanmu memperlihatkan beberapa tahap proses berpikir. Itu memberi dasar yang lebih kaya untuk mengaitkannya dengan fungsi kognitif yang paling dekat.",
)

CLOSINGS = (
    "Sisi yang perlu dijaga adalah bahwa jika pola ini mengambil terlalu banyak ruang, {watch}.",
    "Dalam kadar yang seimbang pola ini berguna, tetapi jika menjadi terlalu dominan, {watch}.",
    "Titik rawannya muncul ketika kecenderungan ini berjalan tanpa penyeimbang; pada kondisi itu, {watch}.",
    "Pola ini bukan masalah dengan sendirinya. Tantangannya baru terasa ketika intensitasnya terlalu tinggi, karena {watch}.",
    "Kekuatan fungsi ini paling terasa ketika tetap diimbangi pola lain; tanpa keseimbangan itu, {watch}.",
    "Setiap kekuatan punya sisi yang perlu diawasi. Pada pola ini, risikonya adalah bahwa {watch}.",
    "Kalau dipakai terus-menerus sebagai satu-satunya cara, pola ini bisa menjadi kurang fleksibel karena {watch}.",
    "Di sisi lain, terlalu mengandalkan kecenderungan ini juga punya harga: {watch}.",
    "Pola ini bekerja paling baik saat tidak mengambil seluruh ruang keputusan. Jika berlebihan, {watch}.",
    "Yang perlu diperhatikan bukan keberadaan polanya, melainkan intensitasnya. Saat terlalu kuat, {watch}.",
    "Kecenderungan ini tetap perlu pasangan yang menyeimbangkan, sebab tanpa itu {watch}.",
    "Dalam kondisi sehat pola ini membantu, tetapi dalam kondisi berlebihan {watch}.",
    "Sisi lemahnya biasanya baru muncul ketika pola ini digunakan terlalu otomatis; saat itu {watch}.",
    "Karena itu, pola ini paling efektif ketika fleksibel. Kalau terlalu kaku, {watch}.",
    "Tantangan utamanya bukan pada fungsi itu sendiri, tetapi pada kemungkinan bahwa {watch}.",
)

RELATION_ALIGNED = (
    "Pilihan jawaban dan alasanmu mengarah ke fungsi yang sama. Ini membuat posisi akhir dan proses berpikirmu saling menguatkan pada bagian ini.",
    "Yang menarik, fungsi yang diuji oleh soal dan fungsi yang terbaca dari alasan bertemu pada titik yang sama. Jadi jawaban dan penjelasanmu cukup konsisten.",
    "Di soal ini, arah pilihan dan isi alasan berjalan searah. Itu membuat pola fungsi terlihat lebih jelas daripada jika keduanya berbeda.",
    "Jawabanmu tidak berdiri sendiri; alasan yang kamu tulis ikut mendukung fungsi yang memang sedang diperiksa oleh pertanyaan ini.",
    "Ada keselarasan antara apa yang kamu pilih dan cara kamu menjelaskan pilihan tersebut, sehingga fungsi ini mendapat dukungan dari dua sumber sekaligus.",
    "Baik posisi jawaban maupun isi alasan menunjuk ke pola yang sama. Ini membuat bagian ini cukup konsisten secara internal.",
)

RELATION_OTHER = (
    "Soal ini terutama memeriksa {qf} ({qtitle}), tetapi alasanmu lebih dekat dengan {pf} ({ptitle}). Artinya, alasanmu membawa konteks kognitif yang berbeda dari fungsi utama pertanyaan.",
    "Pertanyaannya dirancang untuk membaca {qf}, sementara cara kamu menjelaskan keputusan justru lebih dekat ke {pf}. Jadi proses yang kamu ceritakan menambahkan sisi yang tidak langsung tertangkap dari fungsi soal.",
    "Ada perbedaan menarik di sini: fungsi utama soal adalah {qf}, tetapi alasanmu lebih kuat menunjukkan {pf}. Ini bukan kontradiksi otomatis; keduanya membaca lapisan yang berbeda.",
    "Pilihan ini berada pada soal {qf}, sedangkan narasi alasanmu mengarah ke {pf}. Dengan kata lain, posisi akhir dan proses penjelasanmu menonjolkan aspek kognitif yang berbeda.",
    "Yang diuji oleh pertanyaan adalah {qf}, tetapi bahasa alasanmu lebih dekat ke {pf}. Konteks tambahan ini membantu membuat profilmu lebih spesifik daripada skor soal saja.",
    "Soal menyoroti {qf}, sementara alasan menyoroti {pf}. Perbedaan itu berguna karena menunjukkan bahwa satu keputusan bisa lahir melalui proses kognitif yang berbeda dari fungsi yang ditargetkan pertanyaan.",
)

RELATION_CONTRADICT = (
    "Arah pilihan dan cara kamu menjelaskan alasan tidak sama. Pilihan menunjukkan posisi akhirnya, sedangkan alasan menunjukkan proses yang membawamu ke sana; keduanya tetap dicatat sebagai informasi berbeda.",
    "Ada ketegangan kecil antara jawaban dan alasan. Itu tidak otomatis berarti salah satu keliru, karena keputusan akhir dan proses pertimbangan memang bisa berjalan melalui arah yang berbeda.",
    "Pilihanmu memberi satu sinyal, sementara alasan memberi sinyal lain. Sistem mempertahankan keduanya agar perbedaan antara hasil akhir dan proses berpikir tidak hilang.",
    "Bagian ini justru menarik karena jawaban dan alasan tidak sepenuhnya searah. Perbedaan tersebut dipakai sebagai konteks, bukan dianggap sebagai kesalahan user.",
    "Apa yang kamu pilih dan bagaimana kamu menjelaskannya tidak sepenuhnya sama arah. Hal ini bisa menunjukkan bahwa konteks keputusanmu lebih kompleks daripada skala jawaban saja.",
    "Di sini posisi akhir dan proses berpikir terlihat berbeda. Sistem tidak memaksa salah satunya mengalahkan yang lain, karena keduanya memberi informasi yang berbeda tentang pola dirimu.",
)

NEUTRAL_LINES = (
    "Pilihan netral menunjukkan bahwa posisi akhirnya tidak mutlak ke satu sisi. Alasan tertulis tetap dipakai untuk melihat proses yang paling dekat dengan konteksmu.",
    "Karena kamu memilih netral, sistem tidak membaca bagian ini sebagai 'tidak punya kecenderungan'. Netral tetap menyimpan dua sisi, sementara alasan menentukan fungsi yang paling dekat.",
    "Jawaban netral di sini memberi ruang pada dua arah sekaligus. Penjelasan tertulismu kemudian membantu menunjukkan pola kognitif yang paling dekat di balik posisi tersebut.",
    "Netral berarti konteks berperan cukup besar. Karena itu alasan yang kamu tulis menjadi penting untuk membaca bagaimana kamu sampai pada posisi tengah tersebut.",
    "Posisi netral membuat pilihan akhirnya lebih fleksibel, tetapi alasanmu tetap memberi arah tentang proses berpikir yang mendasarinya.",
    "Di bagian ini kamu tidak mengambil posisi ekstrem. Alasan yang kamu tulis membantu sistem melihat fungsi apa yang paling dekat meskipun jawabannya berada di tengah.",
)


def _pick(bank, *parts, salt=""):
    return bank[_stable_variant(salt, *parts, modulo=len(bank))]


def _depth(reason):
    count = len(re.findall(r"(?u)\b\w+\b", reason))
    if count >= 35:
        return "long"
    if count >= 14:
        return "medium"
    return "short"


def _human_function_explanation(pf, stance, reason, question_id, choice):
    info = FUNCTIONS[pf]
    style = FUNCTION_STYLE[pf]
    values = {
        "pf": pf,
        "name": info["name"],
        "title": info["title"],
        "focus": style["focus"],
        "daily": style["daily"],
        "strength": style["strength"],
        "watch": style["watch"],
    }
    key = (question_id, choice, pf, stance, reason)

    if stance == "oppose":
        opening = _pick(OPPOSE_OPENINGS, *key, salt="opening-oppose").format(**values)
    elif stance == "mixed":
        opening = _pick(MIXED_OPENINGS, *key, salt="opening-mixed").format(**values)
    else:
        opening = _pick(SUPPORT_OPENINGS, *key, salt="opening-support").format(**values)

    process = _pick(PROCESS_LINES, *key, salt="process").format(**values)
    strength = _pick(STRENGTH_LINES, *key, salt="strength").format(**values)
    depth = _depth(reason)
    depth_bank = LONG_DEPTH if depth == "long" else MEDIUM_DEPTH if depth == "medium" else SHORT_DEPTH
    detail = _pick(depth_bank, *key, salt="depth")
    closing = _pick(CLOSINGS, *key, salt="closing").format(**values)

    # Do not make every explanation identically long. The reason itself controls
    # how much language is used, while all versions still mention the function.
    if depth == "short":
        return " ".join((opening, process, detail, closing))
    return " ".join((opening, process, strength, detail, closing))


def question_insight(answer, prediction):
    q = QUESTION_BY_ID[answer.id]
    reason = answer.reason.strip()
    qf = q["function"]
    neutral = answer.choice == "neutral"
    effective = 0 if neutral else answer.choice * q["direction"]
    relationship = "empty"

    if not reason:
        variants = (
            f"Pada soal {q['id']}, kamu memilih {LABELS[answer.choice].lower()}.",
            f"Untuk soal {q['id']}, pilihanmu adalah {LABELS[answer.choice].lower()}.",
            f"Di pertanyaan {q['id']}, kamu mengambil posisi {LABELS[answer.choice].lower()}.",
            f"Pada bagian ini, jawabanmu untuk soal {q['id']} adalah {LABELS[answer.choice].lower()}.",
        )
        paragraphs = [_pick(variants, q["id"], answer.choice, salt="no-reason-opening")]
        if neutral:
            neutral_texts = (
                "Pilihan netral tetap dihitung sebagai dua sisi: dukungan dan penolakan. Karena tidak ada alasan tertulis, sistem tidak menebak motivasi di baliknya.",
                "Netral di sini tidak berarti kosong. Sistem tetap menyimpan dua arah kontribusi, tetapi tanpa alasan tertulis tidak ada konteks tambahan yang bisa dibaca.",
                "Jawaban netral tetap membawa informasi, hanya saja tanpa alasan sistem tidak menambahkan interpretasi tentang mengapa kamu memilih posisi tengah.",
            )
            paragraphs.append(_pick(neutral_texts, q["id"], answer.choice, salt="no-reason-neutral"))
        else:
            action = "mendukung" if effective > 0 else "kurang mendukung"
            info = FUNCTIONS[qf]
            no_reason = (
                f"Dengan arah pernyataan soal ini, pilihanmu {action} pola {qf} ({info['name']}). Karena tidak ada alasan tertulis, bagian ini dibaca dari pilihan jawaban saja.",
                f"Pilihan tersebut {action} {qf} ({info['name']}), fungsi yang berkaitan dengan kecenderungan untuk {info['meaning']}. Tanpa alasan, sistem tidak menambahkan cerita yang tidak kamu tulis.",
                f"Dari skala jawaban, posisi ini {action} pola {qf}. Fungsi itu berhubungan dengan kecenderungan untuk {info['meaning']}; konteks motivasinya tidak ditebak karena kolom alasan kosong.",
            )
            paragraphs.append(_pick(no_reason, q["id"], answer.choice, qf, salt="no-reason-body"))
    else:
        lead_variants = (
            f"Di soal {q['id']}, kamu memilih {LABELS[answer.choice].lower()}, lalu menulis: “{reason}”",
            f"Untuk pertanyaan {q['id']}, pilihanmu adalah {LABELS[answer.choice].lower()}. Alasanmu: “{reason}”",
            f"Pada soal {q['id']}, kamu mengambil posisi {LABELS[answer.choice].lower()} dan menjelaskan: “{reason}”",
            f"Di bagian {q['id']}, jawabanmu {LABELS[answer.choice].lower()}, dengan alasan: “{reason}”",
            f"Soal {q['id']} kamu jawab {LABELS[answer.choice].lower()}. Kamu menambahkan konteks: “{reason}”",
        )
        paragraphs = [_pick(lead_variants, q["id"], answer.choice, reason, salt="reason-lead")]
        qualified = bool(re.search(r"\b(tapi|tetapi|namun|tergantung|kadang|kalau|kecuali)\b", reason, re.I))

        if prediction.get("accepted") and prediction.get("function") in FUNCTIONS:
            pf, stance = prediction["function"], prediction["stance"]
            paragraphs.append(_human_function_explanation(pf, stance, reason, q["id"], answer.choice))

            relationship = "qualified" if neutral or qualified or stance == "mixed" else "other_function" if pf != qf else "aligned"
            if pf == qf and not neutral and stance != "mixed":
                agrees = (effective > 0) == (stance == "support")
                if not agrees:
                    relationship = "contradictory"
                    paragraphs.append(_pick(RELATION_CONTRADICT, q["id"], reason, pf, salt="contradict"))
                else:
                    paragraphs.append(_pick(RELATION_ALIGNED, q["id"], reason, pf, salt="aligned"))
            elif pf != qf:
                paragraphs.append(_pick(RELATION_OTHER, q["id"], reason, pf, qf, salt="other").format(
                    qf=qf, qtitle=FUNCTIONS[qf]["title"], pf=pf, ptitle=FUNCTIONS[pf]["title"]
                ))
        else:
            relationship = "unclear"
            info = FUNCTIONS[qf]
            defensive = (
                f"Model teks tidak dapat memakai hasil klasifikasi alasan ini, sehingga pembahasan sementara mengikuti fungsi utama soal: {qf} ({info['name']}).",
                f"Klasifikasi teks tidak tersedia untuk alasan ini. Agar penjelasan tetap berjalan, sistem sementara merujuk pada fungsi soal, yaitu {qf} ({info['name']}).",
            )
            paragraphs.append(_pick(defensive, q["id"], reason, salt="defensive"))

        if neutral:
            paragraphs.append(_pick(NEUTRAL_LINES, q["id"], reason, salt="neutral-line"))

    return {
        "question_id": q["id"], "question": q["text"], "choice": answer.choice,
        "choice_label": LABELS[answer.choice], "question_function": qf,
        "reason": reason, "relationship": relationship,
        "text_function": prediction.get("function") if prediction.get("accepted") else None,
        "text_stance": prediction.get("stance", "unknown"),
        "text_recognized": bool(prediction.get("accepted")),
        "text_score": prediction.get("model_score", 0.0),
        "paragraphs": paragraphs, "evidence": [reason] if reason else [],
    }


def build_reflection(answers, predictions, functions, decision, name="", age=None, gender=""):
    insights = [question_insight(a, predictions.get(a.id, {})) for a in sorted(answers, key=lambda a: a.id)]
    meaningful = [i for i in insights if i["reason"]]
    opening = profile_opening(name, age, gender, len(meaningful))
    paragraphs = [opening]

    if decision.get("type"):
        stack = "–".join(decision["stack"])
        dominant = decision["stack"][0]
        auxiliary = decision["stack"][1] if len(decision["stack"]) > 1 else None
        intro_variants = (
            f"Dari pola delapan fungsi, kandidat utamamu adalah {decision['type']} dengan susunan {stack}. Fungsi teratasnya {dominant} ({FUNCTIONS[dominant]['name']}).",
            f"Ketika seluruh skor disusun, profilmu paling dekat dengan {decision['type']} ({stack}). Fungsi yang memimpin adalah {dominant} ({FUNCTIONS[dominant]['name']}).",
            f"Hasil keseluruhan menempatkan {decision['type']} sebagai kandidat utama, dengan urutan fungsi {stack}. Pola teratas datang dari {dominant} ({FUNCTIONS[dominant]['name']}).",
            f"Empat huruf yang paling dekat dengan susunan skormu adalah {decision['type']}. Di balik label itu, urutan fungsinya adalah {stack}, dengan {dominant} sebagai fungsi teratas.",
            f"Jika delapan fungsi dipetakan ke susunan MBTI, hasilmu paling dekat dengan {decision['type']} ({stack}). Fungsi yang memberi warna terbesar adalah {dominant} ({FUNCTIONS[dominant]['name']}).",
            f"Susunan fungsi yang paling cocok dengan hasilmu adalah {stack}, yang mengarah ke {decision['type']}. Di posisi teratas ada {dominant} ({FUNCTIONS[dominant]['name']}).",
        )
        intro = _pick(intro_variants, decision.get("type"), stack, len(meaningful), salt="intro-type")
        if auxiliary:
            aux_variants = (
                f" Fungsi pendampingnya adalah {auxiliary} ({FUNCTIONS[auxiliary]['name']}), yang menambahkan kecenderungan untuk {FUNCTIONS[auxiliary]['meaning']}.",
                f" {auxiliary} ({FUNCTIONS[auxiliary]['name']}) berada sebagai pendamping utama dan memberi lapisan tambahan berupa kecenderungan untuk {FUNCTIONS[auxiliary]['meaning']}.",
                f" Di belakangnya, {auxiliary} ({FUNCTIONS[auxiliary]['name']}) ikut membentuk pola melalui kecenderungan untuk {FUNCTIONS[auxiliary]['meaning']}.",
                f" Fungsi kedua, {auxiliary}, membuat profilmu tidak hanya bergantung pada {dominant}; ia menambahkan kecenderungan untuk {FUNCTIONS[auxiliary]['meaning']}.",
            )
            intro += _pick(aux_variants, decision.get("type"), dominant, auxiliary, salt="intro-aux")
        intro += " Tipe ini dihitung dari pola fungsi, bukan sekadar penjumlahan pasangan huruf."
        paragraphs.append(intro)
    else:
        candidates = decision.get("candidates") or []
        if candidates:
            top = candidates[0]
            paragraphs.append(
                f"Susunan fungsi terdekatmu adalah {top['type']} ({'–'.join(top['stack'])}). Profilnya cukup berimbang, tetapi susunan ini tetap menjadi kecocokan tertinggi saat seluruh fungsi dibandingkan."
            )
        else:
            paragraphs.append("Pola fungsi utama dibaca langsung dari delapan skor fungsi kognitif yang tersedia.")

    paragraphs.append(_personal_pattern(answers, meaningful, functions, decision))

    if decision.get("status") == "tentative" and decision.get("type"):
        tentative = (
            f"Kandidat utama tetap {decision['type']}. Kandidat lain berada cukup dekat, jadi perbedaannya terutama terletak pada urutan dan intensitas fungsi.",
            f"Beberapa susunan lain memiliki skor yang berdekatan, tetapi {decision['type']} tetap dipakai sebagai hasil utama karena posisinya paling dekat secara keseluruhan.",
            f"Jarak dengan kandidat berikutnya tidak terlalu besar. Meski begitu, pola yang paling dekat tetap {decision['type']}; nuansanya ada pada besar-kecil skor tiap fungsi.",
            f"Hasil ini punya beberapa kandidat pembanding yang cukup dekat. Sistem tetap memakai {decision['type']} sebagai titik utama, lalu detail fungsi digunakan untuk membedakan profil personalmu.",
        )
        paragraphs.append(_pick(tentative, decision.get("type"), len(meaningful), salt="tentative"))

    reason_paragraph_indices = {}
    for insight in meaningful:
        reason_paragraph_indices[insight["question_id"]] = len(paragraphs)
        paragraphs.append(" ".join(insight["paragraphs"]))

    if not meaningful:
        no_reason_summary = (
            "Karena tidak ada alasan tertulis, pembahasan personal terutama memakai pola pilihan dan skor delapan fungsi. Profil tetap dibedakan melalui jarak antar-skor, jawaban tegas, dan pilihan netral.",
            "Kamu belum menulis alasan, jadi personalisasi berasal dari pola skor dan intensitas jawaban. Itu tetap bisa membedakan dua orang dengan tipe yang sama, meski tidak sedalam saat alasan tersedia.",
            "Tanpa alasan tertulis, sistem tidak menebak proses yang tidak kamu ceritakan. Perbedaan personal tetap dibaca dari komposisi delapan fungsi dan pola pilihanmu.",
        )
        paragraphs.append(_pick(no_reason_summary, decision.get("type"), salt="no-reason-summary"))

    grouped = {}
    for insight in meaningful:
        if insight["text_function"]:
            grouped.setdefault(insight["text_function"], []).append(insight["question_id"])
    repeat = [(f, ids) for f, ids in grouped.items() if len(ids) > 1]
    repeat_templates = (
        "Ada pola berulang pada alasan soal {ids}: semuanya paling dekat dengan {f} ({name}). Ini menunjukkan bahwa {focus} muncul lebih dari sekali dalam cara kamu menjelaskan keputusan.",
        "Fungsi {f} ({name}) muncul berulang pada soal {ids}. Pengulangan ini membuat pola bahwa {focus} terlihat sebagai kecenderungan yang cukup konsisten.",
        "Beberapa alasanmu—soal {ids}—bertemu pada fungsi {f} ({name}). Artinya, kecenderungan bahwa {focus} bukan cuma muncul di satu konteks.",
        "Ada jejak {f} yang berulang di soal {ids}. Karena muncul pada beberapa alasan, pola {focus} mendapat dukungan dari lebih dari satu situasi.",
        "Soal {ids} sama-sama menghasilkan best-match {f} ({name}). Pengulangan ini memperkuat gambaran bahwa {focus} cukup sering hadir dalam proses berpikirmu.",
        "Saat alasan-alasanmu dikelompokkan, soal {ids} berkumpul pada {f} ({name}). Itu menandakan pola {focus} muncul secara berulang, bukan kebetulan sekali saja.",
    )
    for f, ids in sorted(repeat, key=lambda item: (-len(item[1]), item[0])):
        template = _pick(repeat_templates, f, *ids, salt="repeat")
        paragraphs.append(template.format(
            ids=", ".join(map(str, ids)), f=f, name=FUNCTIONS[f]["name"], focus=FUNCTION_STYLE[f]["focus"]
        ))

    neutral_count = sum(a.choice == "neutral" for a in answers)
    if neutral_count:
        neutral_summary = (
            f"Ada {neutral_count} pilihan netral. Di sistem ini netral tetap membawa dua sisi kontribusi, sementara alasan tertulis dipakai untuk membaca proses yang paling dekat dengan konteksnya.",
            f"Kamu menggunakan jawaban netral sebanyak {neutral_count} kali. Itu membuat sebagian profilmu lebih kontekstual, karena beberapa kecenderungan tidak selalu bergerak ke satu arah.",
            f"Sebanyak {neutral_count} jawaban berada di posisi netral. Sistem tetap menghitungnya, tetapi membaca alasan untuk memahami fungsi yang paling dekat di balik posisi tengah tersebut.",
            f"Ada {neutral_count} respons netral dalam tesmu. Bagian ini memberi nuansa bahwa beberapa pola dirimu berubah menurut keadaan, bukan selalu tetap pada satu kutub.",
        )
        paragraphs.append(_pick(neutral_summary, neutral_count, decision.get("type"), salt="neutral-summary"))

    methodology = (
        "Model teks ini belajar dari contoh sintetis dan belum divalidasi pada responden nyata. Setiap alasan nonkosong dipetakan ke fungsi best-match, sehingga kualitas penjelasan sangat dipengaruhi oleh seberapa konkret alasan yang ditulis.",
        "Perlu diingat, classifier masih belajar dari data sintetis. Sistem selalu memilih fungsi terdekat untuk setiap alasan, jadi penjelasan yang paling berguna biasanya datang dari alasan yang memuat situasi, pertimbangan, dan akibat yang jelas.",
        "Analisis teks ini memakai model lokal berbasis data sintetis. Karena pendekatannya best-match, alasan yang lebih konkret memberi dasar yang lebih kaya daripada jawaban yang sangat singkat atau tidak relevan.",
        "Sistem sengaja tidak abstain pada alasan nonkosong: setiap teks dipetakan ke fungsi terdekat. Karena itu kualitas input tetap penting; semakin jelas konteks yang kamu tulis, semakin spesifik pembahasannya.",
    )
    paragraphs.append(_pick(methodology, decision.get("type"), len(meaningful), neutral_count, salt="methodology"))

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
