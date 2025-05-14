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


def initialize_data():
    """Inizializza le directory e i file di dati se non esistono."""
    # Crea la directory dei dati se non esiste
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)

    # Crea il file delle domande se non esiste
    if not QUESTIONS_FILE.exists():
        questions_df = pd.DataFrame({
            'id': pd.Series(dtype='str'),
            'domanda': pd.Series(dtype='str'),  # Rinominata
            'risposta_attesa': pd.Series(dtype='str'),  # Rinominata
            'categoria': pd.Series(dtype='str')  # Aggiunta
        })
        questions_df.to_csv(QUESTIONS_FILE, index=False)

    # Crea il file dei set di domande se non esiste
    if not QUESTION_SETS_FILE.exists():
        sets_df = pd.DataFrame({
            'id': pd.Series(dtype='str'),
            'name': pd.Series(dtype='str'),
            'questions': pd.Series(dtype='object')  # Lista di ID domande
        })
        sets_df.to_csv(QUESTION_SETS_FILE, index=False)

    # Crea il file dei risultati se non esiste
    if not RESULTS_FILE.exists():
        results_df = pd.DataFrame({
            'id': pd.Series(dtype='str'),
            'set_id': pd.Series(dtype='str'),
            'timestamp': pd.Series(dtype='str'),
            'results': pd.Series(dtype='object')  # Dizionario dei risultati
        })
        results_df.to_csv(RESULTS_FILE, index=False)


def load_questions():
    """Carica le domande dal file CSV, gestendo la migrazione dei nomi delle colonne e l'aggiunta di 'categoria'."""
    if QUESTIONS_FILE.exists():
        try:
            df = pd.read_csv(QUESTIONS_FILE)

            # Gestione migrazione nomi colonne
            if 'question' in df.columns and 'domanda' not in df.columns:
                df.rename(columns={'question': 'domanda'}, inplace=True)
            if 'expected_answer' in df.columns and 'risposta_attesa' not in df.columns:
                df.rename(columns={'expected_answer': 'risposta_attesa'}, inplace=True)

            # Aggiunta colonna 'categoria' se non esiste
            if 'categoria' not in df.columns:
                df['categoria'] = ""

            # Assicurarsi che le colonne abbiano il tipo corretto, specialmente se 'categoria' era appena aggiunta
            df['id'] = df['id'].astype(str)
            df['domanda'] = df['domanda'].astype(str).fillna("")
            df['risposta_attesa'] = df['risposta_attesa'].astype(str).fillna("")
            df['categoria'] = df['categoria'].astype(str).fillna("")

            return df
        except pd.errors.EmptyDataError:  # File vuoto
            pass  # Restituisce DataFrame vuoto con nuovo schema sotto
        except Exception as e:  # Altri errori di lettura
            st.error(f"Errore durante la lettura di {QUESTIONS_FILE}: {e}")
            # Restituisce comunque un DataFrame vuoto con lo schema corretto per non bloccare l'app

    return pd.DataFrame({
        'id': pd.Series(dtype='str'),
        'domanda': pd.Series(dtype='str'),
        'risposta_attesa': pd.Series(dtype='str'),
        'categoria': pd.Series(dtype='str')
    })


def save_questions(questions_df):
    """Salva le domande nel file CSV."""
    # Assicurarsi che le colonne siano nell'ordine desiderato e abbiano il tipo corretto
    expected_columns = ['id', 'domanda', 'risposta_attesa', 'categoria']
    df_to_save = pd.DataFrame(columns=expected_columns)  # Crea un df con l'ordine corretto

    for col in expected_columns:
        if col in questions_df.columns:
            df_to_save[col] = questions_df[col].astype(str)
        else:  # Se una colonna attesa manca nel dataframe di input (non dovrebbe succedere con la logica attuale)
            df_to_save[col] = pd.Series(dtype='str')

    df_to_save.to_csv(QUESTIONS_FILE, index=False)
    st.session_state.questions = df_to_save  # Salva il df normalizzato nello stato


