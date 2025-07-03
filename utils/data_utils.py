import os
import pandas as pd
import streamlit as st
import uuid
import json
from sqlalchemy import text

from .db_utils import get_engine, init_db

def initialize_data():
    """Inizializza il database creando le tabelle."""
    init_db()


def load_api_presets():
    """Carica i preset API dal database."""
    try:
        df = pd.read_sql("SELECT * FROM api_presets", get_engine())
        df['id'] = df['id'].astype(str)
        df['name'] = df['name'].astype(str).fillna("")
        df['provider_name'] = df['provider_name'].astype(str).fillna("")
        df['endpoint'] = df['endpoint'].astype(str).fillna("")
        df['api_key'] = df['api_key'].astype(str).fillna("")
        df['model'] = df['model'].astype(str).fillna("")
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce').fillna(0.0)
        df['max_tokens'] = pd.to_numeric(df['max_tokens'], errors='coerce').fillna(1000).astype(int)
        return df
    except Exception as e:
        st.error(f"Errore durante la lettura della tabella api_presets: {e}")

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
    """Salva i preset API nel database."""
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
    engine = get_engine()
    with engine.begin() as conn:
        existing_ids = pd.read_sql('SELECT id FROM api_presets', conn)['id'].astype(str).tolist()
        incoming_ids = df_to_save['id'].astype(str).tolist()

        # Elimina i preset rimossi
        ids_to_delete = set(existing_ids) - set(incoming_ids)
        for del_id in ids_to_delete:
            conn.execute(text('DELETE FROM api_presets WHERE id = :id'), {'id': del_id})

        # Inserisci o aggiorna i preset forniti
        for _, row in df_to_save.iterrows():
            params = row.to_dict()
            if row['id'] in existing_ids:
                conn.execute(
                    text('''UPDATE api_presets SET name=:name, provider_name=:provider_name,
                         endpoint=:endpoint, api_key=:api_key, model=:model,
                         temperature=:temperature, max_tokens=:max_tokens WHERE id=:id'''),
                    params
                )
            else:
                conn.execute(
                    text('''INSERT INTO api_presets
                         (id, name, provider_name, endpoint, api_key, model, temperature, max_tokens)
                         VALUES (:id, :name, :provider_name, :endpoint, :api_key, :model, :temperature, :max_tokens)'''),
                    params
                )
    if 'api_presets' in st.session_state:
        st.session_state.api_presets = df_to_save.copy()

# --- Funzioni esistenti (accorciate per brevità, nessuna modifica qui) --- 

def load_questions():
    """Carica le domande dal database."""
    try:
        df = pd.read_sql("SELECT * FROM questions", get_engine())
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
    except Exception as e:
        st.error(f"Errore durante la lettura della tabella questions: {e}")
    return pd.DataFrame({'id': pd.Series(dtype='str'), 'domanda': pd.Series(dtype='str'), 'risposta_attesa': pd.Series(dtype='str'), 'categoria': pd.Series(dtype='str')})

def save_questions(questions_df):
    """Sincronizza le domande con il database usando INSERT/UPDATE/DELETE."""
    expected_columns = ['id', 'domanda', 'risposta_attesa', 'categoria']
    df_to_save = pd.DataFrame(columns=expected_columns)
    for col in expected_columns:
        if col in questions_df.columns:
            df_to_save[col] = questions_df[col].astype(str)
        else:
            df_to_save[col] = pd.Series(dtype='str')
    engine = get_engine()
    with engine.begin() as conn:
        existing = pd.read_sql('SELECT id FROM questions', conn)
        existing_ids = existing['id'].astype(str).tolist()
        incoming_ids = df_to_save['id'].astype(str).tolist()

        ids_to_delete = set(existing_ids) - set(incoming_ids)
        for qid in ids_to_delete:
            conn.execute(text('DELETE FROM questions WHERE id = :id'), {'id': qid})

        for _, row in df_to_save.iterrows():
            params = row.to_dict()
            if row['id'] in existing_ids:
                conn.execute(
                    text('''UPDATE questions SET domanda=:domanda, risposta_attesa=:risposta_attesa,
                         categoria=:categoria WHERE id=:id'''),
                    params
                )
            else:
                conn.execute(
                    text('''INSERT INTO questions (id, domanda, risposta_attesa, categoria)
                         VALUES (:id, :domanda, :risposta_attesa, :categoria)'''),
                    params
                )
    st.session_state.questions = df_to_save.copy()
