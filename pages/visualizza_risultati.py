import streamlit as st
import pandas as pd
import sys
import os
import json
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_utils import load_results, load_question_sets
from utils.ui_utils import add_page_header, add_section_title, create_card, create_metrics_container

add_page_header(
    "Visualizzazione Risultati Test",
    icon="📊",
    description="Analizza e visualizza i risultati dettagliati delle valutazioni dei test eseguiti."
)

if 'results' not in st.session_state or st.session_state.results.empty:
    st.warning("Nessun risultato di test disponibile. Esegui prima alcuni test dalla pagina 'Esecuzione Test'.")
    st.stop()

if 'question_sets' not in st.session_state:
    st.session_state.question_sets = load_question_sets()

def get_set_name(set_id):
    if not st.session_state.question_sets.empty:
        set_info = st.session_state.question_sets[st.session_state.question_sets['id'] == str(set_id)]
        if not set_info.empty:
            return set_info.iloc[0]['name']
    return "Set Sconosciuto"

# Elabora i risultati per la visualizzazione nel selectbox
processed_results_for_select = []
for _, row in st.session_state.results.iterrows():
    result_data = row['results'] # Questo è il dizionario che contiene tutti i dettagli
    set_name = get_set_name(row['set_id'])
    avg_score = result_data.get('avg_score', 0)
    method = result_data.get('method', 'N/A')
    method_icon = "🤖" if method == "LLM" else "🔍" if method == "BM25" else "📊"
    
    processed_results_for_select.append({
        'id': row['id'],
        'display_name': f"{row['timestamp']} - {method_icon} {set_name} (Avg: {avg_score:.2f}%) - {method}"
    })

processed_results_for_select.sort(key=lambda x: x['display_name'].split(' - ')[0], reverse=True) # Ordina per timestamp

result_options = {r['id']: r['display_name'] for r in processed_results_for_select}

# Seleziona il risultato da visualizzare
selected_result_id = st.selectbox(
    "Seleziona un Risultato del Test da Visualizzare",
    options=list(result_options.keys()),
    format_func=lambda x: result_options[x],
    index=0 if result_options else None,
    key="select_test_result_to_view"
)

if not selected_result_id:
    st.info("Nessun risultato selezionato o disponibile.")
    st.stop()

# Ottieni i dati del risultato selezionato
selected_result_row = st.session_state.results[st.session_state.results['id'] == selected_result_id].iloc[0]
result_data = selected_result_row['results']
set_name = get_set_name(selected_result_row['set_id'])
questions_results = result_data.get('questions', {})

# Visualizza informazioni generali sul risultato
evaluation_method = result_data.get('method', 'LLM')
method_icon = "🤖" if evaluation_method == "LLM" else "🔍"
method_desc = "Valutazione LLM" if evaluation_method == "LLM" else "Valutazione BM25"

add_section_title(f"Dettaglio Test: {set_name} [{method_icon} {evaluation_method}]", icon="📄")
st.markdown(f"**ID Risultato:** `{selected_result_id}`")
st.markdown(f"**Eseguito il:** {selected_result_row['timestamp']}")
st.markdown(f"**Metodo di Valutazione:** {method_icon} **{method_desc}**")

if 'generation_preset' in result_data:
    st.markdown(f"**Preset Generazione Risposte:** `{result_data['generation_preset']}`")
if evaluation_method == "LLM" and 'evaluation_preset' in result_data:
    st.markdown(f"**Preset Valutazione Risposte (LLM):** `{result_data['evaluation_preset']}`")

if evaluation_method == "BM25" and 'parameters' in result_data:
    params = result_data['parameters']
    with st.expander("Parametri BM25 Utilizzati"):
        k1 = params.get('k1', 'N/A')
        b = params.get('b', 'N/A')
        ht = params.get('high_threshold', 'N/A')
        mt = params.get('medium_threshold', 'N/A')
        st.json({ "k1": k1, "b": b, "Soglia Alta": f"{ht}%", "Soglia Media": f"{mt}%" })

# Metriche Generali del Test
add_section_title("Metriche Generali del Test", icon="📈")