def load_question_sets():
    """Carica i set di domande dal file CSV."""
    if QUESTION_SETS_FILE.exists():
        try:
            sets_df = pd.read_csv(QUESTION_SETS_FILE)
            if not sets_df.empty and 'questions' in sets_df.columns:
                sets_df['questions'] = sets_df['questions'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else ([] if pd.isna(x) else x)
                )
            else:  # Gestisce il caso di un file vuoto o senza la colonna 'questions'
                sets_df = pd.DataFrame({'id': pd.Series(dtype='str'), 'name': pd.Series(dtype='str'),
                                        'questions': pd.Series(dtype='object')})

            # Assicura tipi corretti
            sets_df['id'] = sets_df['id'].astype(str)
            sets_df['name'] = sets_df['name'].astype(str).fillna("")
            # 'questions' dovrebbe già essere una lista o una lista vuota
            sets_df['questions'] = sets_df['questions'].apply(lambda x: x if isinstance(x, list) else [])

            return sets_df
        except pd.errors.EmptyDataError:
            pass
        except Exception as e:
            st.error(f"Errore durante la lettura di {QUESTION_SETS_FILE}: {e}")

    return pd.DataFrame(
        {'id': pd.Series(dtype='str'), 'name': pd.Series(dtype='str'), 'questions': pd.Series(dtype='object')})


def save_question_sets(sets_df):
    """Salva i set di domande nel file CSV."""
    sets_df_to_save = sets_df.copy()
    if not sets_df_to_save.empty and 'questions' in sets_df_to_save.columns:
        sets_df_to_save['questions'] = sets_df_to_save['questions'].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else "[]"
        )
    sets_df_to_save.to_csv(QUESTION_SETS_FILE, index=False)
    st.session_state.question_sets = sets_df  # Salva il df originale (con liste) nello stato


def load_results():
    """Carica i risultati dei test dal file CSV."""
    if RESULTS_FILE.exists():
        try:
            results_df = pd.read_csv(RESULTS_FILE)
            if not results_df.empty and 'results' in results_df.columns:
                results_df['results'] = results_df['results'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) and x.startswith('{') else ({} if pd.isna(x) else x)
                )
            else:  # Gestisce il caso di un file vuoto o senza la colonna 'results'
                results_df = pd.DataFrame({'id': pd.Series(dtype='str'), 'set_id': pd.Series(dtype='str'),
                                           'timestamp': pd.Series(dtype='str'), 'results': pd.Series(dtype='object')})

            # Assicura tipi corretti
            results_df['id'] = results_df['id'].astype(str)
            results_df['set_id'] = results_df['set_id'].astype(str).fillna("")
            results_df['timestamp'] = results_df['timestamp'].astype(str).fillna("")
            results_df['results'] = results_df['results'].apply(lambda x: x if isinstance(x, dict) else {})

            return results_df
        except pd.errors.EmptyDataError:
            pass
        except Exception as e:
            st.error(f"Errore durante la lettura di {RESULTS_FILE}: {e}")

    return pd.DataFrame(
        {'id': pd.Series(dtype='str'), 'set_id': pd.Series(dtype='str'), 'timestamp': pd.Series(dtype='str'),
         'results': pd.Series(dtype='object')})


def save_results(results_df):
    """Salva i risultati dei test nel file CSV."""
    results_df_to_save = results_df.copy()
    if not results_df_to_save.empty and 'results' in results_df_to_save.columns:
        results_df_to_save['results'] = results_df_to_save['results'].apply(
            lambda x: json.dumps(x) if isinstance(x, dict) else "{}"
        )
    results_df_to_save.to_csv(RESULTS_FILE, index=False)
    st.session_state.results = results_df  # Salva il df originale (con dicts) nello stato


