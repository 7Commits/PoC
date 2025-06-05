#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from utils.ui_utils import add_page_header, add_section_title, create_card, create_metrics_container
from utils.bm25 import (
    calcola_similarita_normalizzata, analizza_parole_chiave, 
    genera_suggerimenti, segmenta_testo
)

# Aggiungi un'intestazione stilizzata
add_page_header(
    "Valutazione BM25",
    icon="🔍",
    description="Valuta le risposte utilizzando l'algoritmo Best Matching 25"
)

# Controlla se ci sono set di domande disponibili
if 'question_sets' not in st.session_state or st.session_state.question_sets.empty:
    st.warning("Nessun set di domande disponibile. Crea dei set di domande prima di eseguire i test.")
    st.stop()

# Ottieni testo della domanda e risposta attesa per ID
def get_question_data(question_id):
    if 'questions' in st.session_state and not st.session_state.questions.empty:
        question_row = st.session_state.questions[st.session_state.questions['id'] == question_id]
        if not question_row.empty:
            return {
                'question': question_row.iloc[0]['domanda'],
                'expected_answer': question_row.iloc[0]['risposta_attesa']
            }
    return None

# Seleziona set di domande per il test
add_section_title("Seleziona Set di Domande", icon="📚")

# Crea una scheda per spiegare la selezione
create_card(
    "Selezione Set di Domande",
    "Scegli un set di domande da valutare utilizzando l'algoritmo BM25 per misurare la similitudine tra le risposte attese e le tue risposte.",
    icon="ℹ️"
)

# Crea dropdown con i set disponibili
set_options = {}
if 'question_sets' in st.session_state and not st.session_state.question_sets.empty:
    for _, row in st.session_state.question_sets.iterrows():
        # Mostra solo i set che hanno domande
        if 'questions' in row and row['questions']:
            set_options[row['id']] = f"{row['name']} ({len(row['questions'])} domande)"

if not set_options:
    create_card(
        "Nessun Set di Domande Disponibile",
        "Crea set di domande prima di eseguire i test. Vai alla pagina Gestione Set di Domande per creare i set.",
        is_warning=True,
        icon="⚠️"
    )
    st.stop()

selected_set_id = st.selectbox(
    "Seleziona un set di domande",
    options=list(set_options.keys()),
    format_func=lambda x: set_options[x]
)

# Ottieni il set selezionato
selected_set = st.session_state.question_sets[st.session_state.question_sets['id'] == selected_set_id].iloc[0]
questions_in_set = selected_set['questions']

# Parametri BM25
add_section_title("Parametri BM25", icon="⚙️")

# Crea una scheda per spiegare i parametri
create_card(
    "Parametri dell'algoritmo BM25",
    "L'algoritmo BM25 utilizza due parametri principali: k1 controlla la saturazione della frequenza dei termini, mentre b controlla la normalizzazione della lunghezza del documento.",
    icon="🔧"
)

# Slider per i parametri principali di BM25
col1, col2 = st.columns(2)

with col1:
    k1 = st.slider(
        "Parametro k1 (saturazione frequenza)",
        min_value=0.5,
        max_value=3.0,
        value=1.5,
        step=0.1,
        help="Controlla quanto la frequenza di un termine influisce sul punteggio. Valori tipici: 1.2-2.0"
    )

with col2:
    b = st.slider(
        "Parametro b (normalizzazione lunghezza)",
        min_value=0.0,
        max_value=1.0,
        value=0.75,
        step=0.05,
        help="Controlla quanto la lunghezza del documento influisce sul punteggio. Valore tipico: 0.75"
    )

# Soglie di corrispondenza
add_section_title("Soglie di Corrispondenza", icon="📊")

col1, col2 = st.columns(2)

with col1:
    high_threshold = st.slider(
        "Soglia per alta corrispondenza (%)",
        min_value=50,
        max_value=100,
        value=80,
        step=5,
        help="Punteggio minimo per considerare una risposta come altamente corrispondente"
    )

with col2:
    medium_threshold = st.slider(
        "Soglia per media corrispondenza (%)",
        min_value=30,
        max_value=high_threshold-5,
        value=50,
        step=5,
        help="Punteggio minimo per considerare una risposta come mediamente corrispondente"
    )

# Opzione per visualizzare i token
show_tokens = st.checkbox(
    "Mostra dettagli di segmentazione",
    value=False,
    help="Visualizza i termini estratti per ogni risposta"
)

# Modulo per inserire le risposte
add_section_title("Inserisci Risposte", icon="✍️")

