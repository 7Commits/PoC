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
tabs = st.tabs(["Visualizza & Modifica Set", "Crea Nuovo Set"])


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

                    question_options_checkboxes = {}
                    if current_question_ids_in_set:
                        for q_id in current_question_ids_in_set:
                            q_text = get_question_text(str(q_id))
                            q_cat = get_question_category(str(q_id), questions_df) if questions_ready else 'N/A'
                            display_text = f"{q_text} (Categoria: {q_cat})"
                            question_options_checkboxes[str(q_id)] = st.checkbox(
                                display_text,
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
                                q_id: f"{q_text} (Cat: {get_question_category(q_id, questions_df)})" for q_id, q_text in
                                zip(available_questions_df['id'].astype(str), available_questions_df['domanda'])
                            }
                            newly_selected_questions_ids = st.multiselect(
                                "Seleziona domande da aggiungere",
                                options=list(question_dict_for_multiselect.keys()),
                                format_func=lambda x: question_dict_for_multiselect.get(x, x),
                                key=f"add_q_{row['id']}"
                            )
                        else:
                            st.info("Nessuna altra domanda disponibile da aggiungere.")
                    else:
                        st.info("Le domande non sono disponibili per la selezione (dati mancanti o incompleti).")

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

