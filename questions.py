"""Original exploratory items, NOT the licensed MBTI questionnaire.

Each function has four items: two forward and two reverse keyed.
The browser sends IDs, never scoring keys. Neutral is an explicit category.
"""
QUESTIONNAIRE_VERSION = "innerself-cognitive-2"
SECTIONS = {
    "experience": {"title": "Mengolah pengalaman", "icon": "compass"},
    "possibilities": {"title": "Melihat kemungkinan", "icon": "lightbulb"},
    "reasoning": {"title": "Menguji pemikiran", "icon": "book-open"},
    "values": {"title": "Menimbang nilai", "icon": "heart"},
}
ITEMS = [
    ("experience", "Se", 1, "Saat situasi berubah, aku cepat memperhatikan apa yang sedang terjadi dan menyesuaikan tindakan secara langsung."),
    ("experience", "Si", 1, "Untuk memahami keadaan baru, aku membandingkannya dengan pengalaman serupa yang pernah kualami."),
    ("experience", "Se", -1, "Ketika mencoba kegiatan baru, aku jarang belajar lewat percobaan langsung dengan benda atau situasi di depanku."),
    ("experience", "Si", -1, "Pengalaman sebelumnya jarang menjadi acuanku saat menentukan cara menghadapi situasi yang mirip."),
    ("experience", "Se", 1, "Aku mudah menangkap detail yang sedang terlihat, terdengar, atau terasa, lalu memakainya untuk bertindak."),
    ("experience", "Si", 1, "Aku menyadari ketika detail sebuah pengalaman berbeda dari yang kuingat, lalu memeriksa perbedaan itu."),
    ("experience", "Se", -1, "Aku sering melewatkan perubahan nyata di sekitarku karena tidak memperhatikan keadaan saat ini."),
    ("experience", "Si", -1, "Saat mengulang kegiatan, aku jarang memeriksa apakah langkahnya sesuai dengan pengalaman yang sebelumnya berhasil."),
    ("possibilities", "Ne", 1, "Satu gagasan sering membuatku menemukan berbagai kemungkinan lain yang belum berkaitan secara jelas."),
    ("possibilities", "Ni", 1, "Aku menggabungkan berbagai petunjuk menjadi satu gambaran tentang arah suatu keadaan."),
    ("possibilities", "Ne", -1, "Saat membahas ide, aku jarang terpikir alternatif di luar kemungkinan yang sudah disebutkan."),
    ("possibilities", "Ni", -1, "Aku jarang mencari benang merah atau makna yang menyatukan berbagai kejadian."),
    ("possibilities", "Ne", 1, "Aku senang mempertanyakan bagaimana sesuatu bisa diubah dan menjelajahi beberapa kemungkinan sekaligus."),
    ("possibilities", "Ni", 1, "Sebelum memilih langkah, aku sering memikirkan ke mana pola kejadian ini akan mengarah dalam jangka panjang."),
    ("possibilities", "Ne", -1, "Aku kurang tertarik menghubungkan ide dari bidang berbeda untuk menemukan kemungkinan baru."),
    ("possibilities", "Ni", -1, "Aku cenderung melihat kejadian sebagai hal terpisah dan jarang merangkainya menjadi gambaran menyeluruh."),
    ("reasoning", "Te", 1, "Saat mengerjakan sesuatu, aku memakai hasil yang bisa diperiksa untuk menentukan cara kerja yang efektif."),
    ("reasoning", "Ti", 1, "Aku perlu memahami mengapa suatu penjelasan masuk akal dan apakah bagian-bagiannya konsisten."),
    ("reasoning", "Te", -1, "Saat mengelola pekerjaan, aku jarang menetapkan ukuran keberhasilan atau mengecek apakah cara kerjanya efektif."),
    ("reasoning", "Ti", -1, "Aku biasanya menerima kesimpulan tanpa memeriksa apakah alasan yang mendasarinya saling bertentangan."),
    ("reasoning", "Te", 1, "Aku senang menyusun prioritas, pembagian tugas, dan ukuran hasil agar pekerjaan benar-benar selesai."),
    ("reasoning", "Ti", 1, "Ketika menemukan masalah, aku membongkar asumsi dan cara kerja dasarnya sebelum menerima penjelasan."),
    ("reasoning", "Te", -1, "Data hasil dan ukuran kinerja jarang kupakai ketika memilih di antara beberapa cara kerja."),
    ("reasoning", "Ti", -1, "Ketepatan definisi dan konsistensi logika bukan hal yang sering kuperiksa saat memahami sebuah ide."),
    ("values", "Fe", 1, "Saat mengambil keputusan bersama, aku memperhatikan kebutuhan orang-orang yang terdampak dan mencari titik temu."),
    ("values", "Fi", 1, "Aku memeriksa apakah pilihanku selaras dengan nilai pribadi yang sungguh kuanggap penting."),
    ("values", "Fe", -1, "Saat berdiskusi, aku jarang menyesuaikan penyampaian agar orang lain merasa didengar."),
    ("values", "Fi", -1, "Ketika memilih sesuatu, aku jarang memikirkan apakah pilihan itu sesuai dengan keyakinan pribadiku."),
    ("values", "Fe", 1, "Aku berusaha memahami suasana emosional kelompok dan menyesuaikan tindakan agar hubungan tetap terjaga."),
    ("values", "Fi", 1, "Aku dapat mempertahankan pilihan yang sesuai nuraniku meskipun orang lain menginginkan hal berbeda."),
    ("values", "Fe", -1, "Mencari kesepahaman dan mempertimbangkan perasaan bersama jarang menjadi perhatianku saat ada konflik."),
    ("values", "Fi", -1, "Aku mudah mengabaikan nilai yang penting bagiku tanpa merasa perlu memeriksa keselarasan dengan diriku."),
]
QUESTIONS = [
    {"id": i, "section": section, "function": function, "direction": direction, "text": text}
    for i, (section, function, direction, text) in enumerate(ITEMS, 1)
]
QUESTION_BY_ID = {q["id"]: q for q in QUESTIONS}
CHOICES = [
    {"value": -3, "label": "Sangat tidak setuju"},
    {"value": -2, "label": "Tidak setuju"},
    {"value": -1, "label": "Agak tidak setuju"},
    {"value": "neutral", "label": "Netral · kadang iya, kadang tidak", "contributions": [-1, 1]},
    {"value": 1, "label": "Agak setuju"},
    {"value": 2, "label": "Setuju"},
    {"value": 3, "label": "Sangat setuju"},
]
