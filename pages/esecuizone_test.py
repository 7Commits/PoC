import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime

# Aggiungi la directory genitore al percorso in modo da poter importare da utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_utils import (
    load_questions, load_question_sets, add_test_result
)
from utils.openai_utils import get_openai_client, evaluate_answer
from utils.ui_utils import add_page_header, add_section_title, create_card, create_metrics_container

# Aggiungi un'intestazione stilizzata
add_page_header(
    "Esecuzione Test",
    icon="🧪",
    description="Esegui valutazioni automatiche sui tuoi set di domande"
)

# Controlla se ci sono set di domande disponibili
if 'question_sets' not in st.session_state or st.session_state.question_sets.empty:
    st.warning("Nessun set di domande disponibile. Crea dei set di domande prima di eseguire i test.") # "Nessun set di domande disponibile. Crea dei set di domande prima di eseguire i test."
    st.stop()

# Controlla se l'API OpenAI è configurata
if not st.session_state.get('api_key'):
    st.warning("La chiave API OpenAI non è configurata. Vai alla pagina Configurazione API per impostarla.") # "La chiave API OpenAI non è configurata. Vai alla pagina Configurazione API per impostarla."
    st.stop()

# Ottieni testo della domanda e risposta attesa per ID
def get_question_data(question_id):
    if 'questions' in st.session_state and not st.session_state.questions.empty:
        question_row = st.session_state.questions[st.session_state.questions['id'] == question_id]
        if not question_row.empty:
            return {
                'question': question_row.iloc[0]['question'],
                'expected_answer': question_row.iloc[0]['expected_answer']
            }
    return None

# Seleziona set di domande per il test
add_section_title("Seleziona Set di Domande", icon="📚") # "Seleziona Set di Domande"

# Crea una scheda per spiegare la selezione
create_card(
    "Selezione Set di Domande", # "Selezione Set di Domande"
    "Scegli un set di domande da valutare. Ogni set può contenere più domande che verranno valutate rispetto alle tue risposte attese.", # "Scegli un set di domande da valutare. Ogni set può contenere più domande che verranno valutate rispetto alle tue risposte attese."
    icon="ℹ️"
)

# Crea dropdown con i set disponibili
set_options = {}
if 'question_sets' in st.session_state and not st.session_state.question_sets.empty:
    for _, row in st.session_state.question_sets.iterrows():
        # Mostra solo i set che hanno domande
        if 'questions' in row and row['questions']:
            set_options[row['id']] = f"{row['name']} ({len(row['questions'])} domande)" # " domande)"

if not set_options:
    create_card(
        "Nessun Set di Domande Disponibile", # "Nessun Set di Domande Disponibile"
        "Crea set di domande con domande prima di eseguire i test. Vai alla pagina Gestione Set di Domande per creare i set.", # "Crea set di domande con domande prima di eseguire i test. Vai alla pagina Gestione Set di Domande per creare i set."
        is_warning=True,
        icon="⚠️"
    )
    st.stop()

selected_set_id = st.selectbox(
    "Seleziona un set di domande", # "Seleziona un set di domande"
    options=list(set_options.keys()),
    format_func=lambda x: set_options[x]
)

# Ottieni il set selezionato
selected_set = st.session_state.question_sets[st.session_state.question_sets['id'] == selected_set_id].iloc[0]
questions_in_set = selected_set['questions']

# Modalità test manuale vs valutazione automatica
add_section_title("Modalità Test", icon="🔄") # "Modalità Test"

# Schede che spiegano le diverse modalità in colonne
col1, col2 = st.columns(2)

with col1:
    create_card(
        "Modalità Inserimento Manuale", # "Modalità Inserimento Manuale"
        "Inserisci le tue risposte per ogni domanda nel set. Il sistema le valuterà rispetto alle risposte attese.", # "Inserisci le tue risposte per ogni domanda nel set. Il sistema le valuterà rispetto alle risposte attese."
        icon="✍️"
    )
    
with col2:
    create_card(
        "Modalità Automatica", # "Modalità Automatica"
        "Il sistema genera risposte di esempio (perfette, parziali o errate) e le valuta automaticamente.", # "Il sistema genera risposte di esempio (perfette, parziali o errate) e le valuta automaticamente."
        icon="🤖"
    )

# Selezione modalità test con pulsanti radio migliorati
test_mode = st.radio(
    "Seleziona modalità test", # "Seleziona modalità test"
    options=["Inserimento Manuale", "Valutazione Automatica con Risposte di Esempio"], # "Inserimento Manuale", "Valutazione Automatica con Risposte di Esempio"
    index=0
)

# Opzioni visibilità API
add_section_title("Opzioni API", icon="🔍") # "Opzioni API"
show_api_details = st.checkbox(
    "Mostra Dettagli Richiesta e Risposta API", # "Mostra Dettagli Richiesta e Risposta API"
    value=False,
    help="Abilita per vedere le chiamate API esatte effettuate al provider LLM" # "Abilita per vedere le chiamate API esatte effettuate al provider LLM"
)