def add_question(testo_domanda, risposta_prevista, categoria=""):
    """Aggiunge una nuova domanda al dataframe delle domande."""
    questions_df = st.session_state.questions.copy()

    new_question_data = {
        'id': str(uuid.uuid4()),
        'domanda': str(testo_domanda),
        'risposta_attesa': str(risposta_prevista),
        'categoria': str(categoria)
    }

    new_question_df = pd.DataFrame([new_question_data])
    questions_df = pd.concat([questions_df, new_question_df], ignore_index=True)

    save_questions(questions_df)
    return new_question_data['id']


def update_question(question_id, testo_domanda=None, risposta_prevista=None, categoria=None):
    """Aggiorna una domanda esistente nel dataframe delle domande."""
    questions_df = st.session_state.questions.copy()

    idx = questions_df.index[questions_df['id'] == str(question_id)].tolist()

    if idx:
        updated = False
        if testo_domanda is not None:
            questions_df.at[idx[0], 'domanda'] = str(testo_domanda)
            updated = True
        if risposta_prevista is not None:
            questions_df.at[idx[0], 'risposta_attesa'] = str(risposta_prevista)
            updated = True
        if categoria is not None:
            questions_df.at[idx[0], 'categoria'] = str(categoria)
            updated = True

        if updated:
            save_questions(questions_df)
        return True

    return False


def delete_question(question_id):
    """Elimina una domanda dal dataframe delle domande."""
    questions_df = st.session_state.questions.copy()
    questions_df = questions_df[questions_df['id'] != str(question_id)]
    save_questions(questions_df)
    update_sets_after_question_deletion(str(question_id))


def update_sets_after_question_deletion(question_id):
    """Aggiorna i set di domande dopo l'eliminazione di una domanda."""
    sets_df = st.session_state.question_sets.copy()

    if not sets_df.empty:
        sets_df['questions'] = sets_df['questions'].apply(
            lambda q_list: [q_id for q_id in q_list if str(q_id) != str(question_id)] if isinstance(q_list,
                                                                                                    list) else []
        )
        save_question_sets(sets_df)


def create_question_set(name, question_ids=None):
    """Crea un nuovo set di domande."""
    sets_df = st.session_state.question_sets.copy()

    new_set_data = {
        'id': str(uuid.uuid4()),
        'name': str(name),
        'questions': [str(qid) for qid in question_ids] if question_ids else []
    }

    new_set_df = pd.DataFrame([new_set_data])
    sets_df = pd.concat([sets_df, new_set_df], ignore_index=True)

    save_question_sets(sets_df)
    return new_set_data['id']


def update_question_set(set_id, name=None, question_ids=None):
    """Aggiorna un set di domande esistente."""
    sets_df = st.session_state.question_sets.copy()

    idx = sets_df.index[sets_df['id'] == str(set_id)].tolist()

    if idx:
        updated = False
        if name is not None:
            sets_df.at[idx[0], 'name'] = str(name)
            updated = True
        if question_ids is not None:
            sets_df.at[idx[0], 'questions'] = [str(qid) for qid in question_ids]
            updated = True

        if updated:
            save_question_sets(sets_df)
        return True

    return False


def delete_question_set(set_id):
    # Elimina un set di domande
    sets_df = st.session_state.question_sets.copy()
    questions_df = st.session_state.questions.copy()
    
    # Trova il set da eliminare
    set_to_delete = sets_df[sets_df['id'] == str(set_id)]
    if set_to_delete.empty:
        return

    # Ottieni gli ID delle domande nel set da eliminare
    question_ids_in_set = set_to_delete.iloc[0].get('questions', [])
    if not isinstance(question_ids_in_set, list):
        question_ids_in_set = []

    # Trova le domande usate in altri set
    other_sets_df = sets_df[sets_df['id'] != str(set_id)]
    question_ids_used_elsewhere = set()
    for qlist in other_sets_df['questions']:
        if isinstance(qlist, list):
            question_ids_used_elsewhere.update(qlist)

    # Domande che possono essere eliminate perché usate solo in questo set
    question_ids_to_delete = [
        qid for qid in question_ids_in_set if qid not in question_ids_used_elsewhere
    ]

    # Elimina le domande dal df
    questions_df = questions_df[~questions_df['id'].isin(question_ids_to_delete)]
    save_questions(questions_df)

    # Elimina il set dal df
    sets_df = sets_df[sets_df['id'] != str(set_id)]
    save_question_sets(sets_df)
    st.session_state.question_sets = sets_df


