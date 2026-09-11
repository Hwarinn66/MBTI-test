from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # ✅ TAMBAHKAN INI!
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
from psychologist import analyze_with_ai
from datetime import datetime
import os

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve static files (foto artis)
# Buat folder dulu kalau belum ada
if not os.path.exists("famous-people"):
    os.makedirs("famous-people")
    print("⚠️ Folder 'famous-people' dibuat. Silakan isi dengan foto artis!")

app.mount("/famous-people", StaticFiles(directory="famous-people"), name="famous-people")

# ✅ Serve index.html
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: index.html tidak ditemukan!</h1>"

# ✅ Serve result.html
@app.get("/result.html", response_class=HTMLResponse)
async def read_result():
    try:
        with open("result.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: result.html tidak ditemukan!</h1>"

# ✅ Serve famous_people.json
@app.get("/famous_people.json")
async def get_famous_people():
    try:
        return FileResponse("famous_people.json")
    except FileNotFoundError:
        return {"error": "famous_people.json tidak ditemukan"}

class AnswerItem(BaseModel):
    id: int
    topic: str
    dimension: str  # EI, SN, TF, JP
    score: int      # -3 (Sangat Tidak Setuju) hingga +3 (Sangat Setuju)
    choice_text: str
    reason: Optional[str] = ""

class Submission(BaseModel):
    answers: List[AnswerItem]
    user_name: Optional[str] = "User"
    user_age: Optional[int] = 25
    user_gender: Optional[str] = "Tidak Disebutkan"

def calculate_math_score(answers):
    """
    Hitung skor MBTI dengan sistem -3 hingga +3
    
    Scoring Logic:
    - Negatif (-3, -2, -1) → Skor ke huruf pertama (E, S, T, J)
    - Positif (+1, +2, +3) → Skor ke huruf kedua (I, N, F, P)
    - Netral (0) → Skor 0.5 ke KEDUA sisi
    """
    scores = {"E":0.0, "I":0.0, "S":0.0, "N":0.0, "T":0.0, "F":0.0, "J":0.0, "P":0.0}
    neutral_count = 0
    total_questions = len(answers)
    
    for a in answers:
        val = a.score  # -3 to +3
        dim = a.dimension
        
        if val == 0:
            # User memilih "Kadang Ya, Kadang Tidak"
            neutral_count += 1
            
            # Beri skor kecil ke KEDUA sisi
            if dim == "EI":
                scores["E"] += 0.5
                scores["I"] += 0.5
            elif dim == "SN":
                scores["S"] += 0.5
                scores["N"] += 0.5
            elif dim == "TF":
                scores["T"] += 0.5
                scores["F"] += 0.5
            elif dim == "JP":
                scores["J"] += 0.5
                scores["P"] += 0.5
        else:
            # Skor normal untuk -3 hingga +3
            abs_score = abs(val)
            
            if dim == "EI":
                if val > 0: 
                    scores["I"] += abs_score  # Positif = Introvert
                else: 
                    scores["E"] += abs_score  # Negatif = Extravert
                    
            elif dim == "SN":
                if val > 0: 
                    scores["N"] += abs_score  # Positif = Intuition
                else: 
                    scores["S"] += abs_score  # Negatif = Sensing
                    
            elif dim == "TF":
                if val > 0: 
                    scores["F"] += abs_score  # Positif = Feeling
                else: 
                    scores["T"] += abs_score  # Negatif = Thinking
                    
            elif dim == "JP":
                if val > 0: 
                    scores["P"] += abs_score  # Positif = Perceiving
                else: 
                    scores["J"] += abs_score  # Negatif = Judging
    
    # Hitung neutral percentage
    neutral_percentage = (neutral_count / total_questions) * 100
    
    # Tentukan pemenang dengan margin check
    res = ""
    margins = {}
    
    # E vs I
    if scores["E"] > scores["I"]:
        res += "E"
        margins["EI"] = scores["E"] - scores["I"]
    else:
        res += "I"
        margins["EI"] = scores["I"] - scores["E"]
    
    # S vs N
    if scores["S"] > scores["N"]:
        res += "S"
        margins["SN"] = scores["S"] - scores["N"]
    else:
        res += "N"
        margins["SN"] = scores["N"] - scores["S"]
    
    # T vs F
    if scores["T"] > scores["F"]:
        res += "T"
        margins["TF"] = scores["T"] - scores["F"]
    else:
        res += "F"
        margins["TF"] = scores["F"] - scores["T"]
    
    # J vs P
    if scores["J"] > scores["P"]:
        res += "J"
        margins["JP"] = scores["J"] - scores["P"]
    else:
        res += "P"
        margins["JP"] = scores["P"] - scores["J"]
    
    return res, scores, neutral_percentage, margins

def calculate_cognitive_functions(mbti_type, dimension_scores):
    """
    Hitung skor 8 Cognitive Functions berdasarkan:
    1. Function Stack dari tipe MBTI
    2. Skor dimensi (E/I, S/N, T/F, J/P)
    
    Updated for -3 to +3 scoring system
    """
    
    # MAP: MBTI Type → Function Stack (Dominant, Auxiliary, Tertiary, Inferior)
    function_stacks = {
        'INTJ': ['Ni', 'Te', 'Fi', 'Se'],
        'INTP': ['Ti', 'Ne', 'Si', 'Fe'],
        'ENTJ': ['Te', 'Ni', 'Se', 'Fi'],
        'ENTP': ['Ne', 'Ti', 'Fe', 'Si'],
        'INFJ': ['Ni', 'Fe', 'Ti', 'Se'],
        'INFP': ['Fi', 'Ne', 'Si', 'Te'],
        'ENFJ': ['Fe', 'Ni', 'Se', 'Ti'],
        'ENFP': ['Ne', 'Fi', 'Te', 'Si'],
        'ISTJ': ['Si', 'Te', 'Fi', 'Ne'],
        'ISFJ': ['Si', 'Fe', 'Ti', 'Ne'],
        'ESTJ': ['Te', 'Si', 'Ne', 'Fi'],
        'ESFJ': ['Fe', 'Si', 'Ne', 'Ti'],
        'ISTP': ['Ti', 'Se', 'Ni', 'Fe'],
        'ISFP': ['Fi', 'Se', 'Ni', 'Te'],
        'ESTP': ['Se', 'Ti', 'Fe', 'Ni'],
        'ESFP': ['Se', 'Fi', 'Te', 'Ni'],
    }
    
    stack = function_stacks.get(mbti_type, ['Ni', 'Te', 'Fi', 'Se'])
    
    # Base scores dari function stack
    base_scores = {
        stack[0]: 45,  # Dominant
        stack[1]: 38,  # Auxiliary
        stack[2]: 22,  # Tertiary
        stack[3]: 12,  # Inferior
    }
    
    # Hitung bonus dari dimension preferences
    e_i_bonus = (dimension_scores['E'] - dimension_scores['I']) / 1.8
    s_n_bonus = (dimension_scores['S'] - dimension_scores['N']) / 1.95
    t_f_bonus = (dimension_scores['T'] - dimension_scores['F']) / 1.95
    
    # Apply bonuses ke functions
    adjustments = {
        'Ne': s_n_bonus + (e_i_bonus if e_i_bonus > 0 else 0),
        'Ni': s_n_bonus + (-e_i_bonus if e_i_bonus < 0 else 0),
        'Se': -s_n_bonus + (e_i_bonus if e_i_bonus > 0 else 0),
        'Si': -s_n_bonus + (-e_i_bonus if e_i_bonus < 0 else 0),
        'Te': t_f_bonus + (e_i_bonus if e_i_bonus > 0 else 0),
        'Ti': t_f_bonus + (-e_i_bonus if e_i_bonus < 0 else 0),
        'Fe': -t_f_bonus + (e_i_bonus if e_i_bonus > 0 else 0),
        'Fi': -t_f_bonus + (-e_i_bonus if e_i_bonus < 0 else 0),
    }
    
    # Gabungkan base + adjustment
    cognitive_scores = {}
    for func in ['Ni', 'Ne', 'Si', 'Se', 'Ti', 'Te', 'Fi', 'Fe']:
        base = base_scores.get(func, 8)
        adjustment = adjustments.get(func, 0)
        cognitive_scores[func] = max(5, min(50, base + adjustment))
    
    return cognitive_scores, stack

@app.post("/submit")
def submit_test(data: Submission):
    try:
        # Validation
        total_questions = len(data.answers)
        if total_questions == 0:
            return {
                "error": "Tidak ada jawaban yang dikirim.",
                "success": False
            }
        
        # Get personal info (with defaults)
        user_name = data.user_name or "User"
        user_age = data.user_age or 25
        user_gender = data.user_gender or "Tidak Disebutkan"
        
        print(f"📝 Processing test for: {user_name}, {user_age}, {user_gender}")
        
        # Validate age if provided
        if data.user_age and (data.user_age < 13 or data.user_age > 100):
            return {
                "error": "Age must be between 13-100",
                "success": False
            }
        
        print("✅ Step 1: Calculating math scores...")
        # 1. Calculate scores
        math_result, dimension_scores, neutral_pct, margins = calculate_math_score(data.answers)
        print(f"   Math Result: {math_result}")
        
        print("✅ Step 2: Detecting borderline dimensions...")
        # 2. Detect borderline dimensions
        borderline_dimensions = [dim for dim, margin in margins.items() if margin < 5]
        print(f"   Borderline: {borderline_dimensions}")
        
        print("✅ Step 3: Preparing AI data...")
        # 3. Prepare data for AI (with personal context)
        reasons = [{"id": a.id, "question_topic": a.topic, "choice": a.choice_text, "reason": a.reason} for a in data.answers]
        
        print("✅ Step 4: Running AI analysis...")
        # 4. AI Analysis WITH personal info AND dimension scores
        ai_result = analyze_with_ai(
            math_result, 
            reasons, 
            neutral_percentage=neutral_pct,
            borderline_dimensions=borderline_dimensions,
            dimension_scores=dimension_scores,
            user_name=user_name,
            user_age=user_age,
            user_gender=user_gender
        )
        print(f"   AI Result: {ai_result.get('final_mbti', 'N/A')}")
        
        print("✅ Step 5: Calculating cognitive functions...")
        # 5. Calculate Cognitive Functions
        final_type = ai_result.get("final_mbti", math_result)
        cognitive_scores, function_stack = calculate_cognitive_functions(final_type, dimension_scores)
        
        print("✅ Step 6: Preparing response...")
        
        response = {
            "math_result": math_result,
            "final_result": final_type,
            "ai_note": ai_result.get("analysis_note", ""),
            "is_corrected": ai_result.get("is_corrected", False),
            "confidence": ai_result.get("confidence", 1.0),
            "dataset_similarity": ai_result.get("dataset_similarity", 0.0),
            "reasoning": ai_result.get("reasoning", ""),
            "cognitive_scores": cognitive_scores,
            "function_stack": function_stack,
            "dimension_scores": dimension_scores,
            "neutral_percentage": neutral_pct,
            "borderline_dimensions": borderline_dimensions,
            "margins": margins,
            "total_questions": total_questions,
            "success": True
        }
        
        print("✅ SUCCESS! Sending response...")
        return response
        
    except Exception as e:
        print(f"❌ ERROR in submit_test: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "error": f"Internal server error: {str(e)}",
            "success": False,
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)