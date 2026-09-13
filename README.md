# InnerSelf Cognitive

Web refleksi dengan 32 pertanyaan **fungsi kognitif**, klasifikasi alasan menggunakan model ML lokal, dan penjelasan yang merujuk jawaban pengguna. Tidak menggunakan Gemini atau API AI eksternal.

**Status: prototipe penelitian berbasis data sintetis.** Belum ada validasi pada responden nyata. Ini bukan tes MBTI resmi, diagnosis, atau pengukuran kemampuan otak. Skor dan susunan fungsi adalah hipotesis eksploratif, bukan kepastian kepribadian.

## Yang langsung berjalan

- Delapan fungsi dinilai langsung: Te, Ti, Fe, Fi, Ne, Ni, Se, Si.
- Kandidat tipe ditentukan dari kecocokan pola delapan fungsi dengan 16 susunan, misalnya **Te–Ni–Se–Fi → ENTJ**. Bukan dari skor E/I, S/N, T/F, atau J/P.
- Netral menggunakan kategori `neutral`, dengan **−1 dan +1 disimpan terpisah**. Tidak diperlakukan sebagai angka nol.
- Model klasifikasi teks hasil training sudah disertakan dalam `models/cognitive_text.json.gz`. Tidak perlu training tiap pengguna selesai tes.
- Ulasan lokal membahas pilihan, kutipan asli, nomor soal, nuansa, dan keterbatasan bukti. Dua orang dengan tipe sama dapat mendapat ulasan berbeda.
- Panjang ulasan mengikuti jumlah soal yang diberi alasan: setiap alasan dibahas, termasuk alasan pada soal terakhir. Halaman hasil menampilkan seluruh ulasan.
- Nama panggilan, usia, dan gender dapat diisi sebelum melihat hasil. Pengantar menyebut profil yang diisi dan melanjutkan pembahasan berdasarkan jawaban.
- Mode generatif lokal tersedia untuk narasi lebih luwes, tetapi **memerlukan pemasangan model bahasa terpisah**. Jangan mengira mode standar adalah LLM.

## Menjalankan di VS Code / PowerShell

Buka folder MBTI yang sudah di-clone. Jika server sedang berjalan, **tekan tombol Ctrl dan C bersamaan**, jangan mengetik `Ctrl+C` sebagai perintah.

```powershell
git pull origin main
python -m pip install -r requirements.txt
python main.py
```

Buka **http://localhost:8000**. Cek status komponen di **http://localhost:8000/health**.

Jika `git pull` melaporkan konflik perubahan lokal, hentikan pembaruan dan simpan perubahanmu terlebih dahulu. Jangan memakai `git restore` secara membabi buta. Hasil dan draft versi lama tidak dikonversi ke sistem baru; isi tes fungsi kognitif dari awal.

Python 3.10+ diperlukan; 3.11 disarankan. Instalasi bersih opsional tanpa mengubah kebijakan PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Jika memakai virtual environment, gunakan executable `.\.venv\Scripts\python.exe` juga untuk perintah lain di panduan ini.

### Ngrok

Web tetap bisa dibagikan lewat ngrok. Di terminal lain, jika `ngrok.exe` ada di folder proyek:

```powershell
.\ngrok.exe http 8000
```

Server Python dan ngrok harus tetap menyala. Ngrok hanya meneruskan akses ke server; bukan layanan AI. Alasan diproses di komputer/server yang menjalankan Python, bukan di browser pengunjung. Saat dibagikan secara publik, pertimbangkan pembatasan akses dan kapasitas CPU/RAM; aplikasi ini belum dilengkapi autentikasi atau pembatasan laju untuk produksi.

## Narasi lebih luwes tanpa API: model bahasa lokal

Mode standar memakai model klasifikasi + penyusun kalimat berbasis bukti. Untuk menghasilkan kalimat baru, pasang **Qwen3 4B Q4_K_M** dengan `llama-cpp-python`. Inferensi berjalan langsung di proses Python, bukan lewat server API Ollama/Gemini.