def add_test_result(set_id, results_data):
    # Aggiunge un nuovo risultato del test.
    results_df = st.session_state.results.copy()

    new_result_data = {
        'id': str(uuid.uuid4()),
        'set_id': str(set_id),
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'results': results_data if isinstance(results_data, dict) else {}
    }

    new_result_df = pd.DataFrame([new_result_data])
    results_df = pd.concat([results_df, new_result_df], ignore_index=True)

    save_results(results_df)
    return new_result_data['id']


def import_questions_from_file(file):
    """Importa domande da un file CSV o JSON e crea un set automaticamente se tutte le domande condividono la stessa categoria."""
    try:
        file_extension = os.path.splitext(file.name)[1].lower()
        imported_df = None

        if file_extension == '.csv':
            imported_df = pd.read_csv(file)
        elif file_extension == '.json':
            data = json.load(file)
            if isinstance(data, list):  # Lista di oggetti domanda
                imported_df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'questions' in data and isinstance(data['questions'],
                                                                               list):  # Oggetto JSON con una chiave 'questions'
                imported_df = pd.DataFrame(data['questions'])
            else:
                return False, "Il file JSON deve essere una lista di domande o un oggetto con una chiave 'questions' contenente una lista."
        else:
            return False, "Formato file non supportato. Caricare un file CSV o JSON."

        if imported_df is None or imported_df.empty:
            return False, "Il file importato è vuoto o non contiene dati validi."

        # Rinominare vecchie colonne se presenti
        if 'question' in imported_df.columns and 'domanda' not in imported_df.columns:
            imported_df.rename(columns={'question': 'domanda'}, inplace=True)
        if 'expected_answer' in imported_df.columns and 'risposta_attesa' not in imported_df.columns:
            imported_df.rename(columns={'expected_answer': 'risposta_attesa'}, inplace=True)

        required_columns = ['domanda', 'risposta_attesa']
        if not all(col in imported_df.columns for col in required_columns):
            return False, f"Il file importato deve contenere le colonne '{required_columns[0]}' e '{required_columns[1]}'."

        # Aggiungere 'id' se non presente
        if 'id' not in imported_df.columns:
            imported_df['id'] = [str(uuid.uuid4()) for _ in range(len(imported_df))]
        else:
            imported_df['id'] = imported_df['id'].astype(str)

        # Aggiungere 'categoria' se non presente, con valore predefinito
        if 'categoria' not in imported_df.columns:
            imported_df['categoria'] = ""
        else:
            imported_df['categoria'] = imported_df['categoria'].astype(str).fillna("")

        # Seleziona solo le colonne rilevanti e assicura il tipo corretto
        imported_df['domanda'] = imported_df['domanda'].astype(str).fillna("")
        imported_df['risposta_attesa'] = imported_df['risposta_attesa'].astype(str).fillna("")

        final_imported_df = imported_df[['id', 'domanda', 'risposta_attesa', 'categoria']]

        questions_df = st.session_state.questions.copy()
        questions_df = pd.concat([questions_df, final_imported_df], ignore_index=True)
        save_questions(questions_df)

        # Se tutte le domande hanno la stessa categoria, crea un set
        categorie_uniche = final_imported_df['categoria'].dropna().unique()
        if len(categorie_uniche) == 1 and categorie_uniche[0].strip():
            nome_set = categorie_uniche[0].strip()
            domande_ids = final_imported_df['id'].tolist()
            create_question_set(nome_set, domande_ids)
        
        return True, f"Importate con successo {len(final_imported_df)} domande."

    except Exception as e:
        return False, f"Errore durante l'importazione delle domande: {str(e)}"
