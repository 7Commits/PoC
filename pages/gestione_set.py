import streamlit as st
import pandas as pd
import sys
import os
import json
import uuid # Assicurati che uuid sia importato se data_utils lo usa internamente e non lo esporta
# Importa le funzioni necessarie da data_utils
# Dovresti avere qualcosa come:
# from data_utils import add_question_if_not_exists, create_question_set, load_questions, load_question_sets
# Oppure:

# Aggiungi la directory genitore al percorso in modo da poter importare da utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_utils import (
    load_questions, load_question_sets,
    create_question_set, update_question_set, delete_question_set,
    import_questions_from_file, add_question_if_not_exists
)
from utils.ui_utils import add_page_header, add_section_title, create_card, create_metrics_container

# Assicurati che questa importazione sia presente all'inizio del file

import streamlit as st
# import pandas as pd # Se necessario

# === CALLBACK FUNCTIONS ===

def save_set_callback(set_id, edited_name, question_options_checkboxes, newly_selected_questions_ids):
    kept_questions_ids = [q_id for q_id, keep in question_options_checkboxes.items() if keep]
    updated_questions_ids = list(
        set(kept_questions_ids + [str(q_id) for q_id in newly_selected_questions_ids])
    )

    if update_question_set(set_id, edited_name, updated_questions_ids):
        st.session_state.save_set_success_message = "Set di domande aggiornato con successo!"
        st.session_state.save_set_success = True
        st.session_state.trigger_rerun = True
    else:
        st.session_state.save_set_error_message = "Impossibile aggiornare il set di domande."
        st.session_state.save_set_error = True


def delete_set_callback(set_id):
    delete_question_set(set_id)
    st.session_state.delete_set_success_message = "Set di domande eliminato con successo!"
    st.session_state.delete_set_success = True
    st.session_state.trigger_rerun = True


@st.dialog("Conferma Eliminazione")
def confirm_delete_set_dialog(set_id, set_name):
    """Dialog di conferma per l'eliminazione del set di domande"""
    st.write(f"Sei sicuro di voler eliminare il set '{set_name}'?")
    st.warning("Questa azione non può essere annullata.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Sì, Elimina", type="primary", use_container_width=True):
            delete_set_callback(set_id)
            st.rerun()
    
    with col2:
        if st.button("No, Annulla", use_container_width=True):
            st.rerun()