if show_api_details:
    st.info("I dettagli della richiesta e della risposta API saranno inclusi nei risultati della valutazione.") # "I dettagli della richiesta e della risposta API saranno inclusi nei risultati della valutazione."

# Inizializza client OpenAI
client = get_openai_client()

if test_mode == "Inserimento Manuale": # "Inserimento Manuale"
    st.header("Modalità Test Manuale") # "Modalità Test Manuale"
    st.write("Inserisci le risposte a ogni domanda. Il sistema le valuterà rispetto alle risposte attese.") # "Inserisci le risposte a ogni domanda. Il sistema le valuterà rispetto alle risposte attese."
    
    # Modulo per inserire le risposte
    with st.form("manual_test_form"):
        answers = {}
        
        # Visualizza ogni domanda e raccogli le risposte
        for q_id in questions_in_set:
            q_data = get_question_data(q_id)
            if q_data:
                st.write(f"**Domanda:** {q_data['question']}") # "**Domanda:**"
                answer = st.text_area(f"La tua risposta per la domanda {q_id}", key=f"answer_{q_id}") # f"La tua risposta per la domanda {q_id}"
                answers[q_id] = answer
        
        submitted = st.form_submit_button("Invia Risposte per Valutazione") # "Invia Risposte per Valutazione"
        
        if submitted:
            if not answers:
                st.error("Nessuna domanda disponibile in questo set.") # "Nessuna domanda disponibile in questo set."
            else:
                # Valuta ogni risposta
                with st.spinner("Valutazione risposte in corso..."): # "Valutazione risposte in corso..."
                    results = {}
                    
                    for q_id, answer in answers.items():
                        if answer.strip():  # Valuta solo risposte non vuote
                            q_data = get_question_data(q_id)
                            if q_data:
                                evaluation = evaluate_answer(
                                    q_data['question'],
                                    q_data['expected_answer'],
                                    answer,
                                    client,
                                    show_api_details
                                )
                                
                                results[q_id] = {
                                    'question': q_data['question'],
                                    'expected_answer': q_data['expected_answer'],
                                    'actual_answer': answer,
                                    'evaluation': evaluation
                                }
                        else:
                            # Risposta vuota
                            q_data = get_question_data(q_id)
                            if q_data:
                                results[q_id] = {
                                    'question': q_data['question'],
                                    'expected_answer': q_data['expected_answer'],
                                    'actual_answer': "(Nessuna risposta fornita)", # "(Nessuna risposta fornita)"
                                    'evaluation': {
                                        'score': 0,
                                        'explanation': "Nessuna risposta è stata fornita.", # "Nessuna risposta è stata fornita."
                                        'similarity': 0,
                                        'correctness': 0,
                                        'completeness': 0
                                    }
                                }
                    
                    # Calcola punteggio medio
                    if results:
                        total_score = sum(r['evaluation']['score'] for r in results.values())
                        avg_score = total_score / len(results) if results else 0 # Aggiunto controllo per divisione per zero
                        
                        # Aggiungi risultato del test al database
                        result_data = {
                            'set_name': selected_set['name'],
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'avg_score': avg_score,
                            'questions': results
                        }
                        
                        result_id = add_test_result(selected_set_id, result_data)
                        
                        # Mostra messaggio di successo
                        st.success(f"Test completato con successo! Punteggio medio: {avg_score:.2f}%") # f"Test completato con successo! Punteggio medio: {avg_score:.2f}%"
                        
                        # Reindirizza alla pagina dei risultati
                        st.session_state.last_result_id = result_id
                        st.info("Visualizza i risultati dettagliati nella pagina Visualizzazione Risultati.") # "Visualizza i risultati dettagliati nella pagina Visualizzazione Risultati."
                        
                        # Visualizza riepilogo risultati
                        st.header("Riepilogo Risultati") # "Riepilogo Risultati"
                        
                        for q_id, result in results.items():
                            with st.expander(f"Domanda: {result['question'][:100]}..."): # f"Domanda: {result['question'][:100]}..."
                                st.write(f"**Domanda:** {result['question']}") # "**Domanda:**"
                                st.write(f"**Risposta Attesa:** {result['expected_answer']}") # "**Risposta Attesa:**"
                                st.write(f"**La Tua Risposta:** {result['actual_answer']}") # "**La Tua Risposta:**"
                                st.write(f"**Punteggio:** {result['evaluation']['score']:.2f}%") # "**Punteggio:**"
                                st.write(f"**Spiegazione:** {result['evaluation']['explanation']}") # "**Spiegazione:**"
                                
                                # Visualizza metriche
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Somiglianza", f"{result['evaluation'].get('similarity', 0):.2f}%") # "Somiglianza"
                                col2.metric("Correttezza", f"{result['evaluation'].get('correctness', 0):.2f}%") # "Correttezza"
                                col3.metric("Completezza", f"{result['evaluation'].get('completeness', 0):.2f}%") # "Completezza"
                    else:
                        st.error("Nessuna risposta è stata fornita per la valutazione.") # "Nessuna risposta è stata fornita per la valutazione."

