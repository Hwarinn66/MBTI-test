import os
from google import genai
from google.genai import types
from dataset_loader import kb
from dotenv import load_dotenv
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pydantic import BaseModel, Field

# Load API Key
load_dotenv()
api_key = os.getenv("AIzaSyBCCtFrsRLNrl-aOrLcT_Xf2iHDL72MK9E")
client = genai.Client(api_key=api_key)

MODEL_NAME = 'gemini-2.5-flash'
print("✅ Using Gemini 2.5 Flash (google-genai)")

class AIAnalysisResult(BaseModel):
    final_mbti: str = Field(description="Tipe MBTI final (contoh: INTJ, ISFP)")
    is_corrected: bool = Field(description="True jika dataset override hasil math")
    confidence: float = Field(description="Skor kepercayaan 0.0 - 1.0")
    dataset_similarity: float = Field(description="Skor kesesuaian dataset 0.0 - 1.0")
    reasoning: str = Field(description="Penjelasan singkat kenapa tipe ini dipilih")
    analysis_note: str = Field(description="Laporan analisis psikologis lengkap dalam Bahasa Indonesia. Pisahkan paragraf dengan literal string \\n\\n, JANGAN pakai enter.")

def clean_json_string(raw_json):
    """Clean JSON string dari control characters dan format issues"""
    # Remove markdown code blocks
    cleaned = re.sub(r'```json\s*|\s*```', '', raw_json)
    cleaned = re.sub(r'```\s*|\s*```', '', cleaned)
    
    # Extract JSON object (greedy)
    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
    
    # Fix common issues - escape newlines in strings
    def escape_newlines_in_strings(match):
        string_content = match.group(0)
        # Normalize then escape
        string_content = string_content.replace('\\n', '\n')
        string_content = string_content.replace('\n', '\\n')
        string_content = string_content.replace('\r', '\\r')
        string_content = string_content.replace('\t', '\\t')
        return string_content
    
    # Apply to all string values (between quotes)
    cleaned = re.sub(r'"[^"]*"', escape_newlines_in_strings, cleaned)
    
    return cleaned

def safe_json_parse(text_response, max_attempts=3):
    """Attempt to parse JSON with multiple strategies"""
    for attempt in range(max_attempts):
        try:
            if attempt == 0:
                # Direct parse
                return json.loads(text_response)
            elif attempt == 1:
                # Clean and parse
                cleaned = clean_json_string(text_response)
                return json.loads(cleaned)
            elif attempt == 2:
                # Extra aggressive cleaning
                cleaned = clean_json_string(text_response)
                # Remove all actual newlines (not \\n)
                cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
                return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"⚠️ Parse attempt {attempt + 1} failed: {e}")
            if attempt == max_attempts - 1:
                raise
    
    return None

def detect_language(text):
    """Deteksi bahasa dominan dari user input"""
    indo_words = ['saya', 'aku', 'gue', 'yang', 'dengan', 'untuk', 'tapi', 'karena', 'kalau', 'jadi', 'lebih', 'sangat']
    eng_words = ['i', 'me', 'my', 'the', 'and', 'but', 'because', 'if', 'so', 'that', 'more', 'very']
    
    text_lower = text.lower()
    indo_count = sum(1 for word in indo_words if word in text_lower)
    eng_count = sum(1 for word in eng_words if f' {word} ' in f' {text_lower} ')
    
    return "Indonesian" if indo_count > eng_count else "English"

def translate_to_english(text):
    """Translate Indonesian to English for better dataset matching"""
    if len(text.strip()) < 10:
        return text
    
    if detect_language(text) == "English":
        print(f"   ✅ Text already in English")
        return text
    
    try:
        from deep_translator import GoogleTranslator
        
        print(f"   🌍 Translating Indonesian → English...")
        translator = GoogleTranslator(source='id', target='en')
        
        max_chunk_size = 4500
        if len(text) > max_chunk_size:
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                try:
                    translated = translator.translate(chunk)
                    translated_chunks.append(translated)
                except Exception as e:
                    translated_chunks.append(chunk)
            
            result = ' '.join(translated_chunks)
        else:
            result = translator.translate(text)
        
        print(f"   ✅ Translation complete")
        return result
        
    except ImportError:
        print(f"   ⚠️ deep-translator not installed")
        return text
    except Exception as e:
        print(f"   ⚠️ Translation error: {e}")
        return text

