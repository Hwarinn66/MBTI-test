# InnerSelf Discovery

Tes refleksi kepribadian berbahasa Indonesia dengan FastAPI, 32 pertanyaan, dan halaman hasil responsif. Antarmuka memakai HTML/CSS/JavaScript biasa, ikon Lucide lokal, dan animasi CSS yang mengikuti preferensi reduced motion. Tidak ada proses build JavaScript atau ketergantungan CDN.

## Menjalankan

Gunakan Python 3.10 atau lebih baru.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Buka http://localhost:8000. Halaman utama juga tersedia di `/index.html`, hasil di `/result.html`. Untuk menjalankan dari direktori lain, gunakan path lengkap ke `main.py`. `PORT` dapat diubah melalui environment proses (default 8000).

`requierements.txt` dipertahankan sebagai alias untuk instruksi instalasi lama.

## Ulasan AI opsional

Tes dasar berjalan tanpa API key, tanpa memuat dataset, dan tanpa menghubungi layanan luar. Untuk mengaktifkan ulasan Gemini, salin `.env.example` menjadi `.env` dan isi `GEMINI_API_KEY` dengan key baru. `GOOGLE_API_KEY` juga didukung. `GEMINI_MODEL` dapat diubah sesuai model yang tersedia di akunmu; default mempertahankan `gemini-2.5-flash`.

Pengguna memilih sendiri opsi ulasan AI sebelum mengirim. Hanya pada saat itu jawaban dan profil opsional diteruskan ke Gemini. Panggilan memiliki timeout dan tidak mencoba ulang otomatis. Jika key belum ada, respons AI tidak valid, kuota habis, atau layanan gagal, hasil dasar tetap dikembalikan dengan status yang jelas.

Key yang pernah terunggah ke repositori harus dicabut/diganti melalui akun penyedianya. Menghapus `.env` dan key dari kode terbaru tidak menghapusnya dari riwayat Git. Jangan commit key baru. Cache Python yang sebelumnya ikut terunggah juga dikeluarkan dari versi baru.

## Perhitungan hasil

- `questions.py` adalah satu sumber pertanyaan, dimensi, arah skor, dan versi kuesioner. Setiap dimensi memiliki delapan pertanyaan dengan arah persetujuan yang berimbang.
- Browser hanya mengirim ID, skor persetujuan -3 hingga +3, dan alasan opsional. Server memvalidasi versi, jumlah, keunikan ID, rentang skor, dan usia bila diberikan. Dimensi atau arah skor buatan klien tidak dipercaya.
- Jawaban netral memberi 0,5 ke masing-masing sisi. Skor seri ditandai `X`; seluruh jawaban netral menghasilkan `XXXX`, bukan tipe tertentu.
- Persentase adalah proporsi skor, bukan akurasi. Nilai kejelasan preferensi juga merupakan ukuran jarak skor dari titik tengah, bukan probabilitas.
- Skor fungsi kognitif adalah ilustrasi berdasarkan tipe dan dimensi, bukan pengukuran kemampuan. Diagram fungsi dan daftar tokoh tidak dipaksakan bila tipe masih mengandung `X`.
- AI memberikan interpretasi, tanpa mengganti hasil skor. Ini memperbaiki perilaku lama yang menimpa tipe berdasarkan kemiripan heuristik dan dapat memaksakan hasil pada jawaban seimbang.
- Kemiripan dataset memakai TF-IDF dengan sampel deterministik dan tanpa penambahan skor minimum buatan. Tidak ada klaim jumlah profil yang di-hardcode, probabilitas, atau diagnosis. Referensi tokoh dari koleksi yang sudah ada ditandai sebagai interpretasi, bukan hasil tes terverifikasi.

Tes ini merupakan kuesioner refleksi buatan situs, bukan instrumen psikometrik tervalidasi atau tes MBTI resmi. Pertanyaan baru perlu ditinjau pengelola bila ingin digunakan sebagai instrumen penelitian.

## Perilaku antarmuka

Jawaban dan hasil baru disimpan di `sessionStorage` pada tab yang sama. Alasan tersimpan ketika berpindah pertanyaan atau memuat ulang halaman. Tombol mulai ulang meminta konfirmasi dan hanya menghapus data aplikasi ini. Bila penyimpanan diblokir, tes tetap berjalan selama halaman terbuka dan hasil ditampilkan di halaman yang sama. Hasil lama dari `localStorage` masih dapat dibaca tanpa menulis data pribadi baru ke sana.

Tidak ada hasil demo yang menggantikan data hilang/rusak. Bagikan hanya menyalin ringkasan tipe, tanpa profil, jawaban, atau ulasan; tersedia fallback bila Web Share/Clipboard tidak tersedia. Foto tokoh yang belum tersedia ditampilkan sebagai inisial, tanpa gambar placeholder eksternal yang rusak. Ulasan AI dan teks pengguna dirender sebagai teks, bukan HTML.

## Pengujian

```bash
python -m pip install httpx
python -m unittest discover -s tests -v
```

Tes regresi mencakup keenam belas tipe, pembalikan arah soal, skor seri, validasi, rute/aset, path absolut, fallback AI, dan keamanan respons. Panggilan AI dimock; tidak menggunakan key asli atau kuota Gemini.

Validasi interaksi DOM juga dilakukan untuk alur 32 pertanyaan, alasan, navigasi kembali, pemulihan penyimpanan, gagal kirim dan coba ulang, tampilan hasil, filter tokoh, serta fallback berbagi. Pemeriksaan ini bukan pengujian visual di browser atau uji terhadap layanan Gemini langsung.

## Aset

Ikon berasal dari [Lucide](https://lucide.dev), paket versi 1.8.0, dan disertakan sebagai subset SVG di `static/icons.svg`. Lisensi lengkap ada di `static/vendor/LUCIDE-LICENSE.txt`. Animasi transisi dan indikator proses dibuat dengan CSS lokal. Tidak diperlukan registrasi atau biaya untuk aset ini.
