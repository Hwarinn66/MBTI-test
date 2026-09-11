"""The canonical questionnaire: clients submit IDs and raw agreement scores only."""

QUESTIONNAIRE_VERSION = "innerself-1"
DIMENSIONS = {
    "EI": {"title": "Energi sosial", "first": "Ekstroversi", "second": "Introversi", "icon": "users"},
    "SN": {"title": "Cara memahami", "first": "Sensing", "second": "Intuisi", "icon": "lightbulb"},
    "TF": {"title": "Cara memutuskan", "first": "Thinking", "second": "Feeling", "icon": "heart"},
    "JP": {"title": "Ritme keseharian", "first": "Judging", "second": "Perceiving", "icon": "compass"},
}

# Last value is the preferred letter when a respondent AGREES. Alternating
# wording prevents every agreement from mechanically producing the same type.
ITEMS = [
    ("EI", "Aku merasa lebih berenergi setelah menghabiskan waktu bersama banyak orang.", "E"),
    ("EI", "Setelah hari yang sibuk, aku lebih ingin mengisi energi dengan waktu sendiri.", "I"),
    ("EI", "Di lingkungan baru, aku biasanya memulai percakapan lebih dulu.", "E"),
    ("EI", "Aku lebih nyaman memikirkan ide sendiri sebelum membicarakannya.", "I"),
    ("EI", "Aku menikmati kegiatan yang membuatku bertemu banyak orang baru.", "E"),
    ("EI", "Aku lebih menikmati percakapan mendalam dengan satu orang daripada obrolan kelompok besar.", "I"),
    ("EI", "Membicarakan sesuatu dengan orang lain membantuku menjernihkan pikiran.", "E"),
    ("EI", "Aku membutuhkan jeda sendiri setelah banyak berinteraksi, meskipun kegiatannya menyenangkan.", "I"),
    ("SN", "Saat mempelajari sesuatu, aku lebih terbantu oleh contoh konkret daripada gambaran abstrak.", "S"),
    ("SN", "Aku tertarik mencari pola dan kemungkinan di balik informasi yang kuterima.", "N"),
    ("SN", "Aku cenderung memperhatikan detail yang nyata sebelum memikirkan makna besarnya.", "S"),
    ("SN", "Aku menikmati membayangkan bagaimana sesuatu bisa berbeda di masa depan.", "N"),
    ("SN", "Pengalaman langsung lebih meyakinkanku daripada dugaan tentang apa yang mungkin terjadi.", "S"),
    ("SN", "Saat berdiskusi, pikiranku sering menghubungkan satu ide dengan kemungkinan lain.", "N"),
    ("SN", "Aku lebih suka petunjuk yang jelas dan berurutan saat mencoba tugas baru.", "S"),
    ("SN", "Aku senang mengeksplorasi teori meskipun manfaat praktisnya belum terlihat.", "N"),
    ("TF", "Saat mengambil keputusan sulit, aku mendahulukan konsistensi logika.", "T"),
    ("TF", "Dampak keputusan terhadap perasaan orang lain menjadi pertimbangan utamaku.", "F"),
    ("TF", "Aku nyaman menyampaikan kritik langsung jika itu membantu memperbaiki masalah.", "T"),
    ("TF", "Saat memberi masukan, menjaga perasaan penerimanya sama pentingnya dengan isi masukan.", "F"),
    ("TF", "Dalam perdebatan, aku paling ingin menemukan argumen yang paling masuk akal.", "T"),
    ("TF", "Nilai pribadiku banyak memengaruhi pilihan, sekalipun pilihan lain lebih efisien.", "F"),
    ("TF", "Aku cenderung memakai kriteria yang sama untuk semua orang saat menilai keputusan.", "T"),
    ("TF", "Aku ingin memahami keadaan pribadi seseorang sebelum menilai tindakannya.", "F"),
    ("JP", "Aku merasa lebih tenang jika kegiatan harianku sudah direncanakan.", "J"),
    ("JP", "Aku senang membiarkan beberapa pilihan tetap terbuka sampai situasinya lebih jelas.", "P"),
    ("JP", "Aku lebih suka menyelesaikan pekerjaan lebih awal daripada mendekati tenggat.", "J"),
    ("JP", "Perubahan rencana mendadak sering terasa menarik bagiku.", "P"),
    ("JP", "Aku senang membuat daftar dan menuntaskan tugas satu per satu.", "J"),
    ("JP", "Aku nyaman menyesuaikan cara kerja sambil berjalan tanpa rencana yang terlalu rinci.", "P"),
    ("JP", "Aku lebih suka keputusan sudah ditetapkan daripada terus mempertimbangkan banyak pilihan.", "J"),
    ("JP", "Aku menikmati ruang untuk bertindak spontan dalam keseharian.", "P"),
]
QUESTIONS = [
    {"id": i, "dimension": dim, "text": text, "agree_letter": letter}
    for i, (dim, text, letter) in enumerate(ITEMS, 1)
]
QUESTION_BY_ID = {q["id"]: q for q in QUESTIONS}