def calculate_pattern_similarity(dimension_scores):
    """Calculate similarity based on scoring patterns"""
    print(f"\n🧬 PATTERN-BASED SIMILARITY ANALYSIS:")
    print("="*60)
    
    type_patterns = kb.get_type_patterns()
    similarities = {}
    
    user_vector = np.array([
        dimension_scores.get('E', 0), dimension_scores.get('I', 0),
        dimension_scores.get('S', 0), dimension_scores.get('N', 0),
        dimension_scores.get('T', 0), dimension_scores.get('F', 0),
        dimension_scores.get('J', 0), dimension_scores.get('P', 0)
    ])
    
    print(f"   User pattern: E={dimension_scores.get('E',0):.1f} I={dimension_scores.get('I',0):.1f} " +
          f"S={dimension_scores.get('S',0):.1f} N={dimension_scores.get('N',0):.1f} " +
          f"T={dimension_scores.get('T',0):.1f} F={dimension_scores.get('F',0):.1f} " +
          f"J={dimension_scores.get('J',0):.1f} P={dimension_scores.get('P',0):.1f}")
    
    for mbti_type, expected in type_patterns.items():
        type_vector = np.array([
            expected['E'], expected['I'],
            expected['S'], expected['N'],
            expected['T'], expected['F'],
            expected['J'], expected['P']
        ])
        
        similarity = cosine_similarity([user_vector], [type_vector])[0][0]
        similarities[mbti_type] = float(max(0, similarity))
    
    sorted_sims = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n📊 Top 5 Pattern Matches:")
    for i, (mtype, sim) in enumerate(sorted_sims[:5], 1):
        bar = "█" * int(sim * 50)
        print(f"   {i}. {mtype}: {sim:.3f} ({sim*100:.1f}%) {bar}")
    
    print("="*60)
    
    return similarities

