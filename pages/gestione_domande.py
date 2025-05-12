import streamlit as st
import pandas as pd
import sys
import os
import json
from io import StringIO

# Aggiungi la directory genitore al percorso in modo da poter importare da utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_utils import (
    load_questions, save_questions, add_question, update_question,
    delete_question, import_questions_from_file
)
from utils.ui_utils import add_page_header, add_section_title, create_card, create_metrics_container

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

        for idx, row in questions_df.iterrows():
            with st.expander(f"Domanda: {row['domanda'][:100]}... (Categoria: {row.get('categoria', 'N/A')})"):
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

                    edited_category = st.text_input(
                        f"Modifica Categoria {idx + 1}",
                        value=row.get('categoria', ''),  # Usa .get per sicurezza se la colonna non fosse presente
                        key=f"c_edit_{row['id']}"
                    )

                with col2:
                    # Pulsante Aggiorna
                    if st.button("Salva Modifiche", key=f"save_{row['id']}"):
                        if update_question(row['id'], testo_domanda=edited_question, risposta_prevista=edited_answer,
                                           categoria=edited_category):
                            st.success("Domanda aggiornata con successo!")
                            st.rerun()
                        else:
                            st.error("Impossibile aggiornare la domanda.")

                    # Pulsante Elimina
                    if st.button("Elimina Domanda", key=f"delete_{row['id']}"):
                        delete_question(row['id'])
                        st.success("Domanda eliminata con successo!")
                        st.rerun()
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
        if st.button("Importa Domande"):
            success, message = import_questions_from_file(uploaded_file)

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)