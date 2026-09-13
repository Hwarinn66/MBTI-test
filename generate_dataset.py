"""Reproducible Indonesian SYNTHETIC corpus; no real respondents or AI API.

The target is the function expressed in a sentence, NOT the writer's true type.
Paraphrases of one semantic family never cross train/validation/test splits.
"""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
SEED = 20260912
VERSION = "synthetic-cognitive-v1"

# Twelve authored semantic families per function. Their labels are hypotheses,
# not expert annotations. Distinct held-out families test template generalization.
STEMS = {
    "Te": [
        "menetapkan target terukur dan membagi pekerjaan agar hasilnya efektif",
        "mengecek data kinerja untuk memilih cara yang paling efisien",
        "menyusun prioritas dan tenggat agar pekerjaan selesai tepat waktu",
        "membandingkan hasil nyata sebelum memutuskan metode kerja",
        "mengatur sumber daya dan pembagian tugas berdasarkan tujuan bersama",
        "memakai indikator keberhasilan untuk mengevaluasi proses pekerjaan",
        "memilih solusi yang sudah terbukti meningkatkan produktivitas",
        "menentukan standar hasil yang jelas supaya orang tahu tugasnya",
        "mengubah rencana kerja setelah melihat ukuran hasil di lapangan",
        "membuat urutan tindakan praktis untuk mencapai sasaran proyek",
        "mengevaluasi biaya dan manfaat nyata sebelum menjalankan keputusan",
        "mengorganisasi waktu dan tenaga supaya sasaran yang disepakati tercapai",
    ],
    "Ti": [
        "memeriksa konsistensi logika sebelum menerima sebuah penjelasan",
        "membongkar asumsi untuk memahami cara kerja sebuah sistem",
        "mencari pertentangan antarargumen sebelum menyimpulkan sesuatu",
        "memperjelas definisi supaya penalarannya tidak rancu",
        "menelusuri sebab akibat untuk mengerti mengapa solusi itu bekerja",
        "menguji apakah kesimpulan benar benar mengikuti premisnya",
        "menganalisis prinsip dasar walaupun belum ada manfaat praktis",
        "membangun kerangka pemahaman yang masuk akal bagi pikiranku",
        "mempertanyakan aturan yang alasan logisnya belum kupahami",
        "memeriksa ketepatan konsep meskipun banyak orang sudah menyetujuinya",
        "menguji contoh pengecualian untuk mencari kelemahan penjelasan",
        "meneliti hubungan antarbagian sampai mekanismenya terasa konsisten",
    ],
    "Fe": [
        "mempertimbangkan perasaan kelompok sebelum mengambil keputusan bersama",
        "menyesuaikan cara bicara agar orang lain merasa didengar",
        "mencari titik temu ketika kebutuhan anggota kelompok berbeda",
        "memperhatikan suasana emosional supaya hubungan tetap terjaga",
        "mengajak orang yang tersisih agar merasa dilibatkan dalam kelompok",
        "mendengarkan kebutuhan bersama sebelum mengusulkan kesepakatan",
        "menyampaikan kritik dengan mempertimbangkan perasaan penerimanya",
        "membantu meredakan konflik agar semua pihak dapat berdialog",
        "memeriksa apakah keputusan bersama membuat seseorang terabaikan",
        "mengubah penyampaian ketika melihat lawan bicara merasa tidak nyaman",
        "mempertemukan kepentingan orang yang berselisih tanpa mempermalukan mereka",
        "menjaga komunikasi yang menghargai norma dan kebutuhan komunitas",
    ],
    "Fi": [
        "memastikan pilihanku selaras dengan nilai pribadi yang kuyakini",
        "mendengarkan nurani meskipun keputusan itu tidak disukai orang lain",
        "memeriksa apa yang sungguh penting bagiku sebelum berkomitmen",
        "menolak tindakan yang bertentangan dengan prinsip pribadiku",
        "menjaga keaslian diriku daripada mengikuti harapan orang begitu saja",
        "merenungkan perasaanku sendiri untuk memahami nilai yang terluka",
        "memilih tindakan yang terasa jujur terhadap keyakinanku",
        "mempertahankan batas pribadi karena itu sesuai dengan nuraniku",
        "membela hal yang kuanggap benar walaupun tidak mendapat dukungan",
        "menimbang makna personal suatu pilihan sebelum mengikuti kelompok",
        "mengenali alasan batin yang membuat suatu keputusan terasa selaras",
        "menghormati nilai unik seseorang tanpa memaksanya sama denganku",
    ],
    "Ne": [
        "menghubungkan satu ide dengan banyak kemungkinan baru",
        "mencari berbagai alternatif sebelum memilih satu pendekatan",
        "membayangkan beberapa cara berbeda untuk mengubah keadaan",
        "menggabungkan gagasan dari bidang berbeda menjadi peluang baru",
        "mempertanyakan bagaimana jadinya kalau aturan yang biasa diubah",
        "melompat dari satu kemungkinan ke kemungkinan lain saat berdiskusi",
        "mencoba sudut pandang baru walaupun gagasannya belum praktis",
        "membiarkan beberapa pilihan terbuka untuk menemukan ide tak terduga",
        "menemukan kaitan yang tidak biasa antara dua topik berbeda",
        "mengembangkan beberapa skenario alternatif dari sebuah informasi",
        "melihat berbagai kegunaan baru dari benda yang sama",
        "memunculkan pilihan tambahan ketika orang lain merasa opsinya habis",
    ],
    "Ni": [
        "merangkai berbagai petunjuk menjadi satu gambaran arah jangka panjang",
        "mencari benang merah di balik kejadian yang tampaknya terpisah",
        "merenungkan pola sampai muncul satu pemahaman menyeluruh",
        "memikirkan ke mana rangkaian kejadian ini akhirnya mengarah",
        "menyatukan banyak informasi menjadi satu visi yang terasa utuh",
        "memperhatikan makna tersembunyi di balik pola yang berulang",
        "menyaring berbagai kemungkinan menuju satu arah yang paling masuk akal",
        "membayangkan dampak jangka panjang dari kecenderungan yang sedang terlihat",
        "mencari pola mendasar yang menjelaskan perubahan selama ini",
        "menyusun gambaran besar sebelum menentukan arah hidup",
        "mendalami satu wawasan sampai hubungannya dengan masa depan menjadi jelas",
        "menafsirkan rangkaian tanda untuk memahami tema yang menyatukannya",
    ],
    "Se": [
        "memperhatikan keadaan nyata saat ini lalu segera menyesuaikan tindakan",
        "belajar lewat mencoba langsung dengan benda yang ada di depanku",
        "menangkap perubahan suara gerak atau warna yang sedang terjadi",
        "merespons peluang konkret yang baru muncul di lapangan",
        "menyesuaikan gerakan berdasarkan apa yang kulihat dan kurasakan langsung",
        "mengamati detail lingkungan sebelum mengambil tindakan saat itu juga",
        "memeriksa kondisi fisik sebenarnya daripada hanya membayangkannya",
        "mencoba alat secara langsung untuk mengetahui respons nyatanya",
        "mengubah langkah dengan cepat ketika keadaan di depan mata berubah",
        "menikmati pengalaman indrawi yang sedang berlangsung di sekitarku",
        "mengikuti perkembangan langsung dan bertindak sesuai situasi terbaru",
        "menangani masalah di tempat dengan memperhatikan benda dan keadaan sekitar",
    ],
    "Si": [
        "membandingkan keadaan sekarang dengan pengalaman serupa yang kuingat",
        "mengingat detail pengalaman lama untuk memeriksa perubahan saat ini",
        "menggunakan langkah yang pernah berhasil sebagai acuan kegiatan baru",
        "memeriksa apakah sesuatu berbeda dari kebiasaan yang sudah kukenal",
        "mengingat urutan kejadian sebelumnya ketika menghadapi persoalan serupa",
        "mengacu pada pengalaman pribadi yang nyata sebelum menerima perubahan",
        "mencocokkan detail hari ini dengan catatan dan ingatan sebelumnya",
        "mempertahankan rutinitas yang terbukti nyaman dari pengalaman berulang",
        "menyadari perbedaan kecil karena masih ingat keadaan yang sebelumnya",
        "memakai pembelajaran dari pengalaman terdahulu agar kesalahan tidak berulang",
        "menautkan pengalaman baru dengan kesan pribadi yang pernah kurasakan",
        "meninjau cara yang sudah kukenal sebelum menyesuaikannya dengan keadaan baru",
    ],
}
UNCLEAR = [
    "aku suka berkumpul tapi aku jarang bicara",
    "saya senang keramaian tetapi lebih banyak diam",
    "aku suka mendengarkan teman namun tidak banyak berbicara",
    "aku suka makanan pedas dan menonton film",
    "aku belum tahu alasan yang tepat untuk jawaban ini",
    "pilihanku sangat bergantung pada situasi yang belum kuceritakan",
    "tidak ada alasan khusus yang bisa kujelaskan",
    "aku sekadar mengikuti pilihan yang menurutku pas",
    "aku sering memakai baju berwarna gelap",
    "kemarin aku pergi ke toko membeli roti",
    "aku belum pernah mengalami situasi seperti yang ditanyakan",
    "hobi saya bermain game dan memelihara kucing",
]
CONTEXTS = ["ketika mengerjakan tugas", "dalam kegiatan sehari hari", "saat kuliah",
            "ketika bekerja bersama teman", "dalam kegiatan komunitas", "saat menghadapi persoalan baru"]