def import_set_callback():
    """
    Importa uno o più set di domande da un file JSON.
    Formato JSON atteso:
    [
        {
            "name": "Nome Set",
            "questions": [
                {
                    "id": "1",
                    "domanda": "Testo domanda",
                    "risposta_attesa": "Risposta",
                    "categoria": "Categoria" (opzionale)
                },
                ...
            ]
        },
        ...
    ]
    """
    # Inizializza i messaggi di stato
    st.session_state.import_set_success = False
    st.session_state.import_set_error = False
    st.session_state.import_set_success_message = ""
    st.session_state.import_set_error_message = ""

    if 'uploaded_file_content_set' in st.session_state and st.session_state.uploaded_file_content_set is not None:
        try:
            uploaded_file = st.session_state.uploaded_file_content_set
            string_data = uploaded_file.getvalue().decode("utf-8")
            data = json.loads(string_data)

            # Carica i dati attuali
            current_questions = load_questions()
            current_sets = load_question_sets()

            if not isinstance(data, list):
                st.session_state.import_set_error = True
                st.session_state.import_set_error_message = "Formato JSON non valido. Il file deve contenere una lista (array) di set."
                st.session_state.trigger_rerun = True
                return

            sets_imported_count = 0
            new_questions_added_count = 0
            existing_questions_found_count = 0

            for set_idx, set_data in enumerate(data):
                if not isinstance(set_data, dict):
                    st.warning(f"Elemento #{set_idx+1} nella lista non è un set valido (saltato).")
                    continue

                set_name = set_data.get("name")
                questions_in_set_data = set_data.get("questions", [])

                if not set_name or not isinstance(set_name, str) or not set_name.strip():
                    st.warning(f"Set #{set_idx+1} con nome mancante o non valido (saltato).")
                    continue
                
                if not isinstance(questions_in_set_data, list):
                    st.warning(f"Dati delle domande mancanti o non validi per il set '{set_name}' (saltato).")
                    continue

                # Controlla se esiste già un set con lo stesso nome
                if set_name in current_sets['name'].values:
                    st.warning(f"Un set con nome '{set_name}' esiste già. Saltato per evitare duplicati.")
                    continue

                current_set_question_ids = []
                
                # Elabora ogni domanda nel set
                for q_idx, q_data in enumerate(questions_in_set_data):
                    if not isinstance(q_data, dict):
                        st.warning(f"Dati domanda #{q_idx+1} nel set '{set_name}' non validi (saltati).")
                        continue

                    q_id = str(q_data.get("id", ""))
                    q_text = q_data.get("domanda", "")
                    q_answer = q_data.get("risposta_attesa", "")
                    q_category = q_data.get("categoria", "")

                    # Validazione dei campi obbligatori
                    if not q_id or not q_text or not q_answer:
                        st.warning(f"Domanda #{q_idx+1} nel set '{set_name}' ha campi mancanti (saltata). ID: {q_id}")
                        continue

                    # Controlla se la domanda esiste già nelle domande attuali
                    if q_id in current_questions['id'].astype(str).values:
                        existing_questions_found_count += 1
                        current_set_question_ids.append(q_id)
                        continue

                    # Aggiungi la nuova domanda se non esiste
                    try:
                        was_added = add_question_if_not_exists(
                            question_id=q_id,
                            testo_domanda=q_text,
                            risposta_prevista=q_answer,
                            categoria=q_category
                        )
                        if was_added:
                            new_questions_added_count += 1
                            current_set_question_ids.append(q_id)
                            # Aggiorna il DataFrame locale delle domande
                            new_row = pd.DataFrame({
                                'id': [q_id],
                                'domanda': [q_text],
                                'risposta_attesa': [q_answer],
                                'categoria': [q_category]
                            })
                            current_questions = pd.concat([current_questions, new_row], ignore_index=True)
                        else:
                            existing_questions_found_count += 1
                            current_set_question_ids.append(q_id)
                    except Exception as e:
                        st.error(f"Errore durante l'aggiunta della domanda ID {q_id} per il set '{set_name}': {e}")
                        continue

                # Crea il set se ha almeno un nome valido (può essere vuoto di domande)
                if current_set_question_ids or len(questions_in_set_data) == 0:
                    try:
                        create_question_set(set_name, current_set_question_ids)
                        sets_imported_count += 1
                    except Exception as e:
                        st.error(f"Errore durante la creazione del set '{set_name}': {e}")
                else:
                    st.warning(f"Il set '{set_name}' non è stato creato perché non conteneva domande valide.")

            # Aggiorna lo stato della sessione
            st.session_state.questions = load_questions()  # Ricarica per sincronizzare
            st.session_state.question_sets = load_question_sets()  # Ricarica per sincronizzare

            # Componi il messaggio di successo
            if sets_imported_count > 0 or new_questions_added_count > 0:
                success_parts = []
                if sets_imported_count > 0:
                    success_parts.append(f"{sets_imported_count} set importati")
                if new_questions_added_count > 0:
                    success_parts.append(f"{new_questions_added_count} nuove domande aggiunte")
                if existing_questions_found_count > 0:
                    success_parts.append(f"{existing_questions_found_count} domande esistenti referenziate")
                
                st.session_state.import_set_success = True
                st.session_state.import_set_success_message = ". ".join(success_parts) + "."
            else:
                st.session_state.import_set_error = True
                st.session_state.import_set_error_message = "Nessun set o domanda valida trovata nel file per l'importazione."

        except json.JSONDecodeError:
            st.session_state.import_set_error = True
            st.session_state.import_set_error_message = "Errore di decodifica JSON. Assicurati che il file sia un JSON valido."
        except Exception as e:
            st.session_state.import_set_error = True
            st.session_state.import_set_error_message = f"Errore imprevisto durante l'importazione: {str(e)}"
        finally:
            st.session_state.trigger_rerun = True
    else:
        st.session_state.import_set_error = True
        st.session_state.import_set_error_message = "Nessun file fornito per l'importazione."

if 'save_set_success' not in st.session_state:
    st.session_state.save_set_success = False
if 'save_set_error' not in st.session_state:
    st.session_state.save_set_error = False
if 'delete_set_success' not in st.session_state:
    st.session_state.delete_set_success = False
if 'import_set_success' not in st.session_state:
    st.session_state.import_set_success = False
if 'import_set_error' not in st.session_state:
    st.session_state.import_set_error = False
if 'trigger_rerun' not in st.session_state:
    st.session_state.trigger_rerun = False

