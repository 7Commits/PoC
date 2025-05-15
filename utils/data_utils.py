import os
import pandas as pd
import streamlit as st
from pathlib import Path
import uuid
import json

# Crea percorsi di directory
DATA_DIR = Path("data")
QUESTIONS_FILE = DATA_DIR / "questions.csv"
QUESTION_SETS_FILE = DATA_DIR / "question_sets.csv"
RESULTS_FILE = DATA_DIR / "test_results.csv"
API_PRESETS_FILE = DATA_DIR / "api_presets.csv" # Nuovo file per i preset API

def initialize_data():
    """Inizializza le directory e i file di dati se non esistono."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)

    if not QUESTIONS_FILE.exists():
        questions_df = pd.DataFrame({
            'id': pd.Series(dtype='str'),
            'domanda': pd.Series(dtype='str'),
            'risposta_attesa': pd.Series(dtype='str'),
            'categoria': pd.Series(dtype='str')
        })
        questions_df.to_csv(QUESTIONS_FILE, index=False)

    if not QUESTION_SETS_FILE.exists():
        sets_df = pd.DataFrame({
            'id': pd.Series(dtype='str'),
            'name': pd.Series(dtype='str'),
            'questions': pd.Series(dtype='object')
        })
        sets_df.to_csv(QUESTION_SETS_FILE, index=False)

    if not RESULTS_FILE.exists():
        results_df = pd.DataFrame({
            'id': pd.Series(dtype='str'),
            'set_id': pd.Series(dtype='str'),
            'timestamp': pd.Series(dtype='str'),
            'results': pd.Series(dtype='object')
        })
        results_df.to_csv(RESULTS_FILE, index=False)
    
    if not API_PRESETS_FILE.exists():
        presets_df = pd.DataFrame({
            'id': pd.Series(dtype='str'),
            'name': pd.Series(dtype='str'), # Nome del preset definito dall'utente
            'provider_name': pd.Series(dtype='str'), # Es. "OpenAI", "Anthropic", "Personalizzato"
            'endpoint': pd.Series(dtype='str'), # URL dell'endpoint o "custom"
            'api_key': pd.Series(dtype='str'), # Chiave API (considerare la sicurezza)
            'model': pd.Series(dtype='str'), # Nome del modello
            'temperature': pd.Series(dtype='float'),
            'max_tokens': pd.Series(dtype='int')
        })
        presets_df.to_csv(API_PRESETS_FILE, index=False)


def load_api_presets():
    """Carica i preset API dal file CSV."""
    if API_PRESETS_FILE.exists():
        try:
            df = pd.read_csv(API_PRESETS_FILE)
            # Assicura i tipi di dati corretti, specialmente per i numerici
            df['id'] = df['id'].astype(str)
            df['name'] = df['name'].astype(str).fillna("")
            df['provider_name'] = df['provider_name'].astype(str).fillna("")
            df['endpoint'] = df['endpoint'].astype(str).fillna("")
            df['api_key'] = df['api_key'].astype(str).fillna("")
            df['model'] = df['model'].astype(str).fillna("")
            df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce').fillna(0.0)
            df['max_tokens'] = pd.to_numeric(df['max_tokens'], errors='coerce').fillna(1000).astype(int)
            return df
        except pd.errors.EmptyDataError:
            pass # Restituisce DataFrame vuoto sotto
        except Exception as e:
            st.error(f"Errore durante la lettura di {API_PRESETS_FILE}: {e}")
    
    return pd.DataFrame({
        'id': pd.Series(dtype='str'),
        'name': pd.Series(dtype='str'),
        'provider_name': pd.Series(dtype='str'),
        'endpoint': pd.Series(dtype='str'),
        'api_key': pd.Series(dtype='str'),
        'model': pd.Series(dtype='str'),
        'temperature': pd.Series(dtype='float'),
        'max_tokens': pd.Series(dtype='int')
    })

def save_api_presets(presets_df):
    """Salva i preset API nel file CSV."""
    # Assicura che le colonne siano nell'ordine desiderato e abbiano il tipo corretto
    expected_columns = ['id', 'name', 'provider_name', 'endpoint', 'api_key', 'model', 'temperature', 'max_tokens']
    df_to_save = pd.DataFrame(columns=expected_columns)

    for col in expected_columns:
        if col in presets_df.columns:
            if presets_df[col].dtype == 'float64': # Gestione specifica per float
                 df_to_save[col] = presets_df[col].astype(float)
            elif presets_df[col].dtype == 'int64' or presets_df[col].dtype == 'int32': # Gestione specifica per int
                 df_to_save[col] = presets_df[col].astype(int)
            else:
                 df_to_save[col] = presets_df[col].astype(str)
        else:
            # Assegna un tipo di default se la colonna manca (non dovrebbe accadere)
            if col in ['temperature']:
                df_to_save[col] = pd.Series(dtype='float')
            elif col in ['max_tokens']:
                df_to_save[col] = pd.Series(dtype='int')
            else:
                df_to_save[col] = pd.Series(dtype='str')

    df_to_save.to_csv(API_PRESETS_FILE, index=False)
    if 'api_presets' in st.session_state: # Aggiorna lo stato della sessione se esiste
        st.session_state.api_presets = df_to_save.copy() # Salva una copia per evitare modifiche per riferimento

# --- Funzioni esistenti (accorciate per brevità, nessuna modifica qui) --- 

def load_questions():
    """Carica le domande dal file CSV, gestendo la migrazione dei nomi delle colonne e l'aggiunta di 'categoria'."""
    if QUESTIONS_FILE.exists():
        try:
            df = pd.read_csv(QUESTIONS_FILE)
            if 'question' in df.columns and 'domanda' not in df.columns:
                df.rename(columns={'question': 'domanda'}, inplace=True)
            if 'expected_answer' in df.columns and 'risposta_attesa' not in df.columns:
                df.rename(columns={'expected_answer': 'risposta_attesa'}, inplace=True)
            if 'categoria' not in df.columns:
                df['categoria'] = ""
            df['id'] = df['id'].astype(str)
            df['domanda'] = df['domanda'].astype(str).fillna("")
            df['risposta_attesa'] = df['risposta_attesa'].astype(str).fillna("")
            df['categoria'] = df['categoria'].astype(str).fillna("")
            return df
        except pd.errors.EmptyDataError:
            pass
        except Exception as e:
            st.error(f"Errore durante la lettura di {QUESTIONS_FILE}: {e}")
    return pd.DataFrame({'id': pd.Series(dtype='str'), 'domanda': pd.Series(dtype='str'), 'risposta_attesa': pd.Series(dtype='str'), 'categoria': pd.Series(dtype='str')})