SPEAKERS = ["aku", "saya", "biasanya aku", "dalam keseharian saya", "kalau ditanya aku"]
STANCE_FRAMES = {
    "support": "{speaker} cenderung {stem} {context}.",
    "oppose": "{speaker} tidak terbiasa {stem} {context}. Itu bukan cara yang biasanya kupakai.",
    "mixed": "{speaker} kadang {stem} {context}, tetapi kadang tidak. Itu bergantung pada keadaan.",
}


def split_for(family_index):
    return "train" if family_index < 8 else "validation" if family_index < 10 else "test"


def build_rows(seed=SEED):
    rows = []
    for function, stems in STEMS.items():
        for family, stem in enumerate(stems):
            for stance, frame in STANCE_FRAMES.items():
                for speaker in SPEAKERS:
                    for context in CONTEXTS:
                        rows.append({"sample_id": f"SYN{len(rows)+1:05}", "text": frame.format(speaker=speaker, stem=stem, context=context),
                                     "function": function, "stance": stance, "label": f"{function}:{stance}",
                                     "family_id": f"{function}-{family:02}", "split": split_for(family),
                                     "source": "synthetic", "generator_version": VERSION})
    for family, sentence in enumerate(UNCLEAR):
        for context in CONTEXTS:
            for ending in ("", " Itu saja yang bisa kuceritakan.", " Begitu yang kurasakan.", " Sulit menjelaskan lebih jauh.", " Tidak ada konteks tambahan."):
                rows.append({"sample_id": f"SYN{len(rows)+1:05}", "text": f"{sentence} {context}.{ending}",
                             "function": "unknown", "stance": "unknown", "label": "unknown",
                             "family_id": f"unknown-{family:02}", "split": split_for(family),
                             "source": "synthetic", "generator_version": VERSION})
    random.Random(seed).shuffle(rows)
    return rows


def validate_rows(rows):
    if len({r["text"].casefold() for r in rows}) != len(rows):
        raise ValueError("Duplicate text found")
    groups = {s: {r["family_id"] for r in rows if r["split"] == s} for s in ("train", "validation", "test")}
    if any(groups[a] & groups[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise ValueError("Semantic-family leakage")
    return {"rows": len(rows), "unique_texts": len(rows), "split_counts": dict(Counter(r["split"] for r in rows)),
            "label_counts": dict(sorted(Counter(r["label"] for r in rows).items())),
            "semantic_family_overlap": 0, "real_respondents": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=BASE / "data" / "cognitive_reasons.csv")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    rows = build_rows(args.seed)
    metadata = validate_rows(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata.update({"version": VERSION, "seed": args.seed,
                     "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                     "warning": "Synthetic language simulation. Not human MBTI validation or cognitive-function ground truth."})
    args.output.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
