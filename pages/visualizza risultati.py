import streamlit as st
import pandas as pd
import sys
import os
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Aggiungi la directory genitore al percorso in modo da poter importare da utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_utils import load_results, load_question_sets
from utils.ui_utils import add_page_header, add_section_title, create_card, create_metrics_container

# Aggiungi un'intestazione stilizzata
add_page_header(
    "Visualizzazione Risultati",
    icon="📊",
    description="Analizza e visualizza i risultati della valutazione dei test"
)

# Controlla se ci sono risultati dei test
if 'results' not in st.session_state or st.session_state.results.empty:
    st.warning("Nessun risultato di test disponibile. Esegui prima i test.") # "Nessun risultato di test disponibile. Esegui prima i test."
    st.stop()

# Funzione per ottenere il nome del set tramite ID
def get_set_name(set_id):
    if 'question_sets' in st.session_state and not st.session_state.question_sets.empty:
        set_row = st.session_state.question_sets[st.session_state.question_sets['id'] == set_id]
        if not set_row.empty:
            return set_row.iloc[0]['name']
    return f"ID Set: {set_id} (non trovato)" # "ID Set: {set_id} (non trovato)"

# Crea opzioni per la selezione dei risultati
st.header("Seleziona Risultato Test") # "Seleziona Risultato Test"

# Elabora i risultati per la visualizzazione
processed_results = []
for _, row in st.session_state.results.iterrows():
    set_name = get_set_name(row['set_id'])
    result_data = row['results']
    
    # Calcola il punteggio medio se disponibile
    avg_score = result_data.get('avg_score', 0)
    if not avg_score and 'questions' in result_data:
        # Calcola dalle domande se non già fornito
        scores = [q['evaluation']['score'] for q in result_data['questions'].values() if 'evaluation' in q and 'score' in q['evaluation']] # Aggiunto controllo per 'evaluation' e 'score'
        avg_score = sum(scores) / len(scores) if scores else 0
    
    processed_results.append({
        'id': row['id'],
        'set_id': row['set_id'],
        'set_name': set_name,
        'timestamp': row['timestamp'],
        'avg_score': avg_score,
        'questions_count': len(result_data.get('questions', {}))
    })

# Ordina per timestamp (i più recenti prima)
processed_results.sort(key=lambda x: x['timestamp'], reverse=True)

# Crea opzioni per la selezione
result_options = {r['id']: f"{r['timestamp']} - {r['set_name']} (Punteggio: {r['avg_score']:.2f}%)"
                  for r in processed_results}

# Pre-seleziona se proviene dall'esecuzione del test
default_idx = 0
if 'last_result_id' in st.session_state and st.session_state.last_result_id in result_options:
    default_idx = list(result_options.keys()).index(st.session_state.last_result_id)

selected_result_id = st.selectbox(
    "Seleziona un risultato del test da visualizzare", # "Seleziona un risultato del test da visualizzare"
    options=list(result_options.keys()),
    index=default_idx,
    format_func=lambda x: result_options[x]
)

# Ottieni il risultato selezionato
selected_result = st.session_state.results[st.session_state.results['id'] == selected_result_id].iloc[0]
result_data = selected_result['results']
set_name = get_set_name(selected_result['set_id'])

# Visualizza le informazioni generali sul risultato
add_section_title(f"Risultati Test: {set_name}", icon="📈") # "Risultati Test: {set_name}"
st.markdown(f"**Test eseguito il:** {selected_result['timestamp']}") # "**Test eseguito il:** {selected_result['timestamp']}"