def save_questions(questions_df):
    expected_columns = ['id', 'domanda', 'risposta_attesa', 'categoria']
    df_to_save = pd.DataFrame(columns=expected_columns)
    for col in expected_columns:
        if col in questions_df.columns:
            df_to_save[col] = questions_df[col].astype(str)
        else:
            df_to_save[col] = pd.Series(dtype='str')
    df_to_save.to_csv(QUESTIONS_FILE, index=False)
    st.session_state.questions = df_to_save

def load_question_sets():
    if QUESTION_SETS_FILE.exists():
        try:
            sets_df = pd.read_csv(QUESTION_SETS_FILE)
            if not sets_df.empty and 'questions' in sets_df.columns:
                sets_df['questions'] = sets_df['questions'].apply(lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else ([] if pd.isna(x) else x))
            else:
                sets_df = pd.DataFrame({'id': pd.Series(dtype='str'), 'name': pd.Series(dtype='str'), 'questions': pd.Series(dtype='object')})
            sets_df['id'] = sets_df['id'].astype(str)
            sets_df['name'] = sets_df['name'].astype(str).fillna("")
            sets_df['questions'] = sets_df['questions'].apply(lambda x: x if isinstance(x, list) else [])
            return sets_df
        except pd.errors.EmptyDataError:
            pass
        except Exception as e:
            st.error(f"Errore durante la lettura di {QUESTION_SETS_FILE}: {e}")
    return pd.DataFrame({'id': pd.Series(dtype='str'), 'name': pd.Series(dtype='str'), 'questions': pd.Series(dtype='object')})