if 'question_checkboxes' not in st.session_state:
    st.session_state.question_checkboxes = {}
if 'newly_selected_questions' not in st.session_state:
    st.session_state.newly_selected_questions = {}

if st.session_state.trigger_rerun:
    st.session_state.trigger_rerun = False
    st.rerun()

if st.session_state.save_set_success:
    st.success(st.session_state.get('save_set_success_message', 'Set aggiornato con successo!'))
    st.session_state.save_set_success = False

if st.session_state.save_set_error:
    st.error(st.session_state.get('save_set_error_message', 'Errore durante l\'aggiornamento del set.'))
    st.session_state.save_set_error = False

if st.session_state.delete_set_success:
    st.success(st.session_state.get('delete_set_success_message', 'Set eliminato con successo!'))
    st.session_state.delete_set_success = False

if st.session_state.import_set_success:
    st.success(st.session_state.get('import_set_success_message', 'Importazione completata con successo!'))
    st.session_state.import_set_success = False

if st.session_state.import_set_error:
    st.error(st.session_state.get('import_set_error_message', 'Errore durante l\'importazione.'))
    st.session_state.import_set_error = False

# Inizializza le variabili di stato della sessione se non esistono
if 'questions' not in st.session_state or st.session_state.questions.empty:
    st.session_state.questions = load_questions()
if 'question_sets' not in st.session_state:
    st.session_state.question_sets = load_question_sets()

# Assicurati che la colonna 'categoria' esista in questions_df e gestisci i NaN
if 'questions' in st.session_state and not st.session_state.questions.empty:
    questions_df_temp = st.session_state.questions
    if 'categoria' not in questions_df_temp.columns:
        questions_df_temp['categoria'] = 'N/A'  # Aggiungi colonna se mancante
    questions_df_temp['categoria'] = questions_df_temp['categoria'].fillna('N/A')  # Riempi NaN
    st.session_state.questions = questions_df_temp

# Aggiungi un'intestazione stilizzata
add_page_header(
    "Gestione Set di Domande",
    icon="📚",
    description="Organizza le tue domande in set per test e valutazioni"
)

# Schede per diverse funzioni di gestione dei set
tabs = st.tabs(["Visualizza & Modifica Set", "Crea Nuovo Set", "Importa Set da file"])


# Funzione per ottenere il testo della domanda tramite ID
def get_question_text(question_id):
    if 'questions' in st.session_state and not st.session_state.questions.empty:
        if 'domanda' not in st.session_state.questions.columns:
            st.session_state.questions = load_questions()  # Prova a ricaricare
            if 'domanda' not in st.session_state.questions.columns:
                return f"ID Domanda: {question_id} (colonna 'domanda' mancante)"

        question_row = st.session_state.questions[st.session_state.questions['id'] == str(question_id)]
        if not question_row.empty:
            return question_row.iloc[0]['domanda']
    return f"ID Domanda: {question_id} (non trovata o dati non caricati)"


# Funzione per ottenere la categoria di una domanda tramite ID
def get_question_category(question_id, questions_df):
    if questions_df is not None and not questions_df.empty and 'categoria' in questions_df.columns:
        question_row = questions_df[questions_df['id'] == str(question_id)]
        if not question_row.empty:
            return question_row.iloc[0]['categoria']
    return 'N/A'  # Ritorna 'N/A' se non trovata o colonna mancante


def create_save_set_callback(set_id):
    def callback():
        edited_name = st.session_state.get(f"set_name_{set_id}", "")
        question_options_checkboxes = st.session_state.question_checkboxes.get(set_id, {})
        newly_selected_questions_ids = st.session_state.newly_selected_questions.get(set_id, [])
        
        save_set_callback(set_id, edited_name, question_options_checkboxes, newly_selected_questions_ids)
    
    return callback


def create_delete_set_callback(set_id):
    def callback():
        delete_set_callback(set_id)
    
    return callback

