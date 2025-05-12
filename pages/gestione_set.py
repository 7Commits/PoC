import streamlit as st
import pandas as pd
import sys
import os

# Aggiungi la directory genitore al percorso in modo da poter importare da utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_utils import (
    load_questions, load_question_sets, save_question_sets,
    create_question_set, update_question_set, delete_question_set
)
from utils.ui_utils import add_page_header, add_section_title, create_card, create_metrics_container

# Inizializza le variabili di stato della sessione se non esistono
# Questo è cruciale per evitare AttributeError
if 'questions' not in st.session_state:
    st.session_state.questions = load_questions()
if 'question_sets' not in st.session_state:
    st.session_state.question_sets = load_question_sets()

# Aggiungi un'intestazione stilizzata
add_page_header(
    "Gestione Set di Domande",
    icon="📚",
    description="Organizza le tue domande in set per test e valutazioni"
)

# Schede per diverse funzioni di gestione dei set
tabs = st.tabs(["Visualizza & Modifica Set", "Crea Nuovo Set"])


# Funzione per ottenere il testo della domanda tramite ID
def get_question_text(question_id):
    if 'questions' in st.session_state and not st.session_state.questions.empty:
        # Assicurati che la colonna 'domanda' esista
        if 'domanda' not in st.session_state.questions.columns:
            # Potrebbe essere necessario ricaricare o gestire questo caso se 'domanda' non è garantita
            # st.warning("La colonna 'domanda' non è presente nei dati delle domande caricate.")
            # Per ora, proviamo a caricare di nuovo se manca, anche se l'inizializzazione sopra dovrebbe gestirlo.
            st.session_state.questions = load_questions()
            if 'domanda' not in st.session_state.questions.columns:
                return f"ID Domanda: {question_id} (colonna 'domanda' mancante dopo ricarica)"

        question_row = st.session_state.questions[st.session_state.questions['id'] == str(question_id)]
        if not question_row.empty:
            return question_row.iloc[0]['domanda']
    return f"ID Domanda: {question_id} (non trovata o dati domande non caricati)"


# Scheda Visualizza e Modifica Set
with tabs[0]:
    st.header("Visualizza e Modifica Set di Domande")

    # Verifica che 'question_sets' e 'questions' (con colonna 'domanda') siano inizializzati
    questions_ready = 'questions' in st.session_state and not st.session_state.questions.empty and 'domanda' in st.session_state.questions.columns
    sets_ready = 'question_sets' in st.session_state  # Non è necessario che non sia vuoto per visualizzare il messaggio "Nessun set"

    if sets_ready and not st.session_state.question_sets.empty:
        if not questions_ready:
            st.warning(
                "Dati delle domande non completamente caricati o colonna 'domanda' mancante. Alcune funzionalità potrebbero essere limitate. Vai a 'Gestione Domande'.")

        for idx, row in st.session_state.question_sets.iterrows():
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

                    question_options_checkboxes = {}
                    if current_question_ids_in_set:
                        for q_id in current_question_ids_in_set:
                            question_text = get_question_text(
                                str(q_id)) if questions_ready else f"ID: {q_id} (testo non disponibile)"
                            question_options_checkboxes[str(q_id)] = st.checkbox(
                                question_text,
                                value=True,
                                key=f"qcheck_{row['id']}_{q_id}"
                            )
                    else:
                        st.info("Nessuna domanda in questo set.")

                    st.subheader("Aggiungi Domande al Set")

                    newly_selected_questions_ids = []
                    if questions_ready:
                        all_questions_df = st.session_state.questions
                        available_questions_df = all_questions_df[
                            ~all_questions_df['id'].astype(str).isin(
                                [str(q_id) for q_id in current_question_ids_in_set])
                        ]

                        if not available_questions_df.empty:
                            question_dict_for_multiselect = {
                                q_id: q_text for q_id, q_text in
                                zip(available_questions_df['id'].astype(str), available_questions_df['domanda'])
                            }

                            newly_selected_questions_ids = st.multiselect(
                                "Seleziona domande da aggiungere",
                                options=list(question_dict_for_multiselect.keys()),
                                format_func=lambda x: question_dict_for_multiselect.get(x, x),
                                # Fallback a ID se testo non trovato
                                key=f"add_q_{row['id']}"
                            )
                        else:
                            st.info("Nessuna altra domanda disponibile da aggiungere.")
                    else:
                        st.info("Le domande non sono disponibili per la selezione.")

                with col2:
                    if st.button("Salva Modifiche", key=f"save_set_{row['id']}"):
                        kept_questions_ids = [q_id for q_id, keep in question_options_checkboxes.items() if keep]

                        updated_questions_ids = list(
                            set(kept_questions_ids + [str(q_id) for q_id in newly_selected_questions_ids]))

                        if update_question_set(row['id'], edited_name, updated_questions_ids):
                            st.success("Set di domande aggiornato con successo!")
                            st.rerun()
                        else:
                            st.error("Impossibile aggiornare il set di domande.")

                    if st.button("Elimina Set", key=f"delete_set_{row['id']}"):
                        delete_question_set(row['id'])
                        st.success("Set di domande eliminato con successo!")
                        st.rerun()
    elif not sets_ready or st.session_state.question_sets.empty:
        st.info("Nessun set di domande disponibile. Crea un nuovo set utilizzando la scheda 'Crea Nuovo Set'.")
    elif not questions_ready:  # Questo caso è per quando i set esistono ma le domande no.
        st.warning("Dati dei set caricati, ma dati delle domande non pronti. Vai a 'Gestione Domande'.")

# Scheda Crea Nuovo Set
with tabs[1]:
    st.header("Crea Nuovo Set di Domande")

    with st.form("create_set_form"):
        set_name = st.text_input("Nome Set", placeholder="Inserisci un nome per il set...")

        selected_qs_for_new_set = []
        questions_ready_for_creation = 'questions' in st.session_state and \
                                       not st.session_state.questions.empty and \
                                       'domanda' in st.session_state.questions.columns

        if questions_ready_for_creation:
            all_questions_df = st.session_state.questions
            question_dict_for_creation = {
                q_id: q_text for q_id, q_text in
                zip(all_questions_df['id'].astype(str), all_questions_df['domanda'])
            }

            selected_qs_for_new_set = st.multiselect(
                "Seleziona domande per questo set",
                options=list(question_dict_for_creation.keys()),
                format_func=lambda x: question_dict_for_creation.get(x, x)  # Fallback a ID
            )
        else:
            st.info(
                "Nessuna domanda disponibile o dati delle domande non pronti. Vai a 'Gestione Domande' per aggiungere/caricare domande.")

        submitted = st.form_submit_button("Crea Set")

        if submitted:
            if set_name:
                set_id = create_question_set(set_name, [str(q_id) for q_id in selected_qs_for_new_set])
                st.success(f"Set di domande creato con successo con ID: {set_id}")
                st.rerun()
            else:
                st.error("Il nome del set è obbligatorio.")