Qwen adalah model pralatih dari tim Qwen, **bukan model bahasa yang dilatih dari nol oleh proyek ini**. Dataset buatan proyek melatih pengenal fungsi dalam teks, bukan kemampuan menulis Qwen. Narasi model lokal tetap dapat salah dan tidak dijamin setara model cloud yang lebih besar.

1. Pasang runtime lokal. Pilihan wheel CPU berikut berasal dari dokumentasi resmi runtime:

   ```powershell
   python -m pip install -r requirements-local-llm.txt --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
   ```

   Jika wheel tidak tersedia untuk versi Python/Windows-mu, instalasi dari sumber membutuhkan compiler C/C++ (misalnya Visual Studio Build Tools). Itu kebutuhan opsional; mode standar tetap bekerja tanpa runtime ini.

2. Unduh model resmi **sekitar 2,5 GB**, satu kali:

   ```powershell
   python setup_local_ai.py --download
   ```

   Skrip memeriksa SHA-256 dan tidak menimpa file berbeda yang sudah ada. Internet hanya dipakai untuk unduhan ini, bukan saat menganalisis jawaban. Model berlisensi Apache-2.0 dan tidak dimasukkan ke Git. Unduhan model besar belum dijalankan di lingkungan pengembangan ini.

3. Buat `.env` jika belum ada, atau **edit file `.env` yang sudah ada**, lalu masukkan:

   ```dotenv
   PORT=8000
   LOCAL_LLM_PATH=models/downloads/Qwen3-4B-Q4_K_M.gguf
   LOCAL_LLM_THREADS=4
   LOCAL_LLM_GPU_LAYERS=0
   ```

   Jangan menimpa `.env` yang berisi konfigurasi lain. Variabel Gemini lama tidak lagi dibaca dan boleh dihapus dari konfigurasi lokalmu. `.env.example` hanya contoh.

4. Jalankan ulang `python main.py`. Di halaman tinjauan, aktifkan **Narasi generatif lokal**.

   `/health` menampilkan `narrator: configured` bila file dan runtime terdeteksi; ini belum membuktikan model berhasil dimuat. Setelah tes, status `reflection.local_llm_status: available` menunjukkan narasi berhasil dibuat dan lolos pemeriksaan struktur/bukti.

Model bahasa membutuhkan RAM lebih besar daripada ukuran file, dan dapat lambat pada CPU laptop. Sediakan ruang untuk model, cache konteks, dan aplikasi lain. Mulai dengan CPU (`0`); offload GPU memerlukan build CUDA yang cocok. Tidak ada klaim kecepatan atau penggunaan RAM yang telah diukur pada laptop pengguna.

### Sapaan personal

Setelah 32 soal selesai, bagian **Personalisasi penjelasan** langsung terbuka sebelum tombol **Lihat hasilku**. Nama panggilan (maksimal 60 karakter), usia (bilangan bulat 13–100 tahun), dan gender masing-masing opsional. Data yang dikosongkan tidak ditebak. Pilihan gender mencakup perempuan, laki-laki, nonbiner, atau tidak ingin menyebutkan.

Contoh untuk nama Andi, usia 17, gender laki-laki, dan lima alasan tertulis:

> Halo Andi, aku asisten AI lokal yang akan menemanimu memahami hasil tes ini. Kamu memperkenalkan diri sebagai laki-laki berusia 17 tahun. Terima kasih sudah membagikan alasan pada 5 soal. Aku akan membacanya bersama pilihanmu untuk melihat pola yang muncul dan konteks di baliknya.

Profil digunakan untuk pengantar personal; skor fungsi dan kandidat tipe dihitung dari pilihan dan alasan. Pengamatan tentang pola pikir tetap merujuk isi jawaban, tanpa menyimpulkan kecerdasan atau kedewasaan dari usia/gender. Pengantar yang sama dipertahankan pada mode standar, Qwen, dan saat generasi Qwen hanya berhasil sebagian. Hasil menyertakan `user_name`, `user_age`, dan `user_gender`; pengantar disusun dari profil yang sudah divalidasi server.

