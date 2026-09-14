import csv, json, random, re, hashlib
from collections import Counter
from pathlib import Path

OUT=Path('/mnt/data'); CSV_PATH=OUT/'cognitive_reasons_v3_100k.csv'; META_PATH=OUT/'cognitive_reasons_v3_100k.metadata.json'
SEED=20260914; VERSION='synthetic-natural-id-v3-100k'

CONCEPTS={
'Te':[
('membuat daftar langkah sebelum mulai','urutan kerja jadi jelas dan aku tahu apa yang harus diselesaikan dulu'),
('menentukan prioritas dari yang paling penting','waktu dan tenaga tidak habis di hal yang dampaknya kecil'),
('memecah target besar menjadi tugas kecil','progres lebih mudah dipantau dan pekerjaan terasa lebih terarah'),
('memasang tenggat untuk tiap tahap','pekerjaan tidak molor dan hasil bisa selesai sesuai target'),
('mengukur progres dengan angka atau hasil nyata','aku bisa melihat apakah cara yang dipakai benar-benar efektif'),
('memilih metode yang paling efisien','aku ingin mendapat hasil bagus tanpa membuang waktu dan sumber daya'),
('membagi peran saat kerja kelompok','semua orang tahu tanggung jawabnya dan pekerjaan tidak tumpang tindih'),
('membuat alur kerja yang rapi dan konsisten','prosesnya lebih gampang diulang dan kesalahan bisa dikurangi'),
('membandingkan hasil beberapa cara','aku ingin memilih cara yang terbukti memberi hasil paling baik'),
('mengatur waktu alat dan sumber daya dari awal','pelaksanaannya lebih lancar dan tujuan lebih cepat tercapai')],
'Ti':[
('mencari tahu cara kerja sesuatu sampai masuk akal','aku sulit puas kalau cuma tahu hasil tanpa memahami logikanya'),
('memeriksa apakah penjelasan saling konsisten','aku ingin memastikan tidak ada bagian yang bertentangan'),
('memperjelas arti istilah yang dipakai','kesimpulan bisa kacau kalau definisinya sejak awal sudah tidak jelas'),
('memecah masalah rumit menjadi bagian kecil','aku lebih mudah melihat hubungan logis antarbagian'),
('mencari celah atau kontradiksi dalam argumen','aku ingin tahu apakah kesimpulannya benar-benar tahan diuji'),
('menelusuri penyebab masalah satu per satu','aku ingin menemukan sumber masalah bukan sekadar menutup gejalanya'),
('menilai ide dari prinsipnya bukan dari siapa yang bilang','yang penting buatku adalah apakah alasannya masuk akal'),
('membangun gambaran logis di kepala sebelum setuju','aku perlu kerangka yang konsisten sebelum menerima suatu klaim'),
('menguji kasus pengecualian dari sebuah aturan','pengecualian sering menunjukkan apakah aturan itu benar-benar kuat'),
('memeriksa asumsi yang dianggap orang lain sudah pasti','aku tidak suka menerima sesuatu hanya karena semua orang menganggapnya benar')],
'Fe':[
('memperhatikan suasana kelompok sebelum bicara','cara penyampaian yang tepat bisa membuat orang lebih nyaman menerima pesan'),
('menyesuaikan nada bicara dengan lawan bicara','aku ingin orang lain merasa dihargai dan tidak diserang'),
('mencari titik temu saat pendapat berbeda','hubungan tetap bisa berjalan meski semua orang tidak sepakat penuh'),
('memperhatikan siapa yang terlihat tidak nyaman','aku tidak ingin ada orang yang merasa diabaikan dalam situasi bersama'),
('menjaga agar suasana kelompok tetap enak','kerja sama biasanya lebih mudah ketika orang merasa aman dan diterima'),
('mengajak anggota yang pendiam ikut terlibat','aku ingin semua orang punya ruang untuk menyampaikan dirinya'),
('memikirkan kebutuhan bersama sebelum memutuskan','keputusan kelompok sebaiknya tidak hanya menguntungkan satu orang'),
('membantu menenangkan konflik antarorang','aku lebih suka membuat komunikasi kembali terbuka daripada membiarkan ketegangan'),
('menunjukkan dukungan saat orang lain sedang kesulitan','respons emosional yang tepat bisa membuat orang merasa tidak sendirian'),
('menyesuaikan cara menyampaikan kritik','pesan yang sama bisa diterima lebih baik kalau disampaikan dengan mempertimbangkan perasaan orang')],
'Fi':[
('memilih berdasarkan nilai yang benar-benar aku pegang','aku ingin keputusan tetap terasa selaras dengan prinsip pribadiku'),
('menolak hal yang bertentangan dengan nuraniku','aku sulit menjalankan sesuatu kalau dari dalam terasa salah'),
('memastikan sikapku terasa jujur terhadap diri sendiri','aku tidak nyaman berpura-pura hanya supaya cocok dengan lingkungan'),
('mengambil keputusan dari keyakinan batin','aku lebih percaya pada apa yang benar-benar terasa penting bagiku'),
('menjaga batas pribadi meski orang lain tidak setuju','ada hal yang menurutku tidak boleh dikorbankan hanya demi menyenangkan orang'),
('memikirkan arti personal dari sebuah pilihan','aku perlu tahu kenapa keputusan itu penting buat diriku sendiri'),
('mempertahankan pendirian yang menurutku benar','dukungan orang lain bukan satu-satunya ukuran benar atau salah bagiku'),
('mengakui perasaan sendiri sebelum memutuskan','reaksi batin sering memberi tahu nilai apa yang sebenarnya sedang tersentuh'),
('memilih keaslian daripada sekadar mengikuti kelompok','aku lebih nyaman jadi diriku sendiri daripada meniru sikap yang tidak terasa cocok'),
('menghormati nilai pribadi orang tanpa harus menyamakan semuanya','setiap orang bisa punya batas dan hal penting yang berbeda')],
'Ne':[
('mencari beberapa kemungkinan sebelum memilih','aku suka tahu ada jalan lain kalau pilihan pertama tidak berhasil'),
('menghubungkan ide yang awalnya kelihatan tidak berkaitan','hubungan yang aneh kadang justru memunculkan ide baru'),
("membayangkan skenario gimana kalau dari suatu situasi",'aku tertarik melihat bagaimana hasilnya berubah kalau satu hal dibuat berbeda'),
('mencoba pendekatan baru ketika cara lama terasa buntu','aku cepat terpikir alternatif lain daripada terpaku pada satu metode'),
('melihat lebih dari satu tafsir dari informasi yang sama','satu hal bisa punya banyak kemungkinan makna tergantung sudut pandangnya'),
('melompat dari satu ide ke ide lain saat berpikir','satu gagasan sering memicu beberapa gagasan lain di kepalaku'),
('mendapat ide baru dari hal kecil yang kebetulan kulihat','stimulus sederhana sering membuka kemungkinan yang sebelumnya tidak kepikiran'),
('mengeksplor pilihan yang belum pernah dicoba','aku penasaran dengan kemungkinan yang belum diketahui hasilnya'),
('membayangkan beberapa masa depan yang berbeda','aku lebih nyaman membuka beberapa jalur daripada langsung mengunci satu arah'),
('menambahkan opsi ketika orang lain merasa pilihannya habis','biasanya masih ada cara lain kalau sudut pandangnya digeser')],
'Ni':[
('mencari benang merah dari banyak informasi','aku ingin menemukan pola utama yang menjelaskan semuanya secara lebih utuh'),
('memikirkan arah jangka panjang dari keadaan sekarang','aku lebih tertarik pada ke mana semuanya akan mengarah daripada kejadian sesaat'),
('menyaring banyak petunjuk menjadi satu kesimpulan','terlalu banyak opsi justru kurang membantu kalau tidak ada arah yang paling masuk akal'),
('membayangkan konsekuensi beberapa langkah ke depan','aku ingin melihat jalur yang kemungkinan besar terbentuk dari keputusan sekarang'),
('mencari makna di balik pola yang berulang','kejadian yang tampak terpisah kadang terasa punya tema yang sama'),
('membuat rencana berdasarkan gambaran masa depan','aku lebih mudah menentukan langkah kalau sudah tahu arah besar yang ingin dituju'),
('merenungkan informasi sampai muncul satu pemahaman','aku sering butuh waktu untuk menyatukan banyak petunjuk menjadi wawasan yang utuh'),
('memperkirakan jalur yang paling mungkin terjadi','aku cenderung mencari arah utama daripada terus membuka semua kemungkinan'),
('menghubungkan beberapa kejadian menjadi satu pola besar','aku suka melihat bagaimana bagian-bagian kecil membentuk cerita yang sama'),
('mendalami satu wawasan sampai terasa jelas','aku lebih suka satu arah yang kuat daripada banyak ide yang belum menyatu')],
'Se':[
('langsung mencoba lalu menyesuaikan dari hasilnya','aku lebih cepat paham setelah melihat apa yang benar-benar terjadi'),
('memperhatikan perubahan yang sedang terjadi di sekitar','informasi yang ada di depan mata sering paling berguna untuk menentukan tindakan'),
('belajar lewat praktik langsung','pengalaman nyata lebih cepat membuatku mengerti daripada hanya membaca teori'),
('bereaksi cepat ketika situasi berubah','aku tidak mau terlalu lama menganalisis saat keadaan menuntut respons langsung'),
('fokus pada apa yang bisa dilakukan sekarang','aku lebih mudah bergerak kalau berurusan dengan kondisi yang konkret'),
('berimprovisasi memakai apa yang tersedia','aku bisa menyesuaikan tindakan dengan sumber daya yang benar-benar ada'),
('memeriksa kondisi nyata sebelum membuat asumsi','aku lebih percaya pada apa yang bisa diamati langsung'),
('bertindak dulu lalu memperbaiki sambil jalan','terlalu banyak memikirkan kemungkinan kadang malah membuat momentum hilang'),
('memperhatikan detail fisik yang berubah','perubahan kecil pada lingkungan sering memberi petunjuk tentang tindakan berikutnya'),
('mencari pengalaman langsung sebelum menilai','aku ingin merasakan atau melihat sendiri sebelum membuat kesimpulan')],
'Si':[
('membandingkan keadaan sekarang dengan pengalaman sebelumnya','pengalaman lama membantuku melihat apa yang berubah dan apa yang masih sama'),
('menggunakan cara yang sudah pernah terbukti berhasil','aku lebih tenang kalau ada pengalaman nyata yang bisa dijadikan acuan'),
('mengingat detail kejadian lama saat menghadapi situasi serupa','detail masa lalu sering membantu menghindari kesalahan yang sama'),
('mempertahankan rutinitas yang sudah cocok','cara yang familiar membuatku lebih konsisten dan tidak perlu mengulang adaptasi dari nol'),
('mengecek apakah sesuatu berbeda dari biasanya','aku cukup peka pada perubahan kecil karena ingat pola yang sebelumnya'),
('mengacu pada pengalaman pribadi sebelum menerima cara baru','aku ingin membandingkan hal baru dengan sesuatu yang sudah pernah kualami'),
('mencatat langkah yang berhasil supaya bisa diulang','pengalaman yang terbukti berguna sebaiknya tidak hilang begitu saja'),
('menggunakan contoh konkret dari masa lalu sebagai patokan','aku lebih mudah menilai situasi baru kalau ada pembanding yang sudah dikenal'),
('mengingat urutan kejadian secara detail','detail yang tersimpan membantu memahami kenapa hasil sekarang bisa berbeda'),
('menjaga kestabilan cara yang sudah terasa aman','perubahan tetap bisa dilakukan tapi aku lebih nyaman kalau ada dasar yang sudah dikenal')]
}
CONTEXTS=['saat mengerjakan tugas kuliah','ketika menyusun proyek kelompok','waktu harus mengambil keputusan yang cukup penting','saat menghadapi masalah yang belum pernah kutemui','ketika merencanakan kegiatan beberapa hari ke depan','waktu berdiskusi dengan teman','ketika mempelajari topik baru','saat harus menyelesaikan sesuatu dalam waktu terbatas','ketika mengatur kegiatan sehari-hari','waktu menghadapi perbedaan pendapat dengan orang lain']
CONTRAST={
'Te':'buatku yang penting bukan sekadar terlihat teratur tapi hasilnya memang lebih efektif dan bisa dipantau',
'Ti':'buatku yang penting bukan cepat selesai tapi logikanya benar-benar nyambung dan tidak kontradiktif',
'Fe':'aku bukan cuma ikut orang lain aku memang mempertimbangkan bagaimana keputusan itu memengaruhi suasana dan hubungan',
'Fi':'aku bukan ingin berbeda sendiri aku hanya tidak mau mengorbankan nilai yang menurutku penting',
'Ne':'ini bukan sekadar susah fokus aku memang spontan melihat beberapa kemungkinan atau kaitan lain',
'Ni':'aku bukan menutup semua alternatif aku cuma cenderung menyaringnya sampai menemukan arah yang paling menyatu',
'Se':'aku bukan asal nekat aku lebih mudah menilai setelah melihat kondisi nyata dan merespons langsung',
'Si':'aku bukan anti perubahan aku cuma memakai pengalaman yang sudah terbukti sebagai pembanding sebelum menyesuaikan diri'}
OPPOSE={
'Te':'aku lebih nyaman bergerak fleksibel tanpa terlalu mengatur langkah target atau ukuran hasil dari awal',
'Ti':'aku lebih sering menerima penjelasan yang cukup praktis tanpa perlu membongkar logika dan definisinya sampai sedetail itu',
'Fe':'aku tidak terlalu menyesuaikan keputusan dengan suasana kelompok dan lebih sering memakai pertimbanganku sendiri',
'Fi':'aku cukup mudah mengikuti tuntutan situasi atau kelompok meski pilihan itu tidak selalu mencerminkan nilai pribadiku',
'Ne':'aku lebih nyaman memilih satu cara yang sudah jelas daripada terus membuka kemungkinan dan alternatif baru',
'Ni':'aku jarang mencari satu pola besar atau arah jangka panjang dan lebih fokus pada hal yang langsung terlihat',
'Se':'aku cenderung menahan tindakan sampai sudah memikirkan kemungkinan dan rencana dengan cukup matang',
'Si':'aku tidak terlalu memakai pengalaman lama sebagai patokan dan lebih suka memperlakukan situasi baru sebagai hal yang benar-benar baru'}
MIX={
'Te':'kalau targetnya jelas aku bisa sangat terstruktur tapi kalau situasinya santai aku bisa membiarkan proses berjalan lebih bebas',
'Ti':'kalau topiknya penting aku akan mengulik logikanya tapi untuk hal sederhana aku tidak merasa perlu menganalisis sedalam itu',
'Fe':'kalau menyangkut orang dekat aku sangat mempertimbangkan suasana tapi di situasi lain aku bisa lebih fokus pada pendirianku sendiri',
'Fi':'untuk nilai yang penting aku sangat tegas tapi pada hal kecil aku bisa mengikuti keadaan tanpa merasa prinsipku terganggu',
'Ne':'kalau masalahnya terbuka aku suka mencari banyak opsi tapi kalau sudah ada cara yang jelas aku bisa berhenti mengeksplor kemungkinan lain',
'Ni':'untuk keputusan besar aku mencari arah jangka panjang tapi untuk hal sehari-hari aku tidak selalu memikirkan pola besarnya',
'Se':'kalau situasi menuntut respons cepat aku langsung bergerak tapi kalau risikonya besar aku bisa berhenti dan merencanakan dulu',
'Si':'kalau ada pengalaman yang relevan aku memakainya sebagai acuan tapi kalau situasinya benar-benar baru aku bisa mencoba pendekatan lain'}