if questions_results:
    avg_score_overall = result_data.get('avg_score', 0)
    num_questions = len(questions_results)
    
    cols_metrics = st.columns(2)
    with cols_metrics[0]:
        st.metric("Punteggio Medio Complessivo", f"{avg_score_overall:.2f}%")
    with cols_metrics[1]:
        st.metric("Numero di Domande Valutate", num_questions)
    
    # Grafico a barre dei punteggi per domanda (se applicabile)
    if evaluation_method == "LLM":
        scores_per_q = {q_data.get('question', f'Domanda {i}')[:50]+"...": q_data.get('evaluation',{}).get('score',0) for i, (q_id, q_data) in enumerate(questions_results.items())}
    else: # BM25
        scores_per_q = {q_data.get('question', f'Domanda {i}')[:50]+"...": q_data.get('similarity_score',0) for i, (q_id, q_data) in enumerate(questions_results.items())}

    if scores_per_q:
        df_scores = pd.DataFrame(list(scores_per_q.items()), columns=['Domanda', 'Punteggio'])
        fig = px.bar(df_scores, x='Domanda', y='Punteggio', title="Punteggi per Domanda", color='Punteggio', height=max(400, num_questions * 30))
        fig.update_layout(yaxis_range=[0,100])
        st.plotly_chart(fig, use_container_width=True)
        
        # Grafico aggiuntivo solo per la modalità LLM
        if evaluation_method == "LLM":
            # Raccogliamo i dati di Somiglianza, Correttezza e Completezza per ogni domanda
            radar_data = []
            metrics_sum = {'similarity': 0, 'correctness': 0, 'completeness': 0}
            count = 0
            
            for q_id, q_data in questions_results.items():
                evaluation = q_data.get('evaluation', {})
                question_text = q_data.get('question', f'Domanda {q_id}')
                # Utilizziamo i primi 20 caratteri della domanda come etichetta
                question_label = question_text[:20] + "..." if len(question_text) > 20 else question_text
                
                # Raccogliamo i dati per il grafico radar individuale
                similarity = evaluation.get('similarity', 0)
                correctness = evaluation.get('correctness', 0)
                completeness = evaluation.get('completeness', 0)
                
                radar_data.append({
                    'Domanda': question_label,
                    'Somiglianza': similarity,
                    'Correttezza': correctness,
                    'Completezza': completeness
                })
                
                # Sommiamo per calcolare le medie
                metrics_sum['similarity'] += similarity
                metrics_sum['correctness'] += correctness
                metrics_sum['completeness'] += completeness
                count += 1
            
            # Calcoliamo le medie
            avg_metrics = {
                'similarity': metrics_sum['similarity'] / count if count > 0 else 0,
                'correctness': metrics_sum['correctness'] / count if count > 0 else 0,
                'completeness': metrics_sum['completeness'] / count if count > 0 else 0
            }
            
            # Creiamo un DataFrame con i dati
            df_radar = pd.DataFrame(radar_data)
            
            # Prima mostriamo il radar chart per ogni domanda
            categories = ['Somiglianza', 'Correttezza', 'Completezza']
            
            # Creiamo il grafico radar
            fig_radar = go.Figure()
            
            # Aggiungiamo una traccia per ogni domanda
            for i, row in df_radar.iterrows():
                fig_radar.add_trace(go.Scatterpolar(
                    r=[row['Somiglianza'], row['Correttezza'], row['Completezza']],
                    theta=categories,
                    fill='toself',
                    name=row['Domanda']
                ))
            
            # Aggiungiamo una traccia per la media
            fig_radar.add_trace(go.Scatterpolar(
                r=[avg_metrics['similarity'], avg_metrics['correctness'], avg_metrics['completeness']],
                theta=categories,
                fill='toself',
                name='Media',
                line=dict(color='red', width=3)
            ))
            
            # Configuriamo il layout del grafico radar
            fig_radar.update_layout(
                title="Grafico Radar delle Metriche LLM per ogni domanda",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                height=600
            )
            
            # Mostriamo il grafico radar
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # Mostriamo anche i valori medi in un blocco di metriche per maggiore chiarezza
            st.subheader("Valori medi delle metriche")
            cols = st.columns(3)
            cols[0].metric("Somiglianza", f"{avg_metrics['similarity']:.2f}%")
            cols[1].metric("Correttezza", f"{avg_metrics['correctness']:.2f}%")
            cols[2].metric("Completezza", f"{avg_metrics['completeness']:.2f}%")
else:
    st.info("Nessun dettaglio per le domande disponibile in questo risultato.")

# Dettagli per ogni domanda
add_section_title("Risultati Dettagliati per Domanda", icon="📝")
if not questions_results:
    st.info("Nessuna domanda trovata in questo set di risultati.")