else:  # Valutazione Automatica con Risposte di Esempio
    st.header("Valutazione Automatica con Risposte di Esempio") # "Valutazione Automatica con Risposte di Esempio"
    st.write("Il sistema genererà risposte di esempio e le valuterà automaticamente.") # "Il sistema genererà risposte di esempio e le valuterà automaticamente."
    
    # Risposte di esempio a scopo dimostrativo
    sample_answers = {
        "Perfetta": "Questa sarebbe una risposta perfetta che corrisponde a quella attesa.", # "Perfetta"
        "Parziale": "Questa risposta contiene solo alcune delle informazioni attese.", # "Parziale"
        "Errata": "Questa è una risposta completamente errata.", # "Errata"
    }
    
    sample_type = st.selectbox(
        "Seleziona il tipo di risposte di esempio da testare", # "Seleziona il tipo di risposte di esempio da testare"
        options=list(sample_answers.keys())
    )
    
    if st.button("Esegui Test Automatico"): # "Esegui Test Automatico"
        with st.spinner("Generazione e valutazione delle risposte di esempio in corso..."): # "Generazione e valutazione delle risposte di esempio in corso..."
            results = {}
            
            for q_id in questions_in_set:
                q_data = get_question_data(q_id)
                if q_data:
                    # Usa la risposta di esempio come modello
                    actual_answer_for_eval = ""
                    if sample_type == "Perfetta": # "Perfetta"
                        # Per perfetta, usa la risposta attesa
                        actual_answer_for_eval = q_data['expected_answer']
                    elif sample_type == "Parziale": # "Parziale"
                        # Per parziale, usa la prima metà della risposta attesa
                        actual_answer_for_eval = q_data['expected_answer'].split('.')[0] + '.' if '.' in q_data['expected_answer'] else q_data['expected_answer'][:len(q_data['expected_answer'])//2]
                    else:  # Errata
                        # Per errata, usa un'affermazione contraria
                        actual_answer_for_eval = f"È vero il contrario. {sample_answers['Errata']}" # "Errata"
                    
                    # Valuta la risposta
                    evaluation = evaluate_answer(
                        q_data['question'],
                        q_data['expected_answer'],
                        actual_answer_for_eval,
                        client,
                        show_api_details
                    )
                    
                    results[q_id] = {
                        'question': q_data['question'],
                        'expected_answer': q_data['expected_answer'],
                        'actual_answer': actual_answer_for_eval,
                        'evaluation': evaluation
                    }
            
            # Calcola punteggio medio
            if results:
                total_score = sum(r['evaluation']['score'] for r in results.values())
                avg_score = total_score / len(results) if results else 0 # Aggiunto controllo
                
                # Aggiungi risultato del test al database
                result_data = {
                    'set_name': selected_set['name'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'avg_score': avg_score,
                    'sample_type': sample_type,
                    'questions': results
                }
                
                result_id = add_test_result(selected_set_id, result_data)
                
                # Mostra messaggio di successo
                st.success(f"Test automatico completato! Punteggio medio: {avg_score:.2f}%") # f"Test automatico completato! Punteggio medio: {avg_score:.2f}%"
                
                # Reindirizza alla pagina dei risultati
                st.session_state.last_result_id = result_id
                st.info("Visualizza i risultati dettagliati nella pagina Visualizzazione Risultati.") # "Visualizza i risultati dettagliati nella pagina Visualizzazione Risultati."
                
                # Visualizza riepilogo risultati
                st.header("Riepilogo Risultati") # "Riepilogo Risultati"
                
                for q_id, result in results.items():
                    with st.expander(f"Domanda: {result['question'][:100]}..."): # f"Domanda: {result['question'][:100]}..."
                        st.write(f"**Domanda:** {result['question']}") # "**Domanda:**"
                        st.write(f"**Risposta Attesa:** {result['expected_answer']}") # "**Risposta Attesa:**"
                        st.write(f"**Risposta di Esempio ({sample_type}):** {result['actual_answer']}") # f"**Risposta di Esempio ({sample_type}):**"
                        st.write(f"**Punteggio:** {result['evaluation']['score']:.2f}%") # "**Punteggio:**"
                        st.write(f"**Spiegazione:** {result['evaluation']['explanation']}") # "**Spiegazione:**"
                        
                        # Visualizza metriche
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Somiglianza", f"{result['evaluation'].get('similarity', 0):.2f}%") # "Somiglianza"
                        col2.metric("Correttezza", f"{result['evaluation'].get('correctness', 0):.2f}%") # "Correttezza"
                        col3.metric("Completezza", f"{result['evaluation'].get('completeness', 0):.2f}%") # "Completezza"
            else:
                st.error("Nessuna domanda disponibile per la valutazione.") # "Nessuna domanda disponibile per la valutazione."