### Panjang ulasan mengikuti jumlah alasan

| Alasan yang diisi | Isi penjelasan utama |
| --- | --- |
| Tidak ada | Ringkasan pola pilihan, tanpa menebak motivasi |
| 4–5 soal | Pembahasan 4–5 alasan, disertai ringkasan hasil |
| 16 soal | Pembahasan seluruh 16 alasan dan pola berulang yang dikenali |
| Hampir semua / 32 soal | Ulasan lebih panjang yang membahas setiap alasan dan menghubungkan pola berulang yang dikenali |

Tidak ada target panjang yang dicapai dengan menambahkan kalimat pengisi. Setiap pembahasan merujuk nomor soal dan alasan terkait. Jumlah kata juga bergantung pada isi alasan; teks kosong atau hanya spasi tidak dihitung. Alasan yang belum dikenali tetap dibahas dengan batas bukti yang jelas. Mode standar menyusun kalimat berbasis bukti, sedangkan Qwen menghasilkan kalimat baru. Perubahan panjang narasi ini **tidak membutuhkan training ulang**.

Narasi generatif memproses seluruh alasan dalam kelompok kecil, maksimal dua alasan per pemanggilan, dengan target satu paragraf 60–120 kata per alasan. Ini menjaga konteks model tetap kecil tanpa membatasi ulasan pada empat alasan pertama. Anggaran penghentian generasi adalah 60 detik per kelompok dan 120 detik bersama untuk satu hasil; waktu muat model / evaluasi satu langkah dapat membuat waktu nyata lebih lama. Hanya satu proses generatif dijalankan sekaligus; permintaan lain mendapat penjelasan standar.

Jika sebagian kelompok gagal, waktunya habis, atau kutipan/nomor soal yang keliru terdeteksi, pembahasan standar untuk alasan itu tetap ditampilkan. Hasil yang sudah berhasil dipertahankan, bersama kesimpulan, catatan kandidat berdekatan, dan pola lintas soal. Status `partial` / mode `local_llm_mixed` berarti narasi gabungan; `generated_reason_count` menunjukkan jumlah alasan yang diulas model bahasa, sedangkan `discussed_reason_count` menghitung semua alasan yang dibahas. Jika tidak ada kelompok yang berhasil, seluruh narasi tetap berbasis bukti. Pemeriksaan struktur dan kutipan tidak menjamin setiap tafsir semantik benar.

## Metode scoring yang dapat ditinjau

### Pertanyaan

Ada empat pernyataan buatan proyek per fungsi: dua searah dan dua berbalik. Kata-katanya bukan salinan instrumen MBTI resmi. Pemetaan dan arah tersimpan di `questions.py`; browser tidak menentukan bobot atau fungsi soal.

### Netral bukan nol

| Pilihan | Kontribusi pada pernyataan searah |
| --- | --- |
| Sangat tidak setuju | −3 |
| Tidak setuju | −2 |
| Agak tidak setuju | −1 |
| Netral / kadang iya kadang tidak | −1 pada sisi penolakan **dan** +1 pada sisi dukungan |
| Agak setuju | +1 |
| Setuju | +2 |
| Sangat setuju | +3 |

Untuk soal berbalik, tanda pilihan nonnetral dibalik. Netral tetap memiliki kedua kontribusi. Sisi dukungan `P` dan besarnya sisi penolakan `N` disimpan terpisah:

`indeks_pilihan = 100 × P / (P + N)`

Contoh empat jawaban netral untuk Te: `P=4`, `N=4`, indeks `50`, dan empat catatan netral. Bukti situasionalnya tetap ada; bukan `0+0`. Karena kedua sisi sama, netral sendiri tidak membuktikan kecenderungan satu arah. Ini memang penanganan desain aplikasi, bukan rumus psikometri resmi.