# Scheda Visualizza e Modifica Set
with tabs[0]:
    st.header("Visualizza e Modifica Set di Domande")

    questions_ready = ('questions' in st.session_state and
                       not st.session_state.questions.empty and
                       'domanda' in st.session_state.questions.columns and
                       'categoria' in st.session_state.questions.columns)
    sets_ready = 'question_sets' in st.session_state

    if not questions_ready:
        st.warning(
            "Dati delle domande (incluse categorie) non completamente caricati. Alcune funzionalità potrebbero essere limitate. Vai a 'Gestione Domande'.")
        # Impedisci l'esecuzione del filtro se i dati delle domande non sono pronti
        unique_categories_for_filter = []
        selected_categories = []
    else:
        questions_df = st.session_state.questions
        # Ottieni categorie uniche per il filtro, escludendo 'N/A' se si preferisce non mostrarlo come opzione selezionabile
        # o gestendolo specificamente. Per ora, includiamo tutto.
        unique_categories_for_filter = sorted(list(questions_df['categoria'].astype(str).unique()))
        if not unique_categories_for_filter:
            st.info("Nessuna categoria definita nelle domande esistenti per poter filtrare.")

        selected_categories = st.multiselect(
            "Filtra per categorie (mostra i set che contengono almeno una domanda da OGNI categoria selezionata):",
            options=unique_categories_for_filter,
            default=[]
        )

    if sets_ready and not st.session_state.question_sets.empty:
        question_sets_df = st.session_state.question_sets
        display_sets_df = question_sets_df.copy()  # Inizia con tutti i set

        if selected_categories and questions_ready:  # Applica il filtro solo se categorie selezionate e dati pronti
            filtered_set_indices = []
            for idx, set_row in question_sets_df.iterrows():
                question_ids_in_set = set_row.get('questions', [])
                if not isinstance(question_ids_in_set, list):
                    question_ids_in_set = []

                if not question_ids_in_set:  # Se il set non ha domande, non può soddisfare il filtro
                    continue

                categories_present_in_set = set()
                for q_id in question_ids_in_set:
                    category = get_question_category(str(q_id), questions_df)
                    categories_present_in_set.add(category)

                # Verifica se il set contiene almeno una domanda da OGNI categoria selezionata
                if all(sel_cat in categories_present_in_set for sel_cat in selected_categories):
                    filtered_set_indices.append(idx)

            display_sets_df = question_sets_df.loc[filtered_set_indices]

        if display_sets_df.empty and selected_categories:
            st.info(
                f"Nessun set trovato che contenga domande da tutte le categorie selezionate: {', '.join(selected_categories)}.")
        elif display_sets_df.empty and not selected_categories:
            st.info("Nessun set di domande disponibile. Crea un nuovo set utilizzando la scheda 'Crea Nuovo Set'.")

        for idx, row in display_sets_df.iterrows():
            with st.expander(f"Set: {row['name']}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    edited_name = st.text_input(
                        f"Nome Set",
                        value=row['name'],
                        key=f"set_name_{row['id']}"
                    )

                    st.subheader("Domande in questo Set")
                    current_question_ids_in_set = row.get('questions', [])
                    if not isinstance(current_question_ids_in_set, list):
                        current_question_ids_in_set = []

                    if row['id'] not in st.session_state.question_checkboxes:
                        st.session_state.question_checkboxes[row['id']] = {}

                    if current_question_ids_in_set:
                        for q_id in current_question_ids_in_set:
                            q_text = get_question_text(str(q_id))
                            q_cat = get_question_category(str(q_id), questions_df) if questions_ready else 'N/A'
                            display_text = f"{q_text} (Categoria: {q_cat})"
                            
                            # 使用回调来更新checkbox状态
                            checkbox_value = st.checkbox(
                                display_text,
                                value=True,
                                key=f"qcheck_{row['id']}_{q_id}"
                            )
                            st.session_state.question_checkboxes[row['id']][str(q_id)] = checkbox_value
                    else:
                        st.info("Nessuna domanda in questo set.")

                    st.subheader("Aggiungi Domande al Set")
                    
                    # 初始化新选择的问题状态
                    if row['id'] not in st.session_state.newly_selected_questions:
                        st.session_state.newly_selected_questions[row['id']] = []

                    if questions_ready:
                        all_questions_df = st.session_state.questions
                        available_questions_df = all_questions_df[
                            ~all_questions_df['id'].astype(str).isin(
                                [str(q_id) for q_id in current_question_ids_in_set])
                        ]

                        if not available_questions_df.empty:
                            question_dict_for_multiselect = {
                                q_id: f"{q_text} (Cat: {get_question_category(q_id, questions_df)})" for q_id, q_text in
                                zip(available_questions_df['id'].astype(str), available_questions_df['domanda'])
                            }
                            newly_selected_questions_ids = st.multiselect(
                                "Seleziona domande da aggiungere",
                                options=list(question_dict_for_multiselect.keys()),
                                format_func=lambda x: question_dict_for_multiselect.get(x, x),
                                key=f"add_q_{row['id']}"
                            )
                            st.session_state.newly_selected_questions[row['id']] = newly_selected_questions_ids
                        else:
                            st.info("Nessuna altra domanda disponibile da aggiungere.")
                    else:
                        st.info("Le domande non sono disponibili per la selezione (dati mancanti o incompleti).")

                with col2:
                    st.button(
                        "Salva Modifiche", 
                        key=f"save_set_{row['id']}",
                        on_click=create_save_set_callback(row['id'])
                    )

                    # Pulsante Elimina con dialog di conferma
                    if st.button(
                        "Elimina Set", 
                        key=f"delete_set_{row['id']}",
                        type="secondary"
                    ):
                        confirm_delete_set_dialog(row['id'], row['name'])

    elif not sets_ready or (st.session_state.question_sets.empty and not selected_categories):
        st.info("Nessun set di domande disponibile. Crea un nuovo set utilizzando la scheda 'Crea Nuovo Set'.")