def load_question_sets():
    """Carica i set di domande dal database insieme alle associazioni."""
    try:
        engine = get_engine()
        sets_df = pd.read_sql("SELECT id, name FROM question_sets", engine)
        rel_df = pd.read_sql("SELECT set_id, question_id FROM question_set_questions", engine)

        if sets_df.empty:
            return pd.DataFrame({'id': pd.Series(dtype='str'), 'name': pd.Series(dtype='str'), 'questions': pd.Series(dtype='object')})

        sets_df['id'] = sets_df['id'].astype(str)
        sets_df['name'] = sets_df['name'].astype(str).fillna("")
        rel_df['set_id'] = rel_df['set_id'].astype(str)
        rel_df['question_id'] = rel_df['question_id'].astype(str)

        sets_df['questions'] = sets_df['id'].apply(lambda sid: rel_df[rel_df['set_id'] == sid]['question_id'].tolist())
        return sets_df
    except Exception as e:
        st.error(f"Errore durante la lettura della tabella question_sets: {e}")
    return pd.DataFrame({'id': pd.Series(dtype='str'), 'name': pd.Series(dtype='str'), 'questions': pd.Series(dtype='object')})

def save_question_sets(sets_df):
    """Sincronizza i set di domande con il database e le relative associazioni."""
    sets_df_to_save = sets_df.copy()
    engine = get_engine()
    with engine.begin() as conn:
        existing = pd.read_sql('SELECT id FROM question_sets', conn)
        existing_ids = existing['id'].astype(str).tolist()
        incoming_ids = sets_df_to_save['id'].astype(str).tolist()

        ids_to_delete = set(existing_ids) - set(incoming_ids)
        for sid in ids_to_delete:
            conn.execute(text('DELETE FROM question_set_questions WHERE set_id = :id'), {'id': sid})
            conn.execute(text('DELETE FROM question_sets WHERE id = :id'), {'id': sid})

        for _, row in sets_df_to_save.iterrows():
            set_id = str(row['id'])
            name = str(row.get('name', ''))
            questions = row.get('questions', [])
            if set_id in existing_ids:
                conn.execute(text('UPDATE question_sets SET name=:name WHERE id=:id'), {'id': set_id, 'name': name})
            else:
                conn.execute(text('INSERT INTO question_sets (id, name) VALUES (:id, :name)'), {'id': set_id, 'name': name})

            if questions is not None:
                existing_q = conn.execute(text('SELECT question_id FROM question_set_questions WHERE set_id=:sid'), {'sid': set_id}).fetchall()
                existing_q_ids = [r[0] for r in existing_q]
                new_q_ids = [str(q) for q in questions]

                for qid in set(existing_q_ids) - set(new_q_ids):
                    conn.execute(text('DELETE FROM question_set_questions WHERE set_id=:sid AND question_id=:qid'), {'sid': set_id, 'qid': qid})
                for qid in set(new_q_ids) - set(existing_q_ids):
                    conn.execute(text('INSERT INTO question_set_questions (set_id, question_id) VALUES (:sid, :qid)'), {'sid': set_id, 'qid': qid})

    st.session_state.question_sets = sets_df.copy()

def load_results():
    """Carica i risultati dei test dal database."""
    try:
        results_df = pd.read_sql("SELECT * FROM test_results", get_engine())
        if not results_df.empty and 'results' in results_df.columns:
            results_df['results'] = results_df['results'].apply(lambda x: json.loads(x) if isinstance(x, str) and x.startswith('{') else ({} if pd.isna(x) else x))
        else:
            results_df = pd.DataFrame({'id': pd.Series(dtype='str'), 'set_id': pd.Series(dtype='str'), 'timestamp': pd.Series(dtype='str'), 'results': pd.Series(dtype='object')})
        results_df['id'] = results_df['id'].astype(str)
        results_df['set_id'] = results_df['set_id'].astype(str).fillna("")
        results_df['timestamp'] = results_df['timestamp'].astype(str).fillna("")
        results_df['results'] = results_df['results'].apply(lambda x: x if isinstance(x, dict) else {})
        return results_df
    except Exception as e:
        st.error(f"Errore durante la lettura della tabella test_results: {e}")
    return pd.DataFrame({'id': pd.Series(dtype='str'), 'set_id': pd.Series(dtype='str'), 'timestamp': pd.Series(dtype='str'), 'results': pd.Series(dtype='object')})