Menolak Te **tidak otomatis** menambah Ti atau Fi. Fungsi lain diukur oleh soal dan alasan masing-masing.

### Alasan ikut memengaruhi penilaian

Model menebak satu fungsi yang diekspresikan dalam alasan dan sikap `support`, `oppose`, atau `mixed`. Ada kelas `unknown`. Ini bukan pembacaan kepribadian sempurna, dan satu alasan tidak otomatis mengungkap susunan empat fungsi.

Alasan diterima hanya jika melewati batas skor kelas dan pemeriksaan bahasa konservatif. Bobotnya maksimal `1.5 × skor_kelas` per alasan berbeda. Dukungan ditambahkan ke `text_support`, penolakan ke `text_opposition`; `mixed` mengisi kedua sisi. Teks yang sama setelah normalisasi spasi/huruf besar hanya dihitung satu kali.

`indeks_gabungan = 100 × (P + text_support) / (P + N + text_support + text_opposition)`

Nilai softmax model adalah skor keyakinan klasifikasi sintetis, **bukan peluang bahwa pengguna benar-benar memiliki fungsi tersebut**. Bobot 1,5 adalah parameter desain konservatif, belum dioptimasi terhadap label responden nyata.

### Dari fungsi ke tipe

`cognitive.py` mendefinisikan 16 susunan dan profil pembanding dengan level `0.90, 0.75, 0.45, 0.20` pada empat posisi, serta `0.30` pada fungsi lainnya. Semua itu asumsi heuristik, bukan norma populasi.

Pola delapan indeks dipusatkan pada rata-ratanya, lalu dibandingkan dengan profil pembanding melalui cosine similarity. Yang dibandingkan adalah **bentuk relatif pola**, bukan sekadar empat skor tertinggi. Skor kecocokan ditampilkan pada skala 0–100 dan tidak dianggap probabilitas. Hasil seri atau hampir datar mengembalikan `final_result: null`; kandidat berdekatan diberi status `tentative`.

## Dataset dan training

`data/cognitive_reasons.csv` berisi **25.000 kalimat sintetis unik**: 9.000 dari generator v1 ditambah 16.000 dari unggahan `cognitive_reasons_v2.csv`. Targetnya label pola bahasa fungsi/sikap, bukan label MBTI seorang responden. Setiap satu dari 25 label memiliki 1.000 contoh. Tidak ada responden nyata dalam dataset ini.

| Kolom | Makna |
| --- | --- |
| `sample_id` | ID sampel dengan awalan versi agar ID v1/v2 tidak bertabrakan |
| `text` | Contoh alasan dalam bahasa Indonesia |
| `function`, `stance` | Hipotesis label fungsi dan sikap |
| `label` | 24 gabungan fungsi/sikap + kelas unknown |
| `family_id` | Keluarga makna yang diselaraskan lintas versi |
| `split` | train / validation / test |
| `source` | Selalu synthetic |
| `generator_version` | Versi generator |
| `source_sample_id`, `source_family_id`, `source_split` | Identitas dan pembagian asli sebelum penggabungan |

File v2 asli disimpan tanpa perubahan di `data/sources/cognitive_reasons_v2.csv`. Saat diimpor, 640 label `unknown:unknown` diseragamkan menjadi `unknown`. Semua 138 keluarga v2 awalnya tersebar di beberapa split. Selain itu, nomor keluarga v2 tidak selalu memiliki makna yang sama dengan nomor v1; misalnya `Ne-07` v2 merupakan parafrasa keluarga `Ne-10` v1.

`merge_datasets.py` memetakan keluarga tersebut secara eksplisit sebelum training dan mempertahankan pembagian asli v1. Pengelompokan ini merupakan penilaian konservatif penulis, bukan anotasi ahli atau jaminan tidak ada kemiripan semantik lain. File v2 yang berubah ditolak berdasarkan SHA-256 sampai pemetaannya ditinjau lagi. Jangan hanya menambahkan awalan versi pada keluarga lalu mengacak baris, karena parafrasa lintas versi bisa masuk ke data uji dan latihan sekaligus.