with st.form("bm25_test_form"):
    answers = {}
    
    # Visualizza ogni domanda e raccogli le risposte
    for q_id in questions_in_set:
        q_data = get_question_data(q_id)
        if q_data:
            st.write(f"**Domanda:** {q_data['question']}")
            st.write(f"**Risposta Attesa:** {q_data['expected_answer']}")
            answer = st.text_area(f"La tua risposta per la domanda {q_id}", key=f"bm25_answer_{q_id}")
            answers[q_id] = answer
    
    submitted = st.form_submit_button("Valuta Risposte con BM25")
    
    if submitted:
        if not answers:
            st.error("Nessuna domanda disponibile in questo set.")
        else:
            # Valuta ogni risposta
            with st.spinner("Valutazione risposte con BM25 in corso..."):
                results = {}
                
                for q_id, answer in answers.items():
                    if answer.strip():  # Valuta solo risposte non vuote
                        q_data = get_question_data(q_id)
                        if q_data:
                            # Calcola similarità con BM25
                            similarity_score = calcola_similarita_normalizzata(
                                q_data['expected_answer'], 
                                answer,
                                k1=k1,
                                b=b
                            )
                            
                            # Analizza parole chiave mancanti e in eccesso
                            missing_keywords, extra_keywords = analizza_parole_chiave(
                                q_data['expected_answer'], 
                                answer
                            )
                            
                            # Determina il livello di corrispondenza
                            if similarity_score >= high_threshold:
                                match_level = "alto"
                                match_class = "match-high"
                            elif similarity_score >= medium_threshold:
                                match_level = "medio"
                                match_class = "match-medium"
                            else:
                                match_level = "basso"
                                match_class = "match-low"
                            
                            # Genera suggerimenti
                            suggestions = genera_suggerimenti(missing_keywords, match_level)
                            
                            # Prepara i risultati
                            results[q_id] = {
                                'question': q_data['question'],
                                'expected_answer': q_data['expected_answer'],
                                'actual_answer': answer,
                                'similarity_score': similarity_score,
                                'match_level': match_level,
                                'missing_keywords': missing_keywords,
                                'extra_keywords': extra_keywords,
                                'suggestions': suggestions,
                                'evaluation': {
                                    'score': similarity_score,  # Per compatibilità con il formato esistente
                                    'explanation': suggestions,
                                    'similarity': similarity_score,
                                    'correctness': similarity_score if match_level == "alto" else (similarity_score * 0.8 if match_level == "medio" else similarity_score * 0.5),
                                    'completeness': 100 - (len(missing_keywords) * 10) if len(missing_keywords) < 10 else 0
                                }
                            }
                    else:
                        # Risposta vuota
                        q_data = get_question_data(q_id)
                        if q_data:
                            results[q_id] = {
                                'question': q_data['question'],
                                'expected_answer': q_data['expected_answer'],
                                'actual_answer': "(Nessuna risposta fornita)",
                                'similarity_score': 0,
                                'match_level': "basso",
                                'missing_keywords': segmenta_testo(q_data['expected_answer']),
                                'extra_keywords': [],
                                'suggestions': "Devi fornire una risposta per la valutazione.",
                                'evaluation': {
                                    'score': 0,
                                    'explanation': "Nessuna risposta è stata fornita.",
                                    'similarity': 0,
                                    'correctness': 0,
                                    'completeness': 0
                                }
                            }
                
                # Calcola punteggio medio
                if results:
                    total_score = sum(r['similarity_score'] for r in results.values())
                    avg_score = total_score / len(results) if results else 0
                    
                    # Aggiungi risultato del test al database
                    result_data = {
                        'set_name': selected_set['name'],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'avg_score': avg_score,
                        'method': 'BM25',
                        'parameters': {
                            'k1': k1,
                            'b': b,
                            'high_threshold': high_threshold,
                            'medium_threshold': medium_threshold
                        },
                        'questions': results
                    }
                    
                    result_id = add_test_result(selected_set_id, result_data)
                    
                    # Mostra messaggio di successo
                    st.success(f"Valutazione BM25 completata! Punteggio medio di similarità: {avg_score:.2f}%")
                    
                    # Reindirizza alla pagina dei risultati
                    st.session_state.last_result_id = result_id
                    st.info("Visualizza i risultati dettagliati nella pagina Visualizzazione Risultati.")
                    
                    # Visualizza riepilogo risultati
                    st.header("Riepilogo Risultati BM25")
                    
                    for q_id, result in results.items():
                        with st.expander(f"Domanda: {result['question'][:100]}..."):
                            st.write(f"**Domanda:** {result['question']}")
                            st.write(f"**Risposta Attesa:** {result['expected_answer']}")
                            st.write(f"**La Tua Risposta:** {result['actual_answer']}")
                            
                            # Usa il CSS personalizzato per il livello di corrispondenza
                            match_classes = {
                                "alto": "match-high",
                                "medio": "match-medium",
                                "basso": "match-low"
                            }
                            match_class = match_classes.get(result['match_level'], "match-low")
                            
                            st.markdown(f"**Livello di Corrispondenza:** <span class='{match_class}'>{result['match_level'].upper()}</span>", unsafe_allow_html=True)
                            st.write(f"**Punteggio di Similarità:** {result['similarity_score']:.2f}%")
                            st.write(f"**Suggerimenti:** {result['suggestions']}")
                            
                            # Visualizza metriche
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Similarità", f"{result['evaluation']['similarity']:.2f}%")
                            col2.metric("Correttezza", f"{result['evaluation']['correctness']:.2f}%")
                            col3.metric("Completezza", f"{result['evaluation']['completeness']:.2f}%")
                            
                            # Mostra dettagli di segmentazione se richiesto
                            if show_tokens:
                                st.write("**Dettagli di Segmentazione:**")
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**Termini Risposta Attesa:**")
                                    st.write(", ".join(segmenta_testo(result['expected_answer'])))
                                
                                with col2:
                                    st.write("**Termini Risposta Fornita:**")
                                    if result['actual_answer'] != "(Nessuna risposta fornita)":
                                        st.write(", ".join(segmenta_testo(result['actual_answer'])))
                                    else:
                                        st.write("Nessun termine disponibile")
                                
                                st.write("**Termini Mancanti:**")
                                if result['missing_keywords']:
                                    st.write(", ".join(result['missing_keywords']))
                                else:
                                    st.write("Nessun termine mancante")
                                
                                st.write("**Termini in Eccesso:**")
                                if result['extra_keywords']:
                                    st.write(", ".join(result['extra_keywords']))
                                else:
                                    st.write("Nessun termine in eccesso")
                else:
                    st.error("Nessuna risposta è stata fornita per la valutazione.")

