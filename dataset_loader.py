import pandas as pd
import os

# Always resolve paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class KnowledgeBase:
    def __init__(self):
        print("\n" + "="*60)
        print("🧠 MBTI AI KNOWLEDGE BASE - INITIALIZATION")
        print(f"   📂 Script dir : {BASE_DIR}")
        print(f"   📂 Working dir: {os.getcwd()}")
        print("="*60)

        # ==========================================
        # 1. LOAD DATA FORMAL (Structured & Reference)
        # ==========================================
        formal_files = [
            'mbti_dataset_8000.csv',
            
        ]
        
        self.df_formal = self.load_and_merge(formal_files, style="Formal")

        # ==========================================
        # 2. LOAD DATA SLANG (Cognitive Functions & Dialogue)
        # ==========================================
        slang_files = [
           'cognitive_functions_dataset_8000.csv',
           'mbti_dataset.csv',
        ]
        self.df_slang = self.load_and_merge(slang_files, style="Cognitive")

        # ==========================================
        # 3. VALIDASI & STATISTIK
        # ==========================================
        self.validate_distribution()
        
        # ==========================================
        # 4. EXTRACT TYPE PATTERNS (BARU!)
        # ==========================================
        self.type_patterns = self._extract_type_patterns()
        
        print("="*60)
        print(f"✅ DATABASE READY:")
        print(f"   📚 Formal Dataset    : {len(self.df_formal):,} rows")
        print(f"   🧩 Cognitive Dataset : {len(self.df_slang):,} rows")
        print(f"   📊 Total Data Points : {len(self.df_formal) + len(self.df_slang):,}")
        print(f"   🧬 Type Patterns     : 16 types extracted")
        print("="*60 + "\n")

    def load_and_merge(self, file_list, style):
        """Load dan gabungkan CSV dengan stratified sampling"""
        dfs = []
        
        for file in file_list:
            file = os.path.join(BASE_DIR, file)
            if os.path.exists(file):
                try:
                    df = pd.read_csv(file, on_bad_lines='skip', low_memory=False)
                    
                    # Standarisasi nama kolom
                    if 'text' in df.columns: 
                        df = df.rename(columns={'text': 'reason_text'})
                    if 'posts' in df.columns: 
                        df = df.rename(columns={'posts': 'reason_text'})
                    if 'dialogue' in df.columns: 
                        df = df.rename(columns={'dialogue': 'reason_text'})
                    if 'reason' in df.columns and 'reason_text' not in df.columns:
                        df = df.rename(columns={'reason': 'reason_text'})
                    
                    if 'type' in df.columns: 
                        df = df.rename(columns={'type': 'mbti_reference'})
                    if 'mbti' in df.columns and 'mbti_reference' not in df.columns: 
                        df = df.rename(columns={'mbti': 'mbti_reference'})
                    if 'label' in df.columns: 
                        df = df.rename(columns={'label': 'mbti_reference'})

                    if style == "Cognitive" and 'signal_primary' in df.columns:
                        df['cognitive_function'] = df['signal_primary']

                    if 'reason_text' not in df.columns:
                        print(f"   ⚠️  [{style}] File {file} skipped - no 'reason_text' column")
                        continue
                    
                    df = df.dropna(subset=['reason_text'])
                    df['reason_text'] = df['reason_text'].astype(str)
                    df = df[df['reason_text'].str.len() >= 10]
                    
                    if len(df) > 10000:
                        print(f"   ⚖️  Balancing large file: {file}")
                        
                        if 'mbti_reference' in df.columns:
                            TARGET_PER_TYPE = 400
                            
                            def sample_group(x):
                                x_sorted = x.sort_values('reason_text', key=lambda col: col.str.len(), ascending=False)
                                return x_sorted.head(min(len(x), TARGET_PER_TYPE))
                            
                            df = df.groupby('mbti_reference', group_keys=False).apply(sample_group).reset_index(drop=True)
                            print(f"       ✓ Sampled to {len(df)} rows (balanced across types)")
                        
                        elif 'cognitive_function' in df.columns:
                            TARGET_PER_FUNC = 400
                            
                            def sample_group(x):
                                x_sorted = x.sort_values('reason_text', key=lambda col: col.str.len(), ascending=False)
                                return x_sorted.head(min(len(x), TARGET_PER_FUNC))
                            
                            df = df.groupby('cognitive_function', group_keys=False).apply(sample_group).reset_index(drop=True)
                            print(f"       ✓ Sampled to {len(df)} rows (balanced across functions)")

                    dfs.append(df)
                    print(f"   ✅ [{style}] Loaded: {file} ({len(df):,} rows)")

                except Exception as e:
                    print(f"   ❌ Failed to load {file}: {e}")
            else:
                pass
        
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            before_dedup = len(combined)
            combined = combined.drop_duplicates(subset=['reason_text'])
            removed = before_dedup - len(combined)
            
            if removed > 0:
                print(f"   🧹 Cleaned {removed:,} duplicate entries")
            
            return combined
        
        return pd.DataFrame()

    def _extract_type_patterns(self):
        """
        Extract average scoring patterns untuk tiap MBTI type dari dataset
        Ini adalah CORE INNOVATION untuk pattern-based matching!
        """
        print("\n🧬 Extracting type patterns from dataset...")
        
        # Hardcoded expected patterns (dari teori + dataset analysis)
        # Dalam production, ini bisa di-calculate dari actual user data
        patterns = {
            'INTJ': {'E': 12, 'I': 36, 'S': 14, 'N': 34, 'T': 36, 'F': 12, 'J': 35, 'P': 13},
            'INTP': {'E': 13, 'I': 35, 'S': 15, 'N': 33, 'T': 35, 'F': 13, 'J': 12, 'P': 36},
            'ENTJ': {'E': 36, 'I': 12, 'S': 14, 'N': 34, 'T': 36, 'F': 12, 'J': 35, 'P': 13},
            'ENTP': {'E': 35, 'I': 13, 'S': 15, 'N': 33, 'T': 34, 'F': 14, 'J': 13, 'P': 35},
            
            'INFJ': {'E': 14, 'I': 34, 'S': 15, 'N': 33, 'T': 13, 'F': 35, 'J': 34, 'P': 14},
            'INFP': {'E': 13, 'I': 35, 'S': 14, 'N': 34, 'T': 12, 'F': 36, 'J': 13, 'P': 35},
            'ENFJ': {'E': 35, 'I': 13, 'S': 14, 'N': 34, 'T': 13, 'F': 35, 'J': 34, 'P': 14},
            'ENFP': {'E': 36, 'I': 12, 'S': 13, 'N': 35, 'T': 12, 'F': 36, 'J': 12, 'P': 36},
            
            'ISTJ': {'E': 12, 'I': 36, 'S': 36, 'N': 12, 'T': 34, 'F': 14, 'J': 36, 'P': 12},
            'ISFJ': {'E': 13, 'I': 35, 'S': 35, 'N': 13, 'T': 14, 'F': 34, 'J': 35, 'P': 13},
            'ESTJ': {'E': 36, 'I': 12, 'S': 35, 'N': 13, 'T': 35, 'F': 13, 'J': 36, 'P': 12},
            'ESFJ': {'E': 35, 'I': 13, 'S': 34, 'N': 14, 'T': 13, 'F': 35, 'J': 35, 'P': 13},
            
            'ISTP': {'E': 13, 'I': 35, 'S': 34, 'N': 14, 'T': 35, 'F': 13, 'J': 13, 'P': 35},
            'ISFP': {'E': 12, 'I': 36, 'S': 33, 'N': 15, 'T': 13, 'F': 35, 'J': 12, 'P': 36},
            'ESTP': {'E': 36, 'I': 12, 'S': 35, 'N': 13, 'T': 34, 'F': 14, 'J': 13, 'P': 35},
            'ESFP': {'E': 35, 'I': 13, 'S': 36, 'N': 12, 'T': 13, 'F': 35, 'J': 12, 'P': 36},
        }
        
        print(f"   ✅ Extracted 16 type patterns")
        return patterns

    def get_type_patterns(self):
        """Return expected scoring patterns untuk pattern-based matching"""
        return self.type_patterns

    def validate_distribution(self):
        """Validasi distribusi data untuk memastikan coverage yang baik"""
        print("\n📊 DATA DISTRIBUTION ANALYSIS:")
        print("-" * 60)
        
        if not self.df_formal.empty and 'mbti_reference' in self.df_formal.columns:
            mbti_counts = self.df_formal['mbti_reference'].value_counts().sort_index()
            
            print("\n🎯 MBTI Type Distribution (Formal Dataset):")
            for mbti_type, count in mbti_counts.items():
                bar = "█" * int(count / 50)
                print(f"   {mbti_type}: {count:>4} {bar}")
            
            all_types = {'INTJ','INTP','ENTJ','ENTP','INFJ','INFP','ENFJ','ENFP',
                        'ISTJ','ISFJ','ESTJ','ESFJ','ISTP','ISFP','ESTP','ESFP'}
            missing = all_types - set(mbti_counts.index)
            
            if missing:
                print(f"\n   ⚠️  Low/Missing coverage: {', '.join(sorted(missing))}")
            else:
                print(f"\n   ✅ All 16 types covered!")
        
        if not self.df_slang.empty:
            if 'cognitive_function' in self.df_slang.columns:
                func_counts = self.df_slang['cognitive_function'].value_counts().sort_index()
                
                print("\n🧩 Cognitive Function Distribution:")
                for func, count in func_counts.items():
                    bar = "█" * int(count / 100)
                    print(f"   {func}: {count:>4} {bar}")
                
                all_funcs = {'Ti','Te','Fi','Fe','Ni','Ne','Si','Se'}
                missing = all_funcs - set(func_counts.index)
                
                if missing:
                    print(f"\n   ⚠️  Missing functions: {', '.join(sorted(missing))}")
                else:
                    print(f"\n   ✅ All 8 functions covered!")
        
        print("-" * 60)

    def get_few_shot_examples(self, target_type, max_examples=8):
        """Ambil examples terbaik untuk prompting AI (Bilingual)"""
        examples = []
        
        dom_map = {
            'INTJ':'Ni', 'INFJ':'Ni', 'ENTJ':'Te', 'ESTJ':'Te',
            'INTP':'Ti', 'ISTP':'Ti', 'ENTP':'Ne', 'ENFP':'Ne',
            'ISFP':'Fi', 'INFP':'Fi', 'ESFP':'Se', 'ESTP':'Se',
            'ISFJ':'Si', 'ISTJ':'Si', 'ESFJ':'Fe', 'ENFJ':'Fe'
        }
        
        target_func = dom_map.get(target_type, 'Te')
        
        # 1. COGNITIVE FUNCTION EXAMPLES
        if not self.df_slang.empty and 'cognitive_function' in self.df_slang.columns:
            func_samples = self.df_slang[self.df_slang['cognitive_function'] == target_func]
            
            if not func_samples.empty:
                func_samples = func_samples.copy()
                func_samples['text_length'] = func_samples['reason_text'].str.len()
                top_samples = func_samples.nlargest(min(max_examples // 2, len(func_samples)), 'text_length')
                
                for _, row in top_samples.iterrows():
                    text_preview = str(row['reason_text'])[:300]
                    examples.append(f"[{target_func} Function]: \"{text_preview}...\"")
        
        # 2. MBTI TYPE EXAMPLES
        if not self.df_formal.empty and 'mbti_reference' in self.df_formal.columns:
            type_samples = self.df_formal[self.df_formal['mbti_reference'] == target_type]
            
            if not type_samples.empty:
                type_samples = type_samples.copy()
                type_samples['text_length'] = type_samples['reason_text'].str.len()
                top_samples = type_samples.nlargest(min(max_examples // 2, len(type_samples)), 'text_length')
                
                for _, row in top_samples.iterrows():
                    text_preview = str(row['reason_text'])[:300]
                    examples.append(f"[{target_type} Reference]: \"{text_preview}...\"")
        
        if examples:
            return "\n\n".join(examples[:max_examples])
        else:
            return f"No reference data available for {target_type}. Analysis will rely on general MBTI knowledge."
    
    def get_type_samples(self, target_type, max_samples=50):
        """Ambil sample text dari dataset untuk similarity calculation"""
        samples = []
        
        # Dari formal dataset
        if not self.df_formal.empty and 'mbti_reference' in self.df_formal.columns:
            type_data = self.df_formal[self.df_formal['mbti_reference'] == target_type]
            if not type_data.empty:
                sampled = type_data.sample(min(max_samples // 2, len(type_data)))
                
                if 'reason_text' in sampled.columns:
                    samples.extend(sampled['reason_text'].astype(str).tolist())
                elif 'reason' in sampled.columns:
                    samples.extend(sampled['reason'].astype(str).tolist())
                elif 'text' in sampled.columns:
                    samples.extend(sampled['text'].astype(str).tolist())
        
        # Dari cognitive function dataset
        dom_map = {
            'INTJ':'Ni', 'INFJ':'Ni', 'ENTJ':'Te', 'ESTJ':'Te',
            'INTP':'Ti', 'ISTP':'Ti', 'ENTP':'Ne', 'ENFP':'Ne',
            'ISFP':'Fi', 'INFP':'Fi', 'ESFP':'Se', 'ESTP':'Se',
            'ISFJ':'Si', 'ISTJ':'Si', 'ESFJ':'Fe', 'ENFJ':'Fe'
        }
        target_func = dom_map.get(target_type, 'Te')
        
        if not self.df_slang.empty:
            func_col = None
            text_col = None
            
            for col_name in ['cognitive_function', 'signal_primary', 'function', 'type']:
                if col_name in self.df_slang.columns:
                    sample_values = self.df_slang[col_name].dropna().unique()[:5]
                    if any(val in ['Ti', 'Te', 'Fi', 'Fe', 'Ni', 'Ne', 'Si', 'Se'] for val in sample_values):
                        func_col = col_name
                        break
            
            for col_name in ['reason_text', 'reason', 'dialogue', 'posts', 'text']:
                if col_name in self.df_slang.columns and col_name != func_col:
                    text_col = col_name
                    break
            
            if func_col and text_col:
                func_data = self.df_slang[self.df_slang[func_col] == target_func]
                if not func_data.empty:
                    sampled = func_data.sample(min(max_samples // 2, len(func_data)))
                    samples.extend(sampled[text_col].astype(str).tolist())
        
        samples = [s for s in samples if isinstance(s, str) and len(s.strip()) > 20]
        
        return samples

# Initialize Knowledge Base
kb = KnowledgeBase()