else:
    for q_id, q_data in questions_results.items():
        question_text = q_data.get('question', "Testo domanda non disponibile")
        expected_answer = q_data.get('expected_answer', "Risposta attesa non disponibile")
        actual_answer = q_data.get('actual_answer', "Risposta effettiva non disponibile")
        
        with st.expander(f"Domanda: {question_text[:100]}..."):
            st.markdown(f"**Domanda:** {question_text}")
            st.markdown(f"**Risposta Attesa:** {expected_answer}")
            st.markdown(f"**Risposta Generata/Effettiva:** {actual_answer}")
            st.divider()
            
            # Mostra Dettagli API di Generazione (se presenti e richiesti)
            generation_api_details = q_data.get('generation_api_details')
            if generation_api_details and isinstance(generation_api_details, dict):
                with st.container():
                    st.markdown("###### Dettagli Chiamata API di Generazione Risposta")
                    if generation_api_details.get('request'):
                        st.caption("Richiesta API Generazione:")
                        st.json(generation_api_details['request'], expanded=False)
                    if generation_api_details.get('response_content'):
                        st.caption("Contenuto Risposta API Generazione:")
                        # Prova a formattare se è una stringa JSON, altrimenti mostra com'è
                        try:
                            response_data_gen = json.loads(generation_api_details['response_content']) if isinstance(generation_api_details['response_content'], str) else generation_api_details['response_content']
                            st.code(json.dumps(response_data_gen, indent=2), language="json")
                        except:
                             st.text(generation_api_details['response_content'])
                    if generation_api_details.get('error'):
                        st.caption("Errore API Generazione:")
                        st.error(generation_api_details['error'])
                st.divider()
            
            if evaluation_method == "LLM":
                evaluation = q_data.get('evaluation', {}) # Assicurati che evaluation sia sempre un dizionario
                # RIGA DI DEBUG RIMOSSA
                st.markdown(f"##### Valutazione LLM")
                evaluation = q_data.get('evaluation', {})
                st.markdown(f"##### Valutazione LLM")
                score = evaluation.get('score', 0)
                explanation = evaluation.get('explanation', "Nessuna spiegazione.")
                similarity = evaluation.get('similarity', 0)
                correctness = evaluation.get('correctness', 0)
                completeness = evaluation.get('completeness', 0)
                
                st.markdown(f"**Punteggio Complessivo:** {score:.2f}%")
                st.markdown(f"**Spiegazione:** {explanation}")
                
                cols_eval_metrics = st.columns(3)
                cols_eval_metrics[0].metric("Somiglianza", f"{similarity:.2f}%")
                cols_eval_metrics[1].metric("Correttezza", f"{correctness:.2f}%")
                cols_eval_metrics[2].metric("Completezza", f"{completeness:.2f}%")

                api_details = evaluation.get('api_details')
                if api_details and isinstance(api_details, dict):
                    with st.container(): # Sostituisce l'expander interno
                        st.markdown("###### Dettagli Chiamata API di Valutazione")
                        if api_details.get('request'):
                            st.caption("Richiesta API:")
                            st.json(api_details['request'], expanded=False)
                        if api_details.get('response_content'):
                            st.caption("Contenuto Risposta API:")
                            st.code(json.dumps(json.loads(api_details['response_content']), indent=2) if isinstance(api_details['response_content'], str) else json.dumps(api_details['response_content'], indent=2), language="json")
                        if api_details.get('error'):
                            st.caption("Errore API:")
                            st.error(api_details['error'])
            
            elif evaluation_method == "BM25":
                st.markdown(f"##### Valutazione BM25")
                similarity_score = q_data.get('similarity_score', 0)
                match_level = q_data.get('match_level', 'N/A')
                suggestions = q_data.get('suggestions', 'Nessun suggerimento.')
                missing_keywords = q_data.get('missing_keywords', [])
                extra_keywords = q_data.get('extra_keywords', [])
                
                st.markdown(f"**Punteggio Similarità BM25:** {similarity_score:.2f}%")
                st.markdown(f"**Livello di Match:** {match_level.capitalize()}")
                st.markdown(f"**Suggerimenti:** {suggestions}")
                
                if missing_keywords:
                    st.markdown(f"**Termini Mancanti:** `{', '.join(missing_keywords)}`")
                if extra_keywords:
                    st.markdown(f"**Termini in Eccesso:** `{', '.join(extra_keywords)}`")
            st.markdown("--- --- ---")