def save_question_sets(sets_df):
    sets_df_to_save = sets_df.copy()
    if not sets_df_to_save.empty and 'questions' in sets_df_to_save.columns:
        sets_df_to_save['questions'] = sets_df_to_save['questions'].apply(lambda x: json.dumps(x) if isinstance(x, list) else "[]")
    sets_df_to_save.to_csv(QUESTION_SETS_FILE, index=False)
    st.session_state.question_sets = sets_df

def load_results():
    if RESULTS_FILE.exists():
        try:
            results_df = pd.read_csv(RESULTS_FILE)
            if not results_df.empty and 'results' in results_df.columns:
                results_df['results'] = results_df['results'].apply(lambda x: json.loads(x) if isinstance(x, str) and x.startswith('{') else ({} if pd.isna(x) else x))
            else:
                results_df = pd.DataFrame({'id': pd.Series(dtype='str'), 'set_id': pd.Series(dtype='str'), 'timestamp': pd.Series(dtype='str'), 'results': pd.Series(dtype='object')})
            results_df['id'] = results_df['id'].astype(str)
            results_df['set_id'] = results_df['set_id'].astype(str).fillna("")
            results_df['timestamp'] = results_df['timestamp'].astype(str).fillna("")
            results_df['results'] = results_df['results'].apply(lambda x: x if isinstance(x, dict) else {})
            return results_df
        except pd.errors.EmptyDataError:
            pass
        except Exception as e:
            st.error(f"Errore durante la lettura di {RESULTS_FILE}: {e}")
    return pd.DataFrame({'id': pd.Series(dtype='str'), 'set_id': pd.Series(dtype='str'), 'timestamp': pd.Series(dtype='str'), 'results': pd.Series(dtype='object')})

def save_results(results_df):
    results_df_to_save = results_df.copy()
    if not results_df_to_save.empty and 'results' in results_df_to_save.columns:
        results_df_to_save['results'] = results_df_to_save['results'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else "{}")
    results_df_to_save.to_csv(RESULTS_FILE, index=False)
    st.session_state.results = results_df

def add_question(testo_domanda, risposta_prevista, categoria=""):
    questions_df = st.session_state.questions.copy()
    new_question_data = {'id': str(uuid.uuid4()), 'domanda': str(testo_domanda), 'risposta_attesa': str(risposta_prevista), 'categoria': str(categoria)}
    new_question_df = pd.DataFrame([new_question_data])
    questions_df = pd.concat([questions_df, new_question_df], ignore_index=True)
    save_questions(questions_df)
    return new_question_data['id']

def update_question(question_id, testo_domanda=None, risposta_prevista=None, categoria=None):
    questions_df = st.session_state.questions.copy()
    idx = questions_df.index[questions_df['id'] == str(question_id)].tolist()
    if idx:
        updated = False
        if testo_domanda is not None: questions_df.at[idx[0], 'domanda'] = str(testo_domanda); updated = True
        if risposta_prevista is not None: questions_df.at[idx[0], 'risposta_attesa'] = str(risposta_prevista); updated = True
        if categoria is not None: questions_df.at[idx[0], 'categoria'] = str(categoria); updated = True
        if updated: save_questions(questions_df)
        return True
    return False

def delete_question(question_id):
    questions_df = st.session_state.questions.copy()
    questions_df = questions_df[questions_df['id'] != str(question_id)]
    save_questions(questions_df)
    update_sets_after_question_deletion(str(question_id))

def update_sets_after_question_deletion(question_id):
    sets_df = st.session_state.question_sets.copy()
    if not sets_df.empty:
        sets_df['questions'] = sets_df['questions'].apply(lambda q_list: [q_id for q_id in q_list if str(q_id) != str(question_id)] if isinstance(q_list, list) else [])
        save_question_sets(sets_df)

