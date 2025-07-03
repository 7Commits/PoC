import streamlit as st
import pandas as pd
import sys
import os
import json

# Aggiungi la directory genitore al percorso in modo da poter importare da utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_utils import (
    load_questions, add_question, update_question,
    delete_question, import_questions_from_file
)
from utils.ui_utils import add_page_header, add_section_title, create_card


# === FUNZIONI DI CALLBACK ===

def save_question_callback(question_id, edited_question, edited_answer, edited_category):
    """Funzione di callback: salva le modifiche alla domanda"""
    if update_question(question_id, testo_domanda=edited_question, risposta_prevista=edited_answer,
                       categoria=edited_category):
        st.session_state.save_success_message = "Domanda aggiornata con successo!"
        st.session_state.save_success = True
        # Aggiorna le domande in session_state per riflettere la modifica
        st.session_state.questions.loc[st.session_state.questions['id'] == question_id, 'categoria'] = edited_category
        st.session_state.trigger_rerun = True
    else:
        st.session_state.save_error_message = "Impossibile aggiornare la domanda."
        st.session_state.save_error = True


def delete_question_callback(question_id):
    """Funzione di callback: elimina la domanda"""
    delete_question(question_id)
    st.session_state.delete_success_message = "Domanda eliminata con successo!"
    st.session_state.delete_success = True
    st.session_state.trigger_rerun = True


def import_questions_callback():
    """Funzione di callback: importa le domande"""
    if 'uploaded_file_content' in st.session_state and st.session_state.uploaded_file_content is not None:
        success, message = import_questions_from_file(st.session_state.uploaded_file_content)

        if success:
            st.session_state.import_success_message = message
            st.session_state.import_success = True
            st.session_state.trigger_rerun = True
        else:
            st.session_state.import_error_message = message
            st.session_state.import_error = True


# === FUNZIONI DI DIALOGO ===

@st.dialog("Conferma Eliminazione")
def confirm_delete_question_dialog(question_id, question_text):
    """Dialogo di conferma per l'eliminazione della domanda"""
    st.write(f"Sei sicuro di voler eliminare questa domanda?")
    st.write(f"**Domanda:** {question_text[:100]}...")
    st.warning("Questa azione non può essere annullata.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Sì, Elimina", type="primary", use_container_width=True):
            delete_question_callback(question_id)
            st.rerun()

    with col2:
        if st.button("No, Annulla", use_container_width=True):
            st.rerun()


# === Inizializzazione delle variabili di stato ===
if 'save_success' not in st.session_state:
    st.session_state.save_success = False
if 'save_error' not in st.session_state:
    st.session_state.save_error = False
if 'delete_success' not in st.session_state:
    st.session_state.delete_success = False
if 'import_success' not in st.session_state:
    st.session_state.import_success = False
if 'import_error' not in st.session_state:
    st.session_state.import_error = False
if 'trigger_rerun' not in st.session_state:
    st.session_state.trigger_rerun = False

# Gestisce la logica di rerun
if st.session_state.trigger_rerun:
    st.session_state.trigger_rerun = False
    st.rerun()

# Mostra i messaggi di stato
if st.session_state.save_success:
    st.success(st.session_state.get('save_success_message', 'Operazione completata con successo!'))
    st.session_state.save_success = False

if st.session_state.save_error:
    st.error(st.session_state.get('save_error_message', 'Si è verificato un errore.'))
    st.session_state.save_error = False

if st.session_state.delete_success:
    st.success(st.session_state.get('delete_success_message', 'Eliminazione completata con successo!'))
    st.session_state.delete_success = False

if st.session_state.import_success:
    st.success(st.session_state.get('import_success_message', 'Importazione completata con successo!'))
    st.session_state.import_success = False

if st.session_state.import_error:
    st.error(st.session_state.get('import_error_message', 'Errore durante l\'importazione.'))
    st.session_state.import_error = False

# Aggiungi un'intestazione stilizzata
add_page_header(
    "Gestione Domande",
    icon="📋",
    description="Crea, modifica e gestisci le tue domande, le risposte attese e le categorie."
)

# Scheda per diverse funzioni di gestione delle domande
tabs = st.tabs(["Visualizza & Modifica Domande", "Aggiungi Domande", "Importa da File"])