def calculate_dataset_similarity(user_text, target_type):
    """Calculate similarity between user's reasoning and dataset"""
    print(f"\n🔬 DATASET SIMILARITY ANALYSIS:")
    print(f"   Original text length: {len(user_text)} chars")
    print(f"   Language: {detect_language(user_text)}")
    print("="*60)
    
    if len(user_text.strip()) == 0:
        print("   ⚠️ User text is completely empty")
        all_types = ['INTJ','INTP','ENTJ','ENTP','INFJ','INFP','ENFJ','ENFP',
                     'ISTJ','ISFJ','ESTJ','ESFJ','ISTP','ISFP','ESTP','ESFP']
        return {t: 0.15 for t in all_types}
    
    user_text_for_matching = translate_to_english(user_text)
    print(f"   🌐 Translated ({len(user_text_for_matching)} chars): {user_text_for_matching[:150]}...")
    
    all_types = ['INTJ','INTP','ENTJ','ENTP','INFJ','INFP','ENFJ','ENFP',
                 'ISTJ','ISFJ','ESTJ','ESFJ','ISTP','ISFP','ESTP','ESFP']
    
    type_similarities = {}
    
    for mbti_type in all_types:
        type_samples = kb.get_type_samples(mbti_type, max_samples=50)
        
        if not type_samples:
            print(f"   ⚠️ No samples for {mbti_type}")
            type_similarities[mbti_type] = 0.0
            continue
        
        if mbti_type == target_type:
            print(f"   ✓ {mbti_type} has {len(type_samples)} samples")
            print(f"   ✓ Sample preview: {type_samples[0][:100]}...")
        
        dataset_text = " ".join(type_samples)
        
        try:
            vectorizer_word = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 2),
                min_df=1,
                stop_words=None,
                lowercase=True,
                token_pattern=r'\b\w+\b'
            )
            
            try:
                tfidf_word = vectorizer_word.fit_transform([user_text_for_matching, dataset_text])
                similarity_word = cosine_similarity(tfidf_word[0:1], tfidf_word[1:2])[0][0]
            except:
                similarity_word = 0.0
            
            vectorizer_char = TfidfVectorizer(
                max_features=150,
                analyzer='char_wb',
                ngram_range=(2, 4),
                min_df=1,
                lowercase=True
            )
            
            try:
                tfidf_char = vectorizer_char.fit_transform([user_text_for_matching, dataset_text])
                similarity_char = cosine_similarity(tfidf_char[0:1], tfidf_char[1:2])[0][0]
            except:
                similarity_char = 0.0
            
            similarity = (0.6 * similarity_word) + (0.4 * similarity_char)
            type_similarities[mbti_type] = float(similarity)
            
            if similarity > 0.01:
                print(f"   ✓ {mbti_type}: {similarity:.3f} (word: {similarity_word:.3f}, char: {similarity_char:.3f})")
            
        except Exception as e:
            print(f"   ❌ TF-IDF error for {mbti_type}: {e}")
            type_similarities[mbti_type] = 0.0
    
    max_similarity = max(type_similarities.values())
    
    if max_similarity == 0.0:
        print(f"\n   ⚠️ All similarities are 0! Giving baseline 15% to math result: {target_type}")
        type_similarities[target_type] = 0.15
    elif max_similarity < 0.10:
        print(f"\n   ⚠️ Max similarity too low ({max_similarity:.1%}), adding 10% boost to all types")
        for mtype in type_similarities:
            type_similarities[mtype] = min(type_similarities[mtype] + 0.10, 1.0)
    elif max_similarity < 0.20:
        print(f"\n   ℹ️ Low similarity ({max_similarity:.1%}), adding 5% boost")
        for mtype in type_similarities:
            type_similarities[mtype] = min(type_similarities[mtype] + 0.05, 1.0)
    
    sorted_types = sorted(type_similarities.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n📊 Top 5 Most Similar Types:")
    for i, (mtype, sim) in enumerate(sorted_types[:5], 1):
        bar = "█" * int(sim * 50)
        marker = "👈 MATH RESULT" if mtype == target_type else ""
        print(f"   {i}. {mtype}: {sim:.3f} ({sim*100:.1f}%) {bar} {marker}")
    
    print("="*60)
    
    return type_similarities

def analyze_with_ai(math_result_type, user_answers_with_reasons, neutral_percentage=0, borderline_dimensions=[], dimension_scores={}, user_name="", user_age=0, user_gender=""):
    """AI analysis with dataset-driven decision (FULL ORIGINAL PROMPT RESTORED)"""
    all_reasons = " ".join([item['reason'] for item in user_answers_with_reasons if item['reason']])
    
    print("\n" + "="*60)
    print("🔬 DATASET-DRIVEN ANALYSIS (70% Dataset, 30% AI)")
    print("="*60)
    
    text_similarities = calculate_dataset_similarity(all_reasons, math_result_type)
    text_confidence = max(text_similarities.values())
    text_top_type = max(text_similarities, key=text_similarities.get)
    
    pattern_similarities = calculate_pattern_similarity(dimension_scores)
    pattern_confidence = max(pattern_similarities.values())
    pattern_top_type = max(pattern_similarities, key=pattern_similarities.get)
    
    combined_dataset_scores = {}
    for mbti_type in text_similarities.keys():
        combined_score = (0.4 * text_similarities[mbti_type]) + (0.6 * pattern_similarities[mbti_type])
        combined_dataset_scores[mbti_type] = combined_score
    
    dataset_top_type = max(combined_dataset_scores, key=combined_dataset_scores.get)
    dataset_confidence = combined_dataset_scores[dataset_top_type]
    
    print(f"\n📊 DATASET ANALYSIS SUMMARY:")
    print(f"   Text-based:    {text_top_type} ({text_confidence:.1%})")
    print(f"   Pattern-based: {pattern_top_type} ({pattern_confidence:.1%})")
    print(f"   🎯 COMBINED:   {dataset_top_type} ({dataset_confidence:.1%})")
    print(f"\n   📝 Math Result: {math_result_type}")
    print(f"   ⚖️ Neutral: {neutral_percentage:.1f}%")
    if borderline_dimensions:
        print(f"   ⚠️ Borderline: {', '.join(borderline_dimensions)}")
    
    top_3_dataset = sorted(combined_dataset_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    
    has_reason = any(item['reason'] and len(item['reason']) > 3 for item in user_answers_with_reasons)
    
    if not has_reason:
        print("\n⚠️ No detailed reasons provided, using dataset + math only")
        return {
            "final_mbti": dataset_top_type if dataset_confidence > 0.5 else math_result_type,
            "is_corrected": dataset_top_type != math_result_type and dataset_confidence > 0.5,
            "confidence": dataset_confidence,
            "dataset_similarity": dataset_confidence,
            "reasoning": f"Dataset: {dataset_top_type} ({dataset_confidence:.1%}), Math: {math_result_type}",
            "analysis_note": f"**Dataset Analysis ({dataset_confidence:.1%} match):** Pola jawaban Anda sangat mirip dengan tipe {dataset_top_type} dalam database kami.\n\n**Mathematical Result:** Scoring menunjukkan {math_result_type}.\n\n*Catatan: Untuk analisis yang lebih mendalam, berikan alasan pada beberapa pertanyaan.*"
        }
    
    # ========== ORIGINAL FULL PROMPT (RESTORED) ==========
    total_reasons = sum(1 for item in user_answers_with_reasons if item['reason'] and len(item['reason']) > 10)
    avg_reason_length = sum(len(item['reason']) for item in user_answers_with_reasons if item['reason']) / max(total_reasons, 1)
    
    if total_reasons >= 40:
        target_words = "1200-1500 kata"
    elif total_reasons >= 20:
        target_words = "800-1200 kata"
    elif total_reasons >= 10:
        target_words = "500-800 kata"
    else:
        target_words = "300-500 kata"
    
    gender_pronoun = ""
    if user_gender == "Perempuan":
        gender_pronoun = "sebagai seorang perempuan"
    elif user_gender == "Laki-laki":
        gender_pronoun = "sebagai seorang laki-laki"
    
    age_context = ""
    if user_age < 18:
        age_context = f"Di usia {user_age} tahun yang masih muda"
    elif user_age < 25:
        age_context = f"Di usia {user_age} tahun"
    elif user_age < 35:
        age_context = f"Sebagai young adult ({user_age} tahun)"
    elif user_age < 50:
        age_context = f"Dengan pengalaman hidup {user_age} tahun"
    else:
        age_context = f"Dengan wisdom dari {user_age} tahun perjalanan hidup"
    
    alternative_examples = ""
    if dataset_top_type != math_result_type:
        alternative_examples = f"\n\n⚠️ IMPORTANT: Dataset strongly suggests {dataset_top_type} ({dataset_confidence:.1%} confidence)\n"
        alternative_examples += f"Math calculation shows {math_result_type}\n"
        alternative_examples += f"Pattern similarity: {pattern_confidence:.1%}\n"
        alternative_examples += f"Text similarity: {text_confidence:.1%}\n\n"
        alternative_examples += kb.get_few_shot_examples(dataset_top_type, max_examples=30)

    prompt = f"""
Kamu adalah AI personality analyst yang friendly dan conversational. Kamu HARUS menulis dengan gaya CASUAL tapi TETAP SOPAN (pakai "aku/kamu", bukan "gue/lo" atau formal "saya/Anda").

⚠️ CRITICAL RULES:
1. JANGAN gunakan simbol berlebihan (**, ===, ----, bullets, emoji berlebihan)
2. JANGAN terlalu banyak pakai bahasa Inggris - maksimal 5-10% aja
3. Tulis seperti ngobrol sama teman yang respect - friendly tapi sopan
4. WAJIB mention jawaban spesifik user dengan nomor soal ("Di soal #15 kamu bilang...")
5. WAJIB sapa dengan nama: "Halo {user_name}!"
6. WAJIB mention umur & gender kalau relevan
7. Panjang tulisan: {target_words} (user kasih {total_reasons} alasan dengan rata-rata {avg_reason_length:.0f} karakter)

==================== PERSONAL INFO ====================
Nama: {user_name}
Umur: {user_age} tahun
Gender: {user_gender}

==================== DATASET EVIDENCE (70% WEIGHT) ====================
Dataset (31,551 profiles): {dataset_top_type} ({dataset_confidence:.1%})
Pattern match: {pattern_confidence:.1%}
Text match: {text_confidence:.1%}
Top 3: {', '.join([f"{t}({s:.1%})" for t, s in top_3_dataset])}

Math scoring: {math_result_type}
Neutral: {neutral_percentage:.1f}%
Borderline: {', '.join(borderline_dimensions) if borderline_dimensions else 'None'}

==================== USER'S DETAILED ANSWERS ====================
"""
    
    # Sanitize user reasons to avoid control characters
    for item in user_answers_with_reasons:
        if item['reason']:
            # Clean reason text - replace control chars with spaces
            clean_reason = item['reason'].replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            prompt += f"""
Soal #{item['id']} - {item['question_topic']}
Pilihan: {item['choice']}
Alasan: "{clean_reason}"

"""

    prompt += f"""
==================== WRITING STYLE EXAMPLES ====================
JANGAN TULIS SEPERTI INI (terlalu formal/kaku):
"Berdasarkan analisis mendalam terhadap respons Anda, dapat disimpulkan bahwa Anda menunjukkan karakteristik..."

JUGA JANGAN SEPERTI INI (terlalu banyak Inggris):
"Gue udah liat semua jawaban lo nih, and honestly lo punya vibe yang keren. Your pattern match 91% dengan typical INTP, specifically cara lo approach problems..."

❌ JANGAN JELASKAN HURUF MBTI SEPERTI INI:
"E vs I: Kamu lebih introvert karena suka waktu sendiri.
S vs N: Kamu lebih intuitive karena suka teori.
T vs F: Kamu lebih thinking karena logis.
J vs P: Kamu lebih perceiving karena fleksibel."

✅ TULIS SEPERTI INI (friendly professional dengan COGNITIVE FUNCTIONS):
"Halo {user_name}! Aku udah baca semua jawaban kamu dengan teliti nih, dan jujur aja, kamu punya kepribadian yang cukup menarik.

Oke, jadi gini... pola kamu di database aku cocok sekitar {pattern_confidence:.0f}% dengan orang-orang yang punya tipe {dataset_top_type}. {age_context}, cara kamu menghadapi masalah itu udah cukup matang loh.

Sekarang aku jelasin function stack kamu ya. Tipe {dataset_top_type} punya susunan: [sebutkan 4 functions].

Function UTAMA kamu adalah [Dominant Function]. Ini keliatan banget di soal #15 dimana kamu bilang \"quote jawaban user\" - nah cara kamu [jelaskan behavior spesifik] itu sangat khas [Dominant Function]. Fungsi ini kayak CEO di otak kamu, yang paling sering dipake dan paling kuat.

Terus function PENDUKUNG kamu [Auxiliary Function]. Di soal #28 kamu cerita \"quote jawaban user\" - ini menunjukkan gimana [Auxiliary Function] kamu bekerja untuk [jelaskan fungsinya]. Ini kayak asisten CEO, selalu support si Dominant.

Function KETIGA adalah [Tertiary Function], yang masih dalam tahap berkembang. Kadang muncul pas kamu lagi santai atau nyaman.

Terakhir, function KELEMAHAN kamu [Inferior Function]. Di soal #42 tentang [topic], kamu agak struggle - nah ini wajar karena [Inferior Function] memang challenging buat tipe {dataset_top_type}..."

==================== BAHASA INDONESIA vs ENGLISH ====================
✅ PAKAI (Bahasa Indonesia):
- "sebenarnya/sejujurnya" (bukan "actually/honestly")
- "pada dasarnya/intinya" (bukan "basically")
- "khususnya/terutama" (bukan "specifically/especially")
- "biasanya/umumnya" (bukan "usually/typically")
- "kemungkinan besar/mungkin" (bukan "probably/maybe")
- "cukup/lumayan/agak" (bukan "quite/pretty")
- "menghadapi masalah" (bukan "approach problems")
- "proses pengambilan keputusan" (bukan "decision-making process")
- "kekuatan/kelemahan" (bukan "strengths/weaknesses")

❌ HINDARI (Terlalu banyak English):
- "honestly/basically/actually/typically/specifically"
- "strengths/weaknesses/challenges"
- "decision-making/problem-solving"
- "personality traits/characteristics"

BOLEH PAKAI (English terms yang udah umum & sulit diganti):
- "Fe/Fi/Te/Ti/Ne/Ni/Se/Si" (cognitive functions - istilah teknis)
- "Dominant/Auxiliary/Tertiary/Inferior" (istilah MBTI standar)
- "INFP/INTJ/etc" (tipe MBTI)

==================== TONE GUIDELINES ====================
✅ USE (Natural & Friendly):
- "aku/kamu" (bukan gue/lo atau saya/Anda)
- "udah/belum" instead of "sudah/belum"
- "gimana/kayak" instead of "bagaimana/seperti"
- "ngerjain/ngelakuin" instead of "mengerjakan/melakukan"
- "cukup", "lumayan", "agak", "rada"
- "sebenarnya", "jujur aja"
- "nih", "sih", "kok", "loh" (tapi jangan berlebihan)

❌ AVOID:
- "gue/lo/elu/gw/bro/bestie" - TOO INFORMAL
- "Berdasarkan/Dapat disimpulkan/Dengan demikian" - TOO FORMAL
- English phrases: "honestly speaking/basically/in real life/moving forward"

==================== STRUCTURE ====================
Target length: {target_words}

1. OPENING (50-80 kata):
   - Sapa dengan nama: "Halo {user_name}!"
   - Hook menarik dari jawaban user
   - Light mention umur/gender kalau relevan
   - Tone: Warm & welcoming
   - Bahasa: 100% Indonesia

2. DATASET INSIGHTS (150-250 kata):
   - "Oke jadi berdasarkan 31,551 profil yang aku analisis..."
   - Jelasin pattern match {pattern_confidence:.1%}
   - "Kamu ini cukup mirip dengan orang-orang yang punya tipe {dataset_top_type}..."
   - Minimal 2-3 referensi spesifik ke nomor soal
   - Bahasa: 95% Indonesia, 5% English (hanya istilah teknis)

3. COGNITIVE FUNCTIONS ANALYSIS (300-500 kata):
   - WAJIB jelasin function stack {dataset_top_type}: Contoh untuk INTP = Ti (Dominant) → Ne (Auxiliary) → Si (Tertiary) → Fe (Inferior)
   - Jelasin SETIAP function dengan contoh dari jawaban user:
     * Dominant function: "Fungsi utama kamu adalah Ti (Introverted Thinking). Ini keliatan banget di soal #X dimana kamu bilang '...' - cara kamu menganalisis masalah itu sangat Ti banget."
     * Auxiliary function: "Fungsi pendukung kamu Ne (Extraverted Intuition). Di soal #Y kamu cerita '...' - nah ini menunjukkan gimana kamu explore berbagai kemungkinan."
     * Tertiary function: "Si (Introverted Sensing) adalah fungsi ketiga kamu, masih berkembang."
     * Inferior function: "Fe (Extraverted Feeling) adalah fungsi kelemahan kamu - makanya di soal #Z tentang empati kamu agak struggle."
   - JANGAN jelasin huruf MBTI (E/I, S/N, T/F, J/P) - fokus ke 8 cognitive functions!
   - WAJIB quote minimal 3-5 jawaban spesifik user untuk menjelaskan functions
   - Pake analogi yang mudah dipahami
   - Bahasa: 90% Indonesia (English hanya untuk istilah function: Ti, Ne, Si, Fe, dll)

4. PERSONALITY IN ACTION (200-300 kata):
   - "Dalam kehidupan sehari-hari, kamu kemungkinan besar tipe orang yang..."
   - Kekuatan, tantangan, cara mengambil keputusan
   - {"Mention gender context kalau relevan: " + gender_pronoun if gender_pronoun else ""}
   - {age_context} - relate to life stage
   - Bahasa: 95% Indonesia

5. UNIQUE OBSERVATIONS (100-200 kata):
   - Highlight 2-3 hal menarik dari jawaban user
   - "Yang aku perhatikan nih, di soal #XX sama #YY..."
   - Make it personal & memorable
   - Bahasa: 100% Indonesia

6. CLOSING (50-80 kata):
   - Pesan yang encouraging
   - "Jadi intinya {user_name}, kamu itu..."
   - Saran pengembangan diri yang actionable
   - Bahasa: 100% Indonesia

TOTAL: {target_words}

==================== CRITICAL REMINDERS ====================
- NO SYMBOLS: No **, ---, ===, bullets (• or -), excessive emojis
- MINIMAL ENGLISH: Maksimal 5-10% (hanya istilah teknis MBTI)
- QUOTE SPECIFIC ANSWERS: Minimal 3-5 kali mention "di soal #X"
- USE NAME: Panggil {user_name} minimal 3-4 kali
- BALANCED TONE: Friendly tapi professional, casual tapi sopan
- SMOOTH FLOW: Natural conversation dalam Bahasa Indonesia
- USE "aku/kamu": CONSISTENTLY
- NO CONTROL CHARACTERS: Use plain text only, separate paragraphs with double newline
- ⚠️ FOCUS ON COGNITIVE FUNCTIONS (Ti, Te, Fi, Fe, Ni, Ne, Si, Se) NOT MBTI LETTERS (E/I, S/N, T/F, J/P)
- ⚠️ ALWAYS mention the 4-function stack: Dominant → Auxiliary → Tertiary → Inferior

==================== COGNITIVE FUNCTIONS REFERENCE ====================
Function Stack untuk setiap tipe:
- INTJ: Ni → Te → Fi → Se
- INTP: Ti → Ne → Si → Fe
- ENTJ: Te → Ni → Se → Fi
- ENTP: Ne → Ti → Fe → Si
- INFJ: Ni → Fe → Ti → Se
- INFP: Fi → Ne → Si → Te
- ENFJ: Fe → Ni → Se → Ti
- ENFP: Ne → Fi → Te → Si
- ISTJ: Si → Te → Fi → Ne
- ISFJ: Si → Fe → Ti → Ne
- ESTJ: Te → Si → Ne → Fi
- ESFJ: Fe → Si → Ne → Ti
- ISTP: Ti → Se → Ni → Fe
- ISFP: Fi → Se → Ni → Te
- ESTP: Se → Ti → Fe → Ni
- ESFP: Se → Fi → Te → Ni

Penjelasan Functions:
- Ti (Introverted Thinking): Analisis internal, logika subjektif, framework mental
- Te (Extraverted Thinking): Efisiensi, sistem eksternal, hasil terukur
- Fi (Introverted Feeling): Nilai personal, autentisitas, moral internal
- Fe (Extraverted Feeling): Harmoni sosial, empati grup, emotional atmosphere
- Ni (Introverted Intuition): Visi jangka panjang, insight mendalam, pola tersembunyi
- Ne (Extraverted Intuition): Kemungkinan, brainstorming, koneksi ide
- Si (Introverted Sensing): Memori detail, tradisi, pengalaman masa lalu
- Se (Extraverted Sensing): Pengalaman real-time, action, sensory awareness

==================== OUTPUT FORMAT ====================
Return ONLY valid JSON with NO markdown, NO code blocks:
{{
    "final_mbti": "{dataset_top_type if dataset_confidence > 0.5 else math_result_type}",
    "is_corrected": true/false,
    "confidence": 0.75,
    "dataset_similarity": {dataset_confidence},
    "reasoning": "Brief explanation",
    "analysis_note": "FULL ANALYSIS DALAM BAHASA INDONESIA (minimal English, no symbols, paragraphs separated by double newline only)"
}}

IMPORTANT: In analysis_note, write plain text paragraphs separated ONLY by double newline (\\n\\n). Do NOT use any special formatting, control characters, or symbols.
"""

    try:
        # ✅ PANGGIL API DENGAN RESPONSE SCHEMA
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.15,
                top_p=0.65,
                top_k=25,
                response_mime_type="application/json",
                response_schema=AIAnalysisResult,  # Memaksa output sesuai schema Pydantic
            )
        )
        
        text_response = response.text.strip()
        
        print("\n" + "="*60)
        print("🤖 GEMINI STRUCTURED RESPONSE:")
        print("="*60)
        print(text_response[:500] + "...")
        print("="*60)
        
        # Karena kita pakai response_schema, hasilnya DIJAMIN JSON valid
        result = json.loads(text_response)
        
        ai_raw_confidence = result.get("confidence", 0.7)
        final_confidence = (0.7 * dataset_confidence) + (0.3 * ai_raw_confidence)
        
        if dataset_confidence > 0.60 and result.get("final_mbti") != dataset_top_type:
            print(f"\n⚠️ AI suggested {result.get('final_mbti')}, but dataset shows {dataset_top_type} ({dataset_confidence:.1%})")
            print(f"   Overriding AI decision - dataset is too strong to ignore!")
            result["final_mbti"] = dataset_top_type
            result["is_corrected"] = True
            result["reasoning"] = f"Dataset override: {dataset_confidence:.1%} confidence for {dataset_top_type}"
        
        result["confidence"] = final_confidence
        result["dataset_similarity"] = dataset_confidence
        result.setdefault("final_mbti", dataset_top_type if dataset_confidence > 0.5 else math_result_type)
        result.setdefault("is_corrected", result["final_mbti"] != math_result_type)
        result.setdefault("reasoning", f"Dataset: {dataset_confidence:.1%}, AI: {ai_raw_confidence:.1%}")
        
        print(f"\n🤖 FINAL DECISION:")
        print(f"   📝 Math: {math_result_type}")
        print(f"   🗄️ Dataset: {dataset_top_type} ({dataset_confidence:.1%})")
        print(f"   🤖 AI Raw: {ai_raw_confidence:.0%}")
        print(f"   🎯 Final: {result['final_mbti']}")
        print(f"   ✅ Confidence: {final_confidence:.0%} (70% dataset + 30% AI)")
        print(f"   ⚖️ Neutral%: {neutral_percentage:.1f}%")
        
        return result
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ JSON Parse Error: {e}")
        if 'text_response' in locals():
            print(f"Attempted to parse: {text_response[:500]}")
        
        return {
            "final_mbti": dataset_top_type if dataset_confidence > 0.5 else math_result_type,
            "is_corrected": dataset_top_type != math_result_type,
            "confidence": dataset_confidence,
            "dataset_similarity": dataset_confidence,
            "reasoning": f"JSON parsing failed: {str(e)[:100]}",
            "analysis_note": f"""Halo {user_name}!

AI mengalami kesulitan teknis dalam memproses analisis lengkap (JSON parsing error), tapi tenang - aku tetap punya hasil untuk kamu berdasarkan dataset analysis.

Dari 31,551 profil yang aku analisis, pola jawaban kamu paling mirip dengan tipe {dataset_top_type} dengan confidence {dataset_confidence:.0%}.

Pattern matching menunjukkan {pattern_confidence:.0%} kesesuaian, sementara text similarity ada di {text_confidence:.0%}.

Math calculation memberikan hasil {math_result_type}, dan kamu memilih jawaban netral sebanyak {neutral_percentage:.1f}%.

{age_context}, cara kamu menjawab {total_reasons} pertanyaan dengan alasan menunjukkan pola yang cukup konsisten dengan tipe {dataset_top_type}.

Beberapa insight dari jawabanmu:

Kamu cenderung {gender_pronoun if gender_pronoun else 'menunjukkan pola yang'} konsisten dalam cara mengambil keputusan. Dataset menunjukkan bahwa orang-orang dengan tipe {dataset_top_type} biasanya memiliki cara berpikir yang mirip dengan pola yang kamu tunjukkan.

Yang menarik, ada {len(borderline_dimensions)} dimensi yang borderline: {', '.join(borderline_dimensions) if borderline_dimensions else 'tidak ada'}. Ini menunjukkan bahwa kepribadian kamu cukup seimbang di beberapa aspek.

Untuk hasil yang lebih akurat dan analisis mendalam yang dipersonalisasi, coba tes ulang dengan memberikan lebih banyak alasan detail pada setiap pertanyaan (minimal 20-30 soal dengan alasan yang substantif).

Jadi intinya {user_name}, berdasarkan pola scoring dan dataset matching, kamu termasuk tipe {dataset_top_type}. Tipe ini biasanya punya kekuatan dalam hal analisis dan pemahaman yang mendalam.

"""
        }
    except Exception as e:
        print(f"❌ Unexpected AI Error: {e}")
        import traceback
        traceback.print_exc()

        # Retry with fallback model if quota exceeded
        is_quota_error = '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e) or '404' in str(e) or 'NOT_FOUND' in str(e)
        fallback_models = ['gemini-2.0-flash', 'gemini-2.0-flash-lite']

        if is_quota_error:
            for fallback in fallback_models:
                try:
                    print(f"⚠️ Quota exceeded, trying fallback: {fallback}")
                    response = client.models.generate_content(
                        model=fallback,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.15,
                            top_p=0.65,
                            top_k=25,
                        )
                    )
                    text_response = response.text.strip()
                    result = safe_json_parse(text_response)
                    if result:
                        print(f"✅ Fallback {fallback} succeeded!")
                        result.setdefault('final_mbti', math_result_type)
                        result.setdefault('is_corrected', False)
                        result.setdefault('confidence', dataset_confidence)
                        result.setdefault('dataset_similarity', dataset_confidence)
                        return result
                except Exception as fallback_err:
                    print(f"❌ Fallback {fallback} also failed: {fallback_err}")
                    continue

        final_type = dataset_top_type if dataset_confidence > 0.5 else math_result_type
        return {
            "final_mbti": final_type,
            "is_corrected": final_type != math_result_type,
            "confidence": dataset_confidence,
            "dataset_similarity": dataset_confidence,
            "reasoning": f"Dataset analysis: {final_type} ({dataset_confidence:.0%})",
            "analysis_note": f"""Halo {user_name}!

Aku udah analisis pola jawaban kamu dan hasilnya menunjukkan kamu punya tipe kepribadian {final_type}.

{age_context}, dari {total_reasons} jawaban dengan alasan yang kamu berikan, pola yang kamu tunjukkan cukup konsisten dengan karakteristik tipe {final_type}.

Sayangnya analisis mendalam dari AI sedang tidak tersedia saat ini karena keterbatasan teknis. Untuk mendapatkan laporan psikologis yang lebih lengkap dan personal, coba lagi dalam beberapa menit.

Jadi intinya {user_name}, berdasarkan pola jawabanmu, kamu termasuk tipe {final_type}.
"""
        }