def create_question_set(name, question_ids=None):
    sets_df = st.session_state.question_sets.copy()
    new_set_data = {'id': str(uuid.uuid4()), 'name': str(name), 'questions': [str(qid) for qid in question_ids] if question_ids else []}
    new_set_df = pd.DataFrame([new_set_data])
    sets_df = pd.concat([sets_df, new_set_df], ignore_index=True)
    save_question_sets(sets_df)
    return new_set_data['id']

def update_question_set(set_id, name=None, question_ids=None):
    sets_df = st.session_state.question_sets.copy()
    idx = sets_df.index[sets_df['id'] == str(set_id)].tolist()
    if idx:
        updated = False
        if name is not None: sets_df.at[idx[0], 'name'] = str(name); updated = True
        if question_ids is not None: sets_df.at[idx[0], 'questions'] = [str(qid) for qid in question_ids]; updated = True
        if updated: save_question_sets(sets_df)
        return True
    return False

def delete_question_set(set_id):
    sets_df = st.session_state.question_sets.copy()
    sets_df = sets_df[sets_df['id'] != str(set_id)]
    save_question_sets(sets_df)

def add_test_result(set_id, results_data):
    results_df = st.session_state.results.copy()
    new_result_data = {'id': str(uuid.uuid4()), 'set_id': str(set_id), 'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), 'results': results_data if isinstance(results_data, dict) else {}}
    new_result_df = pd.DataFrame([new_result_data])
    results_df = pd.concat([results_df, new_result_df], ignore_index=True)
    save_results(results_df)
    return new_result_data['id']

def import_questions_from_file(file):
    try:
        file_extension = os.path.splitext(file.name)[1].lower()
        imported_df = None
        if file_extension == '.csv': imported_df = pd.read_csv(file)
        elif file_extension == '.json':
            data = json.load(file)
            if isinstance(data, list): imported_df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'questions' in data and isinstance(data['questions'], list): imported_df = pd.DataFrame(data['questions'])
            else: return False, "Il file JSON deve essere una lista di domande o un oggetto con una chiave 'questions' contenente una lista."
        else: return False, "Formato file non supportato. Caricare un file CSV o JSON."
        if imported_df is None or imported_df.empty: return False, "Il file importato è vuoto o non contiene dati validi."
        if 'question' in imported_df.columns and 'domanda' not in imported_df.columns: imported_df.rename(columns={'question': 'domanda'}, inplace=True)
        if 'expected_answer' in imported_df.columns and 'risposta_attesa' not in imported_df.columns: imported_df.rename(columns={'expected_answer': 'risposta_attesa'}, inplace=True)
        required_columns = ['domanda', 'risposta_attesa']
        if not all(col in imported_df.columns for col in required_columns): return False, f"Il file importato deve contenere le colonne '{required_columns[0]}' e '{required_columns[1]}'."
        if 'id' not in imported_df.columns: imported_df['id'] = [str(uuid.uuid4()) for _ in range(len(imported_df))]
        else: imported_df['id'] = imported_df['id'].astype(str)
        if 'categoria' not in imported_df.columns: imported_df['categoria'] = ""
        else: imported_df['categoria'] = imported_df['categoria'].astype(str).fillna("")
        imported_df['domanda'] = imported_df['domanda'].astype(str).fillna("")
        imported_df['risposta_attesa'] = imported_df['risposta_attesa'].astype(str).fillna("")
        final_imported_df = imported_df[['id', 'domanda', 'risposta_attesa', 'categoria']]
        questions_df = st.session_state.questions.copy()
        questions_df = pd.concat([questions_df, final_imported_df], ignore_index=True)
        save_questions(questions_df)
        return True, f"Importate con successo {len(final_imported_df)} domande."
    except Exception as e:
        return False, f"Errore durante l'importazione delle domande: {str(e)}"