Pembagian gabungan adalah **16.944 training, 4.268 validasi, dan 3.788 test**. Tidak ada duplikat setelah normalisasi Unicode/huruf/spasi, serta tidak ada ID keluarga hasil pemetaan yang melintasi split. Semua split mengandung 25 label; proporsinya tidak harus sama karena keluarga dijaga tetap utuh. Metadata mencatat asal data, pemetaan, jumlah perbaikan, seed, dan hash. **Variasi template bukan observasi manusia independen.**

Model hasil training sudah disertakan, sehingga pengguna web cukup menjalankan aplikasi. Untuk membangun ulang dataset gabungan dan model:

```powershell
python -m pip install -r requirements-training.txt
python merge_datasets.py
python train_model.py
```

`python generate_dataset.py` hanya menghasilkan v1 di `data/cognitive_reasons_v1.csv`; sekarang perintah ini tidak menimpa dataset gabungan aktif. Generator v1 tetap dipakai langsung oleh proses penggabungan. `dataset_utils.py` menolak label yang tidak konsisten, kolom wajib kosong, sumber bukan sintetis, ID/teks duplikat, keluarga lintas-split, dan kelas yang hilang dari suatu split.

Untuk membandingkan dengan model sebelumnya pada baris test yang persis sama, sebelum menimpanya:

```powershell
python train_model.py --baseline-model models/cognitive_text.json.gz
```

Model pembanding dibaca sebelum file output diperbarui. Setelah pembaruan ini, perintah tersebut membandingkan dengan model yang saat itu ada di komputermu, bukan otomatis mengambil versi lama dari Git.

Training memakai TF-IDF kata dan subkata + Logistic Regression. TF-IDF hanya di-fit pada training. `C` dan ambang penolakan dipilih dari validasi, bukan dari test. Kolom ID, fungsi, label, keluarga, serta split tidak dimasukkan sebagai fitur. Model diekspor sebagai koefisien JSON terkompresi yang dapat dijalankan tanpa scikit-learn/pickle pada server web.

`models/evaluation.json` menyimpan hasil validasi, matriks kebingungan, macro-F1, cakupan prediksi diterima, dan akurasi di antara prediksi diterima. Baca **cakupan dan kegagalan**, bukan hanya satu angka akurasi. Hasil-hasil ini menguji bahasa sintetis; **jangan dilaporkan sebagai akurasi penentuan MBTI manusia**. Dataset/pipeline ini dikembangkan secara iteratif; untuk skripsi, gunakan data uji manusia baru yang dikunci sebelum pemilihan model.

Hasil training gabungan pada lingkungan pengembangan:

| Ukuran pada test sintetis | Hasil |
| --- | --- |
| Ketepatan klasifikasi fungsi/sikap, seluruh 3.788 baris | 74,68% |
| Macro-F1 seluruh label | 0,7196 |
| Proporsi baris yang diterima oleh jalur inferensi aplikasi | 15,44% |
| Ketepatan pada bagian yang diterima saja | 97,44% |

Angka 97,44% **bukan akurasi seluruh data**: model menahan prediksi pada 84,56% kalimat uji. Pada test yang sama, model sebelumnya mencapai ketepatan keseluruhan 68,82%, menerima 33,74% kalimat, dan benar pada 81,85% dari kalimat yang diterimanya. Model baru lebih selektif; penambahan data tidak menjamin lebih banyak alasan akan dikenali. Pada 1.500 test v1, ketepatan keseluruhan naik 88% → 93%, tetapi cakupan turun 19,73% → 6,67%. Pada 2.288 test v2, ketepatan naik 56,25% → 62,67%, dan cakupan turun 42,92% → 21,20%. Model tetap dapat menghasilkan catatan bahwa alasan belum cukup jelas. Jangan menurunkan ambang hanya untuk menghilangkan catatan itu.