REGISTERS=['formal','neutral','slang','chat','mixed']
PRONOUNS={'formal':['saya','saya sendiri','saya pribadi'],'neutral':['aku','aku sendiri','aku pribadi'],'slang':['gue','gua','gw'],'chat':['gw','gue','aku'],'mixed':['aku','gue','saya']}
REPL={
'formal':[('nggak','tidak'),('gak','tidak'),('bikin','membuat'),('pake','menggunakan'),('nyari','mencari'),('mikirin','memikirkan'),('ngerti','memahami'),('ngelist','membuat daftar'),('udah','sudah'),('aja','saja'),('kalo','kalau'),('biar','agar'),('soalnya','karena'),('pas','saat'),('buatku','bagi saya'),('kepikiran','terpikir'),('kelihatan','terlihat'),('nyambung','konsisten')],
'neutral':[('tidak','nggak'),('agar','biar'),('bagi saya','buatku')],
'slang':[('membuat daftar','ngelist'),('tidak','gak'),('sudah','udah'),('saja','aja'),('kalau','kalo'),('ketika','pas'),('saat','pas'),('karena','soalnya'),('agar','biar'),('membuat','bikin'),('menggunakan','pake'),('memikirkan','mikirin'),('mencari','nyari'),('memahami','ngerti'),('memperhatikan','merhatiin'),('menyesuaikan','nyesuaiin'),('membandingkan','bandingin'),('mengingat','inget'),('menentukan','nentuin'),('menyusun','nyusun'),('memilih','milih'),('menjaga','jaga'),('lebih mudah','lebih gampang'),('terlihat','kelihatan'),('terpikir','kepikiran'),('sangat','banget'),('dengan','sama')],
'chat':[('membuat daftar','ngelist'),('tidak','ga'),('nggak','ga'),('sudah','udh'),('kalau','klo'),('karena','krn'),('yang','yg'),('dengan','dgn'),('untuk','utk'),('sebelum','sblm'),('banget','bgt'),('saja','aja'),('ketika','pas'),('saat','pas'),('membuat','bikin'),('menggunakan','pake'),('memikirkan','mikirin'),('mencari','nyari'),('memahami','ngerti'),('memperhatikan','merhatiin'),('menyesuaikan','nyesuaiin'),('membandingkan','bandingin'),('mengingat','inget'),('menentukan','nentuin'),('menyusun','nyusun'),('memilih','milih'),('terlihat','keliatan')],
'mixed':[('membuat daftar','bikin list'),('daftar','list'),('tenggat','deadline'),('hasil','result'),('progres','progress'),('pilihan','option'),('cara','approach'),('pola','pattern'),('suasana','vibe'),('rencana','plan'),('membandingkan','compare'),('memeriksa','check'),('menyesuaikan','adjust'),('mencari','cari'),('membuat','bikin'),('menggunakan','pakai')]
}