# Scheda Visualizza e Modifica Domande
with tabs[0]:
    st.header("Visualizza e Modifica Domande")

    if 'questions' in st.session_state and not st.session_state.questions.empty:
        questions_df = st.session_state.questions
        # Assicurati che la colonna 'categoria' esista, altrimenti aggiungila con valori vuoti
        if 'categoria' not in questions_df.columns:
            questions_df['categoria'] = ""
        else:
            # Riempi i valori NaN o None nella colonna 'categoria' con una stringa vuota o 'N/A'
            # per assicurare che il filtro funzioni correttamente e per la visualizzazione.
            questions_df['categoria'] = questions_df['categoria'].fillna('N/A')

        # Ottieni le categorie uniche per il filtro, includendo un'opzione per mostrare tutto
        # Converti esplicitamente in stringa per evitare problemi con tipi misti e aggiungi 'Tutte le categorie'
        unique_categories = sorted(list(questions_df['categoria'].astype(str).unique()))
        unique_categories.insert(0, "Tutte le categorie")

        # Crea il selettore per la categoria
        selected_category = st.selectbox(
            "Filtra per categoria:",
            options=unique_categories,
            index=0  # Imposta "Tutte le categorie" come predefinito
        )

        # Filtra il DataFrame in base alla categoria selezionata
        if selected_category == "Tutte le categorie":
            filtered_questions_df = questions_df
        else:
            filtered_questions_df = questions_df[questions_df['categoria'] == selected_category]

        if not filtered_questions_df.empty:
            for idx, row in filtered_questions_df.iterrows():
                # Usa .get('categoria', 'N/A') per una gestione sicura se 'categoria' non fosse presente o fosse NaN dopo il filtro
                # Anche se abbiamo gestito i NaN prima, è una buona pratica per la robustezza.
                category_display = row.get('categoria', 'N/A') if pd.notna(row.get('categoria')) else 'N/A'
                with st.expander(f"Domanda: {row['domanda'][:100]}... (Categoria: {category_display})"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        edited_question = st.text_area(
                            f"Modifica Domanda {idx + 1}",
                            value=row['domanda'],
                            key=f"q_edit_{row['id']}"
                        )

                        edited_answer = st.text_area(
                            f"Modifica Risposta Attesa {idx + 1}",
                            value=row['risposta_attesa'],
                            key=f"a_edit_{row['id']}"
                        )

                        edited_category_value = row.get('categoria', '')
                        edited_category = st.text_input(
                            f"Modifica Categoria {idx + 1}",
                            value=edited_category_value,
                            key=f"c_edit_{row['id']}"
                        )

                    with col2:
                        # Pulsante Aggiorna con callback
                        st.button(
                            "Salva Modifiche",
                            key=f"save_{row['id']}",
                            on_click=save_question_callback,
                            args=(row['id'], edited_question, edited_answer, edited_category)
                        )

                        # Pulsante Elimina con dialog di conferma
                        if st.button(
                                "Elimina Domanda",
                                key=f"delete_{row['id']}",
                                type="secondary"
                        ):
                            confirm_delete_question_dialog(row['id'], row['domanda'])
        else:
            st.info(f"Nessuna domanda trovata per la categoria '{selected_category}'.")

    else:
        st.info("Nessuna domanda disponibile. Aggiungi domande utilizzando la scheda 'Aggiungi Domande'.")

# Scheda Aggiungi Domande
with tabs[1]:
    st.header("Aggiungi Nuova Domanda")

    with st.form("add_question_form"):
        domanda = st.text_area("Domanda", placeholder="Inserisci qui la domanda...")
        risposta_attesa = st.text_area("Risposta Attesa", placeholder="Inserisci qui la risposta attesa...")
        categoria = st.text_input("Categoria (opzionale)", placeholder="Inserisci qui la categoria...")

        submitted = st.form_submit_button("Aggiungi Domanda")

        if submitted:
            if domanda and risposta_attesa:
                # Passa la categoria, che può essere una stringa vuota se non inserita
                question_id = add_question(testo_domanda=domanda, risposta_prevista=risposta_attesa,
                                           categoria=categoria)
                st.success(f"Domanda aggiunta con successo con ID: {question_id}")
                st.rerun()
            else:
                st.error("Sono necessarie sia la domanda che la risposta attesa.")

# Scheda Importa da File
with tabs[2]:
    st.header("Importa Domande da File")

    st.write("""
    Carica un file CSV o JSON contenente domande, risposte attese e categorie (opzionale).

    ### Formato File:
    - **CSV**: Deve includere le colonne 'domanda' e 'risposta_attesa'. Può includere opzionalmente 'categoria'.
      (Se usi i vecchi nomi 'question' e 'expected_answer', verranno convertiti automaticamente).
    - **JSON**: Deve contenere un array di oggetti con i campi 'domanda' e 'risposta_attesa'. Può includere opzionalmente 'categoria'.
      (Se usi i vecchi nomi 'question' e 'expected_answer', verranno convertiti automaticamente).

    ### Esempio CSV:
    ```csv
    domanda,risposta_attesa,categoria
    "Quanto fa 2+2?","4","Matematica Base"
    "Qual è la capitale della Francia?","Parigi","Geografia"
    "Chi ha scritto 'Amleto'?","William Shakespeare","Letteratura"
    ```

    ### Esempio JSON:
    ```json
    [
        {
            "domanda": "Quanto fa 2+2?",
            "risposta_attesa": "4",
            "categoria": "Matematica Base"
        },
        {
            "domanda": "Qual è la capitale della Francia?",
            "risposta_attesa": "Parigi",
            "categoria": "Geografia"
        },
        {
            "domanda": "Chi ha scritto 'Romeo e Giulietta'?",
            "risposta_attesa": "William Shakespeare" 
        }
    ]
    ```
    """)

    uploaded_file = st.file_uploader("Scegli un file", type=["csv", "json"])

    if uploaded_file is not None:
        # Salva il file in session_state per l'uso da parte della callback
        st.session_state.uploaded_file_content = uploaded_file

        # Pulsante che utilizza la funzione di callback
        st.button(
            "Importa Domande",
            key="import_questions_btn",
            on_click=import_questions_callback
        )