# Scheda Crea Nuovo Set
with tabs[1]:
    st.header("Crea Nuovo Set di Domande")

    with st.form("create_set_form"):
        set_name = st.text_input("Nome Set", placeholder="Inserisci un nome per il set...")

        selected_qs_for_new_set = []
        questions_ready_for_creation = ('questions' in st.session_state and
                                        not st.session_state.questions.empty and
                                        'domanda' in st.session_state.questions.columns and
                                        'categoria' in st.session_state.questions.columns)

        if questions_ready_for_creation:
            all_questions_df_creation = st.session_state.questions
            question_dict_for_creation = {
                q_id: f"{q_text} (Cat: {get_question_category(q_id, all_questions_df_creation)})" for q_id, q_text in
                zip(all_questions_df_creation['id'].astype(str), all_questions_df_creation['domanda'])
            }

            selected_qs_for_new_set = st.multiselect(
                "Seleziona domande per questo set",
                options=list(question_dict_for_creation.keys()),
                format_func=lambda x: question_dict_for_creation.get(x, x)
            )
        else:
            st.info(
                "Nessuna domanda disponibile o dati delle domande non pronti (incl. categorie). Vai a 'Gestione Domande' per aggiungere/caricare domande.")

        submitted = st.form_submit_button("Crea Set")

        if submitted:
            if set_name:
                set_id = create_question_set(set_name, [str(q_id) for q_id in selected_qs_for_new_set])
                st.success(f"Set di domande creato con successo con ID: {set_id}")
                st.rerun()
            else:
                st.error("Il nome del set è obbligatorio.")

# Scheda Importa da File
with tabs[2]:
    st.header("Importa Set da File")

    st.write("""
    Carica un file JSON contenente uno o più set di domande.

    ### Formato File JSON per Set Multipli:
    ```json
    [
        {
            "name": "Capitali",
            "questions": [
                {
                    "id": "1",
                    "domanda": "Qual è la capitale della Francia?",
                    "risposta_attesa": "Parigi",
                    "categoria": "Geografia"
                },
                {
                    "id": "2",
                    "domanda": "Qual è la capitale della Germania?",
                    "risposta_attesa": "Berlino",
                    "categoria": "Geografia"
                }
            ]
        },
        {
            "name": "Matematica Base",
            "questions": [
                {
                    "id": "3",
                    "domanda": "Quanto fa 2+2?",
                    "risposta_attesa": "4",
                    "categoria": "Matematica"
                },
                {
                    "id": "4",
                    "domanda": "Quanto fa 10*4?",
                    "risposta_attesa": "40",
                    "categoria": "Matematica"
                }
            ]
        }
    ]
    ```

    ### Note Importanti:
    - Se una domanda con lo stesso ID esiste già, non verrà aggiunta nuovamente
    - Se un set con lo stesso nome esiste già, verrà saltato
    - Solo le domande nuove verranno aggiunte al database
    - Le domande esistenti verranno referenziate nei nuovi set
    """)

    uploaded_file = st.file_uploader("Scegli un file JSON", type=["json"])

    if uploaded_file is not None:
        st.session_state.uploaded_file_content_set = uploaded_file
        st.button(
            "Importa Set",
            key="import_set_btn",
            on_click=import_set_callback
        )

# === DIALOG FUNCTIONS ===