def _pat(term):
    # Whole-token / whole-phrase replacement: prevents aja -> s-aja inside "mempelajari".
    return re.compile(r'(?<!\w)'+re.escape(term)+r'(?!\w)', re.I)
PATTERNS={reg:[(_pat(a),b) for a,b in pairs] for reg,pairs in REPL.items()}
AKU_PAT=_pat('aku')

def transform(text, reg, pron):
    text=AKU_PAT.sub(pron,text)
    for pat,b in PATTERNS[reg]: text=pat.sub(b,text)
    return ' '.join(text.split())

def cap(s): return s[:1].upper()+s[1:] if s else s
SUP=['{p} biasanya {a} {c}, karena {r}.','kalau {c}, {p} lebih sering {a}. buatku {r}.','{p} memang cenderung {a} {c}; alasannya {r}.','{cc}, {p} hampir selalu {a}. {rr}.','{p} {a} {c}. bukan sekadar kebiasaan; {x}.','beberapa kali saat {c}, {p} sadar kalau {a} lebih cocok karena {r}.','{p} suka {a} {c} biar {r}.','{p} cenderung {a} {c}. biasanya {r}, jadi cara itu terasa paling natural buatku.']
OPP=['{p} justru jarang {a} {c}; {o}.','kalau {c}, {p} biasanya tidak {a}. {o}.','{p} kurang cocok dengan kebiasaan {a} {c}. {o}.','{cc}, {p} malah menghindari kebiasaan {a}. {oo}.','{p} tidak terlalu suka {a} {c}; buatku cara seperti itu bukan pilihan utama. {o}.','meskipun orang lain sering {a} {c}, {p} biasanya tidak. {o}.','{p} hampir tidak pernah {a} {c}. {o}.','{p} pernah mencoba {a} {c}, tapi akhirnya lebih sering memakai cara lain karena {o}.']
MIXT=['{p} kadang {a} {c}, tapi kadang juga tidak. {m}.','kalau {c}, tergantung kondisinya: sesekali {p} {a}, sesekali tidak. {m}.','{p} tidak selalu {a} {c}. {m}.','{cc}, pola {a} muncul pada situasi tertentu saja. {mm}.','buat {p}, kebiasaan {a} {c} itu sangat situasional. {m}.','{p} bisa {a} {c}, tetapi bukan setiap saat. {m}.','ada kondisi ketika {p} {a} {c}, dan ada juga kondisi ketika pendekatannya kebalikannya. {m}.','{p} cukup fleksibel soal {a} {c}; {m}.']
END=['',' itu yang paling terasa buatku.',' kurang lebih begitu cara pikirku.',' biasanya begitu.',' setidaknya itu yang sering terjadi.']