def save_results(results_df):
    """Sincronizza i risultati dei test con il database."""
    results_df_to_save = results_df.copy()
    if not results_df_to_save.empty and 'results' in results_df_to_save.columns:
        results_df_to_save['results'] = results_df_to_save['results'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else "{}")
    engine = get_engine()
    with engine.begin() as conn:
        existing = pd.read_sql('SELECT id FROM test_results', conn)
        existing_ids = existing['id'].astype(str).tolist()
        incoming_ids = results_df_to_save['id'].astype(str).tolist()

        ids_to_delete = set(existing_ids) - set(incoming_ids)
        for rid in ids_to_delete:
            conn.execute(text('DELETE FROM test_results WHERE id = :id'), {'id': rid})

        for _, row in results_df_to_save.iterrows():
            params = row.to_dict()
            if row['id'] in existing_ids:
                conn.execute(
                    text('''UPDATE test_results SET set_id=:set_id, timestamp=:timestamp, results=:results WHERE id=:id'''),
                    params
                )
            else:
                conn.execute(
                    text('''INSERT INTO test_results (id, set_id, timestamp, results) VALUES (:id, :set_id, :timestamp, :results)'''),
                    params
                )
    st.session_state.results = results_df.copy()

def add_question(testo_domanda, risposta_prevista, categoria="", question_id=None):
    """Inserisce una nuova domanda nel database."""
    if 'questions' not in st.session_state:
        st.session_state.questions = load_questions()

    new_id = question_id or str(uuid.uuid4())
    new_question_data = {
        'id': new_id,
        'domanda': str(testo_domanda),
        'risposta_attesa': str(risposta_prevista),
        'categoria': str(categoria)
    }

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text('''INSERT INTO questions (id, domanda, risposta_attesa, categoria)
                 VALUES (:id, :domanda, :risposta_attesa, :categoria)'''),
            new_question_data
        )

    new_df = pd.DataFrame([new_question_data])
    st.session_state.questions = pd.concat([st.session_state.questions, new_df], ignore_index=True)
    return new_id

def update_question(question_id, testo_domanda=None, risposta_prevista=None, categoria=None):
    """Aggiorna i campi di una domanda nel database."""
    if 'questions' not in st.session_state:
        st.session_state.questions = load_questions()

    questions_df = st.session_state.questions.copy()
    idx = questions_df.index[questions_df['id'] == str(question_id)].tolist()
    if not idx:
        return False

    updates = []
    params = {'id': str(question_id)}
    if testo_domanda is not None:
        questions_df.at[idx[0], 'domanda'] = str(testo_domanda)
        updates.append('domanda = :domanda')
        params['domanda'] = str(testo_domanda)
    if risposta_prevista is not None:
        questions_df.at[idx[0], 'risposta_attesa'] = str(risposta_prevista)
        updates.append('risposta_attesa = :risposta_attesa')
        params['risposta_attesa'] = str(risposta_prevista)
    if categoria is not None:
        questions_df.at[idx[0], 'categoria'] = str(categoria)
        updates.append('categoria = :categoria')
        params['categoria'] = str(categoria)

    if updates:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text(f"UPDATE questions SET {', '.join(updates)} WHERE id = :id"),
                params
            )
        st.session_state.questions = questions_df
    return True

def delete_question(question_id):
    """Elimina una domanda dal database usando il suo ID."""
    if 'questions' not in st.session_state:
        st.session_state.questions = load_questions()

    questions_df = st.session_state.questions.copy()
    questions_df = questions_df[questions_df['id'] != str(question_id)]

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM questions WHERE id = :id'), {'id': str(question_id)})

    st.session_state.questions = questions_df
    update_sets_after_question_deletion(str(question_id))

def update_sets_after_question_deletion(question_id):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM question_set_questions WHERE question_id = :qid'), {'qid': str(question_id)})
    st.session_state.question_sets = load_question_sets()

def create_question_set(name, question_ids=None):
    """Crea un nuovo set di domande inserendolo nel database."""
    if 'question_sets' not in st.session_state:
        st.session_state.question_sets = load_question_sets()

    new_set_id = str(uuid.uuid4())
    new_set_data = {
        'id': new_set_id,
        'name': str(name),
        'questions': [str(qid) for qid in question_ids] if question_ids else []
    }

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text('INSERT INTO question_sets (id, name) VALUES (:id, :name)'),
            {'id': new_set_id, 'name': new_set_data['name']}
        )
        for qid in new_set_data['questions']:
            conn.execute(
                text('INSERT INTO question_set_questions (set_id, question_id) VALUES (:sid, :qid)'),
                {'sid': new_set_id, 'qid': qid}
            )

    new_df = pd.DataFrame([new_set_data])
    st.session_state.question_sets = pd.concat([st.session_state.question_sets, new_df], ignore_index=True)
    return new_set_id