# Calcola statistiche generali
if 'questions' in result_data:
    questions = result_data['questions']
    
    # Punteggio complessivo
    avg_score = result_data.get('avg_score', 0)
    if not avg_score:
        scores = [q['evaluation']['score'] for q in questions.values() if 'evaluation' in q and 'score' in q['evaluation']] # Aggiunto controllo
        avg_score = sum(scores) / len(scores) if scores else 0
    
    # Medie delle metriche
    similarity_avg = sum(q['evaluation'].get('similarity', 0) for q in questions.values() if 'evaluation' in q) / len(questions) if questions else 0 # Aggiunto controllo
    correctness_avg = sum(q['evaluation'].get('correctness', 0) for q in questions.values() if 'evaluation' in q) / len(questions) if questions else 0 # Aggiunto controllo
    completeness_avg = sum(q['evaluation'].get('completeness', 0) for q in questions.values() if 'evaluation' in q) / len(questions) if questions else 0 # Aggiunto controllo
    
    # Crea una visualizzazione delle metriche più accattivante
    metrics_data = [
        {'label': 'Punteggio Complessivo', 'value': f"{avg_score:.1f}", 'unit': '%', 'icon': '🎯'}, # "Punteggio Complessivo"
        {'label': 'Somiglianza', 'value': f"{similarity_avg:.1f}", 'unit': '%', 'icon': '🔍'}, # "Somiglianza"
        {'label': 'Correttezza', 'value': f"{correctness_avg:.1f}", 'unit': '%', 'icon': '✓'}, # "Correttezza"
        {'label': 'Completezza', 'value': f"{completeness_avg:.1f}", 'unit': '%', 'icon': '📋'} # "Completezza"
    ]
    
    # Usa la funzione contenitore delle metriche per uno stile migliore
    create_metrics_container(metrics_data)
    
    # Crea un grafico a barre per tutte le domande
    question_scores = []
    for q_id, q_data in questions.items():
        question_text = q_data.get('question', f'Domanda {q_id}') # "Domanda {q_id}"
        # Tronca il testo della domanda per la visualizzazione
        question_short = question_text[:50] + "..." if len(question_text) > 50 else question_text
        
        evaluation = q_data.get('evaluation', {}) # Aggiunto default vuoto
        question_scores.append({
            'question': question_short,
            'score': evaluation.get('score', 0), # Aggiunto default
            'similarity': evaluation.get('similarity', 0),
            'correctness': evaluation.get('correctness', 0),
            'completeness': evaluation.get('completeness', 0)
        })
    
    # Ordina per punteggio se ci sono punteggi
    if question_scores:
        question_scores.sort(key=lambda x: x['score'])
        
        # Crea dataframe per il plottaggio
        df = pd.DataFrame(question_scores)
        
        st.subheader("Punteggi per Domanda") # "Punteggi per Domanda"
        
        # Grafico a barre per i punteggi complessivi
        fig = px.bar(
            df,
            x='score',
            y='question',
            orientation='h',
            title="Punteggio Complessivo per Domanda", # "Punteggio Complessivo per Domanda"
            labels={'score': 'Punteggio (%)', 'question': 'Domanda'}, # "Punteggio (%)", "Domanda"
            color='score',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        fig.update_layout(height=max(400, len(df) * 30))
        st.plotly_chart(fig, use_container_width=True)
        
        # Grafico radar per le metriche
        metrics = ['similarity', 'correctness', 'completeness'] # Non tradurre, sono chiavi
        
        # Crea dataframe per il grafico radar
        radar_df = pd.DataFrame({
            'metric': ['Somiglianza', 'Correttezza', 'Completezza'], # Etichette per il grafico
            'value': [similarity_avg, correctness_avg, completeness_avg]
        })
        
        # Crea grafico radar
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=radar_df['value'],
            theta=radar_df['metric'],
            fill='toself',
            name='Punteggio Medio' # "Punteggio Medio"
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            title="Metriche Medie" # "Metriche Medie"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostra risultati dettagliati per ogni domanda
        st.subheader("Risultati Dettagliati per Domanda") # "Risultati Dettagliati per Domanda"
        
        for q_id, q_data in questions.items():
            with st.expander(f"Domanda: {q_data.get('question', '')[:100]}..."): # "Domanda:"
                evaluation = q_data.get('evaluation', {}) # Aggiunto default
                st.write(f"**Domanda:** {q_data.get('question', '')}") # "**Domanda:**"
                st.write(f"**Risposta Attesa:** {q_data.get('expected_answer', '')}") # "**Risposta Attesa:**"
                st.write(f"**Risposta Effettiva:** {q_data.get('actual_answer', '')}") # "**Risposta Effettiva:**"
                st.write(f"**Punteggio:** {evaluation.get('score', 0):.2f}%") # "**Punteggio:**"
                st.write(f"**Spiegazione:** {evaluation.get('explanation', '')}") # "**Spiegazione:**"
                
                # Crea metriche per i punteggi
                col1, col2, col3 = st.columns(3)
                col1.metric("Somiglianza", f"{evaluation.get('similarity', 0):.2f}%") # "Somiglianza"
                col2.metric("Correttezza", f"{evaluation.get('correctness', 0):.2f}%") # "Correttezza"
                col3.metric("Completezza", f"{evaluation.get('completeness', 0):.2f}%") # "Completezza"
                
                # Mostra dettagli API se disponibili
                if 'api_details' in evaluation:
                    with st.expander("Visualizza Dettagli Richiesta e Risposta API"): # "Visualizza Dettagli Richiesta e Risposta API"
                        st.subheader("Richiesta API") # "Richiesta API"
                        st.json(evaluation['api_details'].get('request', {})) # Aggiunto default
                        
                        st.subheader("Risposta API") # "Risposta API"
                        st.json(evaluation['api_details'].get('response', {})) # Aggiunto default
                        
                        st.subheader("Utilizzo Token") # "Utilizzo Token"
                        if 'response' in evaluation['api_details'] and 'usage' in evaluation['api_details']['response']:
                            usage = evaluation['api_details']['response']['usage']
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Token Prompt", usage.get('prompt_tokens', 0)) # "Token Prompt"
                            col2.metric("Token Completamento", usage.get('completion_tokens', 0)) # "Token Completamento"
                            col3.metric("Token Totali", usage.get('total_tokens', 0)) # "Token Totali"
    else:
        st.warning("Nessun punteggio per le domande disponibile in questo risultato del test.") # "Nessun punteggio per le domande disponibile in questo risultato del test."
else:
    st.warning("Nessun dato dettagliato sulle domande disponibile per questo risultato del test.") # "Nessun dato dettagliato sulle domande disponibile per questo risultato del test."

# Opzione per visualizzare i dati grezzi del risultato
with st.expander("Visualizza Dati Grezzi Risultato"): # "Visualizza Dati Grezzi Risultato"
    st.json(result_data)