def render(f,stance,concept,context,reg,style,variant):
    pron=PRONOUNS[reg][variant%3]
    t=(SUP if stance=='support' else OPP if stance=='oppose' else MIXT)[style]
    # Speaker placeholder avoids replacing the "aku" inside an already-expanded pronoun.
    raw=t.format(p='__PRON__',a=concept[0],r=concept[1],c=context,x=CONTRAST[f],o=OPPOSE[f],m=MIX[f],cc=cap(context),rr=cap(concept[1]),oo=cap(OPPOSE[f]),mm=cap(MIX[f]))
    s=transform(raw,reg,pron).replace('__PRON__',pron)
    if variant%5: s=s.rstrip('.')+'.'+END[variant%5]
    return cap(' '.join(s.split()))

rows=[]; seen=set(); n=1; register_counts=Counter()
for f,concepts in CONCEPTS.items():
  for ci,concept in enumerate(concepts):
    for xi,context in enumerate(CONTEXTS):
      fi=ci*10+xi; family=f'v3-{f}-{fi:03d}'; split='train' if fi<70 else 'validation' if fi<85 else 'test'
      for stance in ('support','oppose','mixed'):
        v=0
        for reg in REGISTERS:
          for style in range(8):
            text=render(f,stance,concept,context,reg,style,v); key=' '.join(text.casefold().split())
            if key in seen:
              text=text.rstrip('.')+' Dalam konteks ini pola itu memang yang paling sering terjadi.'; key=' '.join(text.casefold().split())
            if key in seen: raise RuntimeError('duplicate '+text)
            seen.add(key); rows.append({'sample_id':f'V3S{n:06d}','text':text,'function':f,'stance':stance,'label':f'{f}:{stance}','family_id':family,'split':split,'source':'synthetic_natural_variation','generator_version':VERSION}); n+=1; v+=1; register_counts[reg]+=1