# Aggiungi stili CSS personalizzati per i livelli di corrispondenza e per garantire la visibilità in tema scuro
st.markdown("""
<style>
    /* Stili per i livelli di corrispondenza */
    .match-high {
        color: #0a8b0a;
        font-weight: bold;
        background-color: #e6ffe6;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .match-medium {
        color: #b86e00;
        font-weight: bold;
        background-color: #fff3e0;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .match-low {
        color: #c70000;
        font-weight: bold;
        background-color: #ffe6e6;
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    /* Stile per i termini mancanti e in eccesso */
    .missing-term {
        color: #c70000;
        text-decoration: line-through;
    }
    .extra-term {
        color: #ff9800;
        font-style: italic;
    }
    
    /* Gli stili per gli input sono stati spostati nel file app.py per coerenza globale */
</style>
""", unsafe_allow_html=True)

# Aggiungi una sezione informativa sull'algoritmo BM25
st.markdown("---")
with st.expander("Informazioni sull'algoritmo BM25"):
    st.markdown("""
    ### Algoritmo Best Matching 25 (BM25)
    
    BM25 (Best Matching 25) è un algoritmo di ranking utilizzato in information retrieval per valutare la rilevanza tra una query e un documento. È un'evoluzione del modello TF-IDF (Term Frequency-Inverse Document Frequency) che introduce due miglioramenti principali:
    
    1. **Saturazione della frequenza dei termini**: BM25 limita l'influenza della frequenza dei termini attraverso il parametro `k1`. Questo significa che dopo un certo numero di occorrenze, ulteriori occorrenze di un termine hanno un impatto sempre minore sul punteggio finale.
    
    2. **Normalizzazione della lunghezza del documento**: BM25 normalizza i punteggi in base alla lunghezza del documento attraverso il parametro `b`. Questo aiuta a evitare che documenti più lunghi ottengano sistematicamente punteggi più alti solo perché contengono più parole.
    
    #### Formula BM25:
    
    La formula per calcolare il punteggio BM25 per un documento D rispetto a una query Q è:
    
    ```
    score(D,Q) = ∑ IDF(qi) · (f(qi,D) · (k1+1)) / (f(qi,D) + k1 · (1-b+b·|D|/avgdl))
    ```
    
    Dove:
    - `f(qi,D)` è la frequenza del termine qi nel documento D
    - `|D|` è la lunghezza del documento D
    - `avgdl` è la lunghezza media dei documenti nella collezione
    - `k1` e `b` sono parametri configurabili
    
    #### Come Funziona la Valutazione:
    
    In questa applicazione, BM25 viene utilizzato per misurare la similarità tra la risposta attesa e la risposta fornita dall'utente. L'algoritmo:
    
    1. Segmenta entrambe le risposte in token (parole)
    2. Calcola un punteggio di similarità bidirezionale (da risposta attesa a risposta utente e viceversa)
    3. Normalizza il punteggio su una scala da 0 a 100%
    4. Identifica parole chiave mancanti e in eccesso
    5. Fornisce suggerimenti specifici per migliorare la risposta
    
    Questa valutazione è particolarmente utile per misurare la qualità delle risposte in modo oggettivo, basato sulla presenza dei concetti chiave richiesti nella risposta.
    """)