`/health` kini menyertakan `classifier_training`: `dataset_rows` menunjukkan total korpus (25.000), `training_rows` menunjukkan yang benar-benar dipakai untuk fitting (16.944), disertai jumlah per versi/split dan hash dataset. Restart server setelah mengganti model karena classifier disimpan dalam cache proses. Training ini memperbarui pengenal fungsi/sikap, **tidak melakukan fine-tuning Qwen**.

Dataset lama berlabel tipe MBTI serta loader/Gemini lama tetap tidak digunakan sebagai ground truth. Yang digabungkan di sini adalah korpus alasan fungsi/sikap v1 dan v2 yang skemanya kompatibel; label tipe 16 MBTI tidak diubah begitu saja menjadi label fungsi sebuah kalimat. Versi lama masih tersedia di riwayat Git.

Untuk penelitian nyata, kumpulkan alasan dengan persetujuan responden, rancang label fungsi/tipe referensi bersama pembimbing/ahli, pisahkan berdasarkan responden, dan evaluasi reliabilitas anotasi. Jangan menjadikan hasil model ini sendiri sebagai label benar untuk training berikutnya.

## Pengujian

```powershell
python -m pip install -r tests/requirements.txt
python -m unittest discover -s tests -v
```

Pengujian interaksi antarmuka melalui DOM (Node.js):

```powershell
npm install --prefix tests/ui
npm test --prefix tests/ui
```

Set variabel `PYTHON` jika executable Python yang dipakai pengujian UI berbeda. Uji mencakup 16 susunan, netral, soal berbalik, bukti teks, serialisasi model, input tidak valid, keamanan kutipan, versi hasil, alur 32 soal, penyimpanan tab, serta kegagalan komponen opsional. Adapter generatif diuji menggunakan model tiruan; kualitas narasi GGUF yang sesungguhnya belum diuji. Pemeriksaan browser visual belum dilakukan karena unduhan browser pengujian gagal di lingkungan ini.

## Privasi dan batasan

- Jawaban tidak disimpan ke database server atau dipakai training otomatis. Browser menyimpan draft/hasil di `sessionStorage` tab aktif. Jangan menulis informasi pribadi sensitif.
- Tidak ada permintaan jaringan dari jalur inferensi lokal. Unduhan dependensi/model saat setup adalah aktivitas terpisah.
- Profil opsional dipakai untuk sapaan dan disimpan bersama draft/hasil di tab aktif. Profil tidak memengaruhi skor, tidak dikirim ke model generatif, dan tidak ikut dalam ringkasan tombol bagikan hasil.
- Teks pengguna/model ditampilkan sebagai teks, bukan HTML. File `.env`, sumber, dataset, dan model tidak disajikan sebagai aset web.
- Token fungsi seperti Si/Ti dan interpretasinya adalah konstruksi tipologi. Kalimat “suka berkumpul tetapi jarang bicara” tidak otomatis diartikan sebagai Si. Ketidakjelasan dan penolakan diperlakukan hati-hati.
- Bahasa generatif yang terdengar meyakinkan tidak membuktikan ketepatan klasifikasi. Jangan gunakan hasil untuk diagnosis, seleksi kerja, atau keputusan berisiko tinggi.

## Referensi teknis dan atribusi

- [Myers & Briggs Foundation — Type dynamics and processes](https://www.myersbriggs.org/unique-features-of-myers-briggs/type-dynamics-processes/): referensi konsep, bukan validasi tes/profil pembanding buatan proyek.
- [scikit-learn — Text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction).
- [scikit-learn — Pencegahan data leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
- [scikit-learn — Validasi dengan kelompok data terkait](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).
- [llama-cpp-python — installation and structured chat](https://llama-cpp-python.readthedocs.io/en/latest/).
- [Qwen3 4B GGUF — sumber model dan lisensi Apache-2.0](https://huggingface.co/Qwen/Qwen3-4B-GGUF).
- Ikon Lucide lokal: `static/vendor/LUCIDE-LICENSE.txt`. Tidak memerlukan CDN atau aset berbayar.