UNK_SUBJ=[('makanan',['nasi goreng','mie ayam','sate','bakso','roti','kopi','teh','sambal','martabak','es krim']),('hiburan',['film','anime','musik','game','novel','podcast','komik','drama','video','streaming']),('benda',['tas','sepatu','laptop','ponsel','meja','kursi','botol','jaket','jam','headset']),('tempat',['kampus','rumah','kafe','toko','perpustakaan','halte','taman','mall','kelas','stasiun']),('aktivitas',['tidur','makan','jalan-jalan','nonton','main game','denger musik','belanja','bersih-bersih','mandi','nongkrong']),('cuaca',['hujan','panas','mendung','berangin','cerah','gerimis','dingin','lembap','kering','berawan']),('warna',['hitam','putih','biru','merah','hijau','abu-abu','ungu','cokelat','kuning','oranye']),('waktu',['pagi','siang','sore','malam','Senin','Jumat','akhir pekan','kemarin','besok','minggu lalu']),('jawaban',['setuju','tidak setuju','netral','agak setuju','asal pilih','bingung','belum tahu','terserah','biasa saja','nggak kepikiran']),('profil',['INTP','INFP','ENTP','INTJ','ENFP','ISTJ','ISFP','ENTJ','INFJ','ESTP'])]
UNK_T=['{p} cuma mau bilang aku suka {v}.','sejujurnya {p} lagi kepikiran soal {v}, bukan alasan khusus buat jawaban ini.','{p} pilih jawaban ini karena rasanya biasa aja; kebetulan aku juga suka {v}.','nggak ada alasan tertentu, yang kepikiran sekarang cuma {v}.','{p} belum tahu harus jelasin apa. mungkin {v}, tapi itu nggak ada hubungannya sama pertanyaan.','jawabanku ya begitu aja. {v} juga lagi kepikiran sekarang.','{p} nulis ini cuma supaya kolomnya nggak kosong: {v}.','kalau ditanya alasan, {p} belum punya penjelasan. yang jelas {v}.']
uf=0
for cat,vals in UNK_SUBJ:
  for value in vals:
    family=f'v3-unknown-{uf:03d}'; split='train' if uf<70 else 'validation' if uf<85 else 'test'; vno=0
    for reg in REGISTERS:
      for style in range(8):
        p=PRONOUNS[reg][vno%3]; text=transform(UNK_T[style].format(p=p,v=value),reg,p)
        if vno%5: text=text.rstrip('.')+'.'+['',' itu aja.',' kurang lebih gitu.',' susah jelasin lebih jauh.',' nggak ada konteks lain.'][vno%5]
        text=cap(' '.join(text.split())); key=' '.join(text.casefold().split())
        if key in seen: text=text.rstrip('.')+f' Kategori yang kepikiran: {cat}.'; key=' '.join(text.casefold().split())
        if key in seen: raise RuntimeError('unknown dup '+text)
        seen.add(key); rows.append({'sample_id':f'V3S{n:06d}','text':text,'function':'unknown','stance':'unknown','label':'unknown','family_id':family,'split':split,'source':'synthetic_natural_variation','generator_version':VERSION}); n+=1; vno+=1; register_counts[reg]+=1
    uf+=1