def update_question_set(set_id, name=None, question_ids=None):
    """Aggiorna un set di domande nel database."""
    if 'question_sets' not in st.session_state:
        st.session_state.question_sets = load_question_sets()

    sets_df = st.session_state.question_sets.copy()
    idx = sets_df.index[sets_df['id'] == str(set_id)].tolist()
    if not idx:
        return False

    engine = get_engine()
    with engine.begin() as conn:
        if name is not None:
            sets_df.at[idx[0], 'name'] = str(name)
            conn.execute(text('UPDATE question_sets SET name=:name WHERE id=:id'), {'id': str(set_id), 'name': str(name)})

        if question_ids is not None:
            new_ids = [str(qid) for qid in question_ids]
            sets_df.at[idx[0], 'questions'] = new_ids
            existing_q = conn.execute(text('SELECT question_id FROM question_set_questions WHERE set_id=:sid'), {'sid': str(set_id)}).fetchall()
            existing_q_ids = [r[0] for r in existing_q]
            for qid in set(existing_q_ids) - set(new_ids):
                conn.execute(text('DELETE FROM question_set_questions WHERE set_id=:sid AND question_id=:qid'), {'sid': str(set_id), 'qid': qid})
            for qid in set(new_ids) - set(existing_q_ids):
                conn.execute(text('INSERT INTO question_set_questions (set_id, question_id) VALUES (:sid, :qid)'), {'sid': str(set_id), 'qid': qid})

    st.session_state.question_sets = sets_df
    return True


def add_question_set(name, question_ids=None):
    """
    Aggiunge un nuovo set di domande.

    Args:
        name: Nome del nuovo set di domande
        question_ids: Lista opzionale di ID delle domande da includere nel set

    Returns:
        L'ID del nuovo set di domande creato
    """
    return create_question_set(name, question_ids)



def delete_question_set(set_id):
    """Elimina un set di domande dal database."""
    if 'question_sets' not in st.session_state:
        st.session_state.question_sets = load_question_sets()

    sets_df = st.session_state.question_sets.copy()
    sets_df = sets_df[sets_df['id'] != str(set_id)]

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM question_set_questions WHERE set_id = :id'), {'id': str(set_id)})
        conn.execute(text('DELETE FROM question_sets WHERE id = :id'), {'id': str(set_id)})

    st.session_state.question_sets = sets_df

def add_test_result(set_id, results_data):
    """Aggiunge un risultato di test nel database."""
    if 'results' not in st.session_state:
        st.session_state.results = load_results()

    new_id = str(uuid.uuid4())
    new_result_data = {
        'id': new_id,
        'set_id': str(set_id),
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'results': results_data if isinstance(results_data, dict) else {}
    }

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text('''INSERT INTO test_results (id, set_id, timestamp, results) VALUES (:id, :set_id, :timestamp, :results)'''),
            {'id': new_id, 'set_id': new_result_data['set_id'], 'timestamp': new_result_data['timestamp'], 'results': json.dumps(new_result_data['results'])}
        )

    new_df = pd.DataFrame([new_result_data])
    st.session_state.results = pd.concat([st.session_state.results, new_df], ignore_index=True)
    return new_id

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
        added_count = 0
        for _, row in final_imported_df.iterrows():
            add_question(row['domanda'], row['risposta_attesa'], row['categoria'], question_id=row['id'])
            added_count += 1
        return True, f"Importate con successo {added_count} domande."
    except Exception as e:
        return False, f"Errore durante l'importazione delle domande: {str(e)}"

def add_question_if_not_exists(question_id: str, testo_domanda: str, risposta_prevista: str, categoria: str = ""):
    """
    Aggiunge una domanda al DataFrame delle domande se un ID specificato non esiste già.
    Restituisce True se la domanda è stata aggiunta, False se esisteva già.
    """
    # Assicurati che 'questions' sia in session_state e sia un DataFrame
    if 'questions' not in st.session_state or not isinstance(st.session_state.questions, pd.DataFrame):
        st.session_state.questions = load_questions() # Carica se non presente

    questions_df = st.session_state.questions.copy()

    if str(question_id) in questions_df['id'].astype(str).values:
        return False
    add_question(testo_domanda, risposta_prevista, categoria, question_id=str(question_id))
    return True