assert len(rows)==100000, len(rows)
rng=random.Random(SEED); rng.shuffle(rows)
fields=['sample_id','text','function','stance','label','family_id','split','source','generator_version']
with CSV_PATH.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
label_counts=Counter(r['label'] for r in rows); split_counts=Counter(r['split'] for r in rows); function_counts=Counter(r['function'] for r in rows); family_counts=Counter(r['family_id'] for r in rows)
fs={s:{r['family_id'] for r in rows if r['split']==s} for s in ('train','validation','test')}
assert not(fs['train']&fs['validation'] or fs['train']&fs['test'] or fs['validation']&fs['test'])
sha=hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
examples={q:[r for r in rows if q.casefold() in r['text'].casefold()][:5] for q in ['ngelist','membuat daftar','gimana kalau','benang merah','vibe','pake','pengalaman']}
meta={'version':VERSION,'seed':SEED,'rows':len(rows),'unique_texts':len(seen),'sha256':sha,'schema':fields,'label_counts':dict(sorted(label_counts.items())),'function_counts':dict(sorted(function_counts.items())),'split_counts':dict(sorted(split_counts.items())),'semantic_families':len(family_counts),'semantic_family_overlap':0,'valid_function_families_per_function':100,'unknown_families':100,'surface_variants_per_function_family_per_stance':40,'register_generation_counts':dict(register_counts),'design':{'registers':REGISTERS,'styles_per_register':8,'contexts_per_function':10,'concepts_per_function':10,'stances':['support','oppose','mixed'],'notes':['Semua variasi dari semantic family yang sama berada di split yang sama.','Bahasa mencakup formal, netral, slang, chat abbreviation, dan code-mixed.','Dataset tetap sintetis; jumlah besar tidak menggantikan evaluasi pada alasan manusia nyata.']},'examples':examples}
META_PATH.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'csv':str(CSV_PATH),'size_mb':round(CSV_PATH.stat().st_size/1024/1024,2),'rows':len(rows),'split_counts':dict(split_counts),'unknown':label_counts['unknown'],'semantic_families':len(family_counts),'sha256':sha},ensure_ascii=False,indent=2))
