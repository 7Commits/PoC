import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_utils import (
    load_questions, load_question_sets, add_test_result, load_api_presets
)
from utils.openai_utils import (
    evaluate_answer, generate_example_answer_with_llm # Client viene creato internamente
)
from utils.ui_utils import add_page_header, add_section_title, create_card
from utils.bm25 import (
    calcola_similarita_normalizzata, analizza_parole_chiave, 
    genera_suggerimenti, segmenta_testo
)

# === CALLBACK FUNCTIONS ===

def set_llm_mode_callback():
    """回调函数：设置LLM模式"""
    if st.session_state.test_mode != "Valutazione Automatica con LLM":
        st.session_state.test_mode = "Valutazione Automatica con LLM"
        st.session_state.mode_changed = True

def set_bm25_mode_callback():
    """回调函数：设置BM25模式"""
    if st.session_state.test_mode != "Valutazione con BM25":
        st.session_state.test_mode = "Valutazione con BM25"
        st.session_state.mode_changed = True

def run_llm_test_callback():
    """回调函数：执行LLM测试"""
    st.session_state.run_llm_test = True

def run_bm25_test_callback():
    """回调函数：执行BM25测试"""
    st.session_state.run_bm25_test = True

# === 初始化状态变量 ===
if 'test_mode' not in st.session_state:
    st.session_state.test_mode = "Valutazione Automatica con LLM"
if 'mode_changed' not in st.session_state:
    st.session_state.mode_changed = False
if 'run_llm_test' not in st.session_state:
    st.session_state.run_llm_test = False
if 'run_bm25_test' not in st.session_state:
    st.session_state.run_bm25_test = False

# 处理模式变更
if st.session_state.mode_changed:
    st.session_state.mode_changed = False
    st.rerun()

add_page_header(
    "Esecuzione Test",
    icon="🧪",
    description="Esegui valutazioni automatiche sui tuoi set di domande utilizzando i preset API configurati."
)

# Carica i preset API e verifica che ce ne sia almeno uno
if 'api_presets' not in st.session_state:
    st.session_state.api_presets = load_api_presets()

if st.session_state.api_presets.empty:
    st.error("Nessun preset API configurato. Vai alla pagina 'Gestione Preset API' per crearne almeno uno prima di eseguire i test.")
    st.stop()

# Controlla se ci sono set di domande disponibili
if 'question_sets' not in st.session_state or st.session_state.question_sets.empty:
    st.warning("Nessun set di domande disponibile. Crea dei set di domande prima di eseguire i test.")
    st.stop()

# Ottieni testo della domanda e risposta attesa per ID
def get_question_data(question_id):
    if 'questions' in st.session_state and not st.session_state.questions.empty:
        question_row = st.session_state.questions[st.session_state.questions['id'] == str(question_id)]
        if not question_row.empty:
            # Assicurati che i nomi delle colonne siano corretti (es. 'domanda', 'risposta_attesa')
            # Questi dovrebbero corrispondere a come sono salvati/caricati in data_utils.py
            q = question_row.iloc[0].get('domanda', question_row.iloc[0].get('question', ''))
            a = question_row.iloc[0].get('risposta_attesa', question_row.iloc[0].get('expected_answer', ''))
            
            # Verifica che domanda e risposta non siano vuote
            if not q or not isinstance(q, str) or q.strip() == "":
                st.error(f"La domanda con ID {question_id} è vuota o non valida.")
                return None
                
            if not a or not isinstance(a, str) or a.strip() == "":
                st.warning(f"La risposta attesa per la domanda con ID {question_id} è vuota o non valida.")
                # Continuiamo comunque ma con una risposta vuota
                a = "Risposta non disponibile"
                
            return {'question': q, 'expected_answer': a}
    return None

# Seleziona set di domande per il test
add_section_title("Seleziona Set di Domande", icon="📚")
set_options = {}
if 'question_sets' in st.session_state and not st.session_state.question_sets.empty:
    for _, row in st.session_state.question_sets.iterrows():
        if 'questions' in row and row['questions']:
            set_options[row['id']] = f"{row['name']} ({len(row['questions'])} domande)"

if not set_options:
    st.warning("Nessun set di domande con domande associate. Creane uno in 'Gestione Set di Domande'.")
    st.stop()

selected_set_id = st.selectbox(
    "Seleziona un set di domande", 
    options=list(set_options.keys()),
    format_func=lambda x: set_options[x],
    key="select_question_set_for_test"
)

selected_set = st.session_state.question_sets[st.session_state.question_sets['id'] == selected_set_id].iloc[0]
questions_in_set = selected_set['questions']

# --- Selezione Modalità Test (UI Migliorata) ---
st.markdown("## 📌 Seleziona modalità test")

selection_container = st.container()
with selection_container:
    # CSS per lo styling (ridotto per brevità)
    st.markdown("""
    <style>
    .mode-box {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        text-align: center;
        transition: all 0.3s ease;
    }
    .selected-mode {
        border-color: #4CAF50;
        background-color: #f1f8e9;
    }
    .unselected-mode {
        border-color: #e0e0e0;
        background-color: #ffffff;
    }
    .mode-title {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 5px;
    }
    .mode-description {
        font-size: 0.9em;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col_sel1, col_sel2 = st.columns(2)
    current_mode_sel = st.session_state.test_mode
    
    with col_sel1:
        is_auto_sel = current_mode_sel == "Valutazione Automatica con LLM"
        auto_box_class = "selected-mode" if is_auto_sel else "unselected-mode"
        st.markdown(f'''
        <div class="mode-box {auto_box_class}">
            <div class="mode-title">🤖 Valutazione Automatica con LLM</div>
            <div class="mode-description">Genera e valuta risposte con modelli linguistici avanzati</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 使用回调函数的按钮
        button_text = "✓ MODALITÀ ATTIVA" if is_auto_sel else "✅ SELEZIONA"
        button_type = "primary" if is_auto_sel else "secondary"
        st.button(
            button_text, 
            key="llm_mode_btn", 
            use_container_width=True, 
            type=button_type,
            on_click=set_llm_mode_callback,
            disabled=is_auto_sel
        )
        
    with col_sel2:
        is_bm25_sel = current_mode_sel == "Valutazione con BM25"
        bm25_box_class = "selected-mode" if is_bm25_sel else "unselected-mode"
        st.markdown(f'''
        <div class="mode-box {bm25_box_class}">
            <div class="mode-title">🔍 Valutazione con BM25</div>
            <div class="mode-description">Analizza la somiglianza semantica basata sui termini condivisi</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 使用回调函数的按钮
        button_text = "✓ MODALITÀ ATTIVA" if is_bm25_sel else "✅ SELEZIONA"
        button_type = "primary" if is_bm25_sel else "secondary"
        st.button(
            button_text, 
            key="bm25_mode_btn", 
            use_container_width=True, 
            type=button_type,
            on_click=set_bm25_mode_callback,
            disabled=is_bm25_sel
        )

mode_icon_sel = "🤖" if st.session_state.test_mode == "Valutazione Automatica con LLM" else "🔍"
st.markdown(f'''
<div style="text-align: center; padding: 10px; background-color: #f0f0f0; border-radius: 5px; margin: 10px 0;">
    <strong>{mode_icon_sel} MODALITÀ SELEZIONATA: {st.session_state.test_mode}</strong>
</div>
''', unsafe_allow_html=True)
st.markdown("---")

# --- Opzioni API basate su Preset ---
add_section_title("Opzioni API basate su Preset", icon="🛠️")

preset_names_to_id = {preset['name']: preset['id'] for _, preset in st.session_state.api_presets.iterrows()}
preset_display_names = list(preset_names_to_id.keys())

def get_preset_config_by_name(name):
    preset_id = preset_names_to_id.get(name)
    if preset_id:
        return st.session_state.api_presets[st.session_state.api_presets["id"] == preset_id].iloc[0].to_dict()
    return None

# Seleziona preset per generazione risposta (comune a entrambe le modalità)
generation_preset_name = st.selectbox(
    "Seleziona Preset per Generazione Risposta LLM",
    options=preset_display_names,
    index=0 if preset_display_names else None, # Seleziona il primo di default
    key="generation_preset_select",
    help="Il preset API utilizzato per generare la risposta alla domanda."
)
st.session_state.selected_generation_preset_name = generation_preset_name

# Seleziona preset per valutazione (solo per modalità LLM)
if st.session_state.test_mode == "Valutazione Automatica con LLM":
    evaluation_preset_name = st.selectbox(
        "Seleziona Preset per Valutazione Risposta LLM",
        options=preset_display_names,
        index=0 if preset_display_names else None, # Seleziona il primo di default
        key="evaluation_preset_select",
        help="Il preset API utilizzato dall'LLM per valutare la similarità e correttezza della risposta generata."
    )
    st.session_state.selected_evaluation_preset_name = evaluation_preset_name
else:
    # Per BM25, non c'è un preset di valutazione LLM
    st.session_state.selected_evaluation_preset_name = None 

show_api_details = st.checkbox("Mostra Dettagli Chiamate API nei Risultati", value=False)

# --- Logica di Esecuzione Test ---
test_mode_selected = st.session_state.test_mode

if test_mode_selected == "Valutazione Automatica con LLM":
    st.header("Esecuzione: Valutazione Automatica con LLM")
    
    # 使用回调函数的按钮
    st.button(
        "🚀 Esegui Test con LLM", 
        key="run_llm_test_btn",
        on_click=run_llm_test_callback
    )
    
    # 处理测试执行
    if st.session_state.run_llm_test:
        st.session_state.run_llm_test = False  # 重置状态
        
        gen_preset_config = get_preset_config_by_name(st.session_state.selected_generation_preset_name)
        eval_preset_config = get_preset_config_by_name(st.session_state.selected_evaluation_preset_name)
        
        if not gen_preset_config or not eval_preset_config:
            st.error("Assicurati di aver selezionato preset validi per generazione e valutazione.")
        else:
            with st.spinner("Generazione risposte e valutazione LLM in corso..."):
                results = {}
                for q_id in questions_in_set:
                    q_data = get_question_data(q_id)
                    if q_data:
                        # Genera risposta di esempio usando LLM
                        generation_output = generate_example_answer_with_llm(q_data['question'], client_config=gen_preset_config, show_api_details=show_api_details)
                        actual_answer = generation_output["answer"]
                        generation_api_details = generation_output["api_details"]
                        
                        if actual_answer is None:
                            # Gestione errore generazione
                            results[q_id] = { 
                                'question': q_data['question'], 
                                'expected_answer': q_data['expected_answer'], 
                                'actual_answer': "Errore Generazione", 
                                'evaluation': {'score':0, 'explanation':'Generazione fallita'},
                                'generation_api_details': generation_api_details # Salva anche se la generazione fallisce
                            }
                            continue
                        
                        evaluation = evaluate_answer(q_data['question'], q_data['expected_answer'], actual_answer, client_config=eval_preset_config, show_api_details=show_api_details)
                        results[q_id] = {
                            'question': q_data['question'], 
                            'expected_answer': q_data['expected_answer'], 
                            'actual_answer': actual_answer, 
                            'evaluation': evaluation, # Questo conterrà i dettagli API della VALUTAZIONE
                            'generation_api_details': generation_api_details # Dettagli API della GENERAZIONE
                        }
                
                # Salva e visualizza risultati
                if results:
                    avg_score = sum(r['evaluation']['score'] for r in results.values()) / len(results) if results else 0
                    result_data = {
                        'set_name': selected_set['name'], 
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'avg_score': avg_score, 
                        'sample_type': 'Generata da LLM', 
                        'method': 'LLM',
                        'generation_preset': gen_preset_config['name'], 
                        'evaluation_preset': eval_preset_config['name'],
                        'questions': results
                    }
                    result_id = add_test_result(selected_set_id, result_data)
                    st.success(f"Test LLM completato! Punteggio medio: {avg_score:.2f}%")
                    
                    # Visualizzazione risultati dettagliati
                    st.subheader("Risultati Dettagliati")
                    for q_id, result in results.items():
                        with st.expander(f"Domanda: {result['question'][:50]}..."):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**Domanda:**", result['question'])
                                st.write("**Risposta Attesa:**", result['expected_answer'])
                            with col2:
                                st.write("**Risposta Generata:**", result['actual_answer'])
                                st.write("**Punteggio:**", f"{result['evaluation']['score']:.1f}%")
                                st.write("**Valutazione:**", result['evaluation']['explanation'])

elif test_mode_selected == "Valutazione con BM25":
    st.header("Esecuzione: Valutazione con BM25")
    
    # Parametri BM25
    k1_bm25 = st.slider("k1 (BM25)", 0.5, 3.0, 1.5, 0.1, key="bm25_k1_slider")
    b_bm25 = st.slider("b (BM25)", 0.0, 1.0, 0.75, 0.05, key="bm25_b_slider")
    high_threshold_bm25_val = st.slider("Soglia Match Alto (BM25 %)", 50, 100, 80, 1, key="bm25_high_thresh_slider")
    medium_threshold_bm25_val = st.slider("Soglia Match Medio (BM25 %)", 20, 80, 50, 1, key="bm25_medium_thresh_slider")
    
    # 使用回调函数的按钮
    st.button(
        "🚀 Esegui Test con BM25", 
        key="run_bm25_test_btn",
        on_click=run_bm25_test_callback
    )
    
    # 处理测试执行
    if st.session_state.run_bm25_test:
        st.session_state.run_bm25_test = False  # 重置状态
        
        gen_preset_config = get_preset_config_by_name(st.session_state.selected_generation_preset_name)
        if not gen_preset_config:
            st.error("Seleziona un preset valido per la generazione delle risposte.")
        else:
            with st.spinner("Generazione risposte e valutazione BM25 in corso..."):
                results = {}
                for q_id in questions_in_set:
                    q_data = get_question_data(q_id)
                    if q_data:
                        generation_output = generate_example_answer_with_llm(q_data['question'], client_config=gen_preset_config, show_api_details=show_api_details)
                        actual_answer = generation_output["answer"]
                        generation_api_details = generation_output["api_details"]

                        if actual_answer is None:
                            # Log più dettagliato dell'errore per diagnostica
                            st.error(f"Errore nella generazione della risposta per la domanda: {q_data['question'][:50]}...")
                            
                            # Salviamo informazioni più dettagliate nell'oggetto risultati
                            results[q_id] = { 
                                'question': q_data['question'], 
                                'expected_answer': q_data['expected_answer'], 
                                'actual_answer': "Errore Generazione", 
                                'similarity_score': 0, 
                                'match_level': 'basso',
                                'missing_keywords': [], 
                                'extra_keywords': [],
                                'suggestions': "Non è stato possibile generare una risposta per questa domanda. Verificare le impostazioni del preset API.",
                                'evaluation': {'score': 0, 'explanation': "Errore nella generazione della risposta."},
                                'generation_api_details': generation_api_details # Salva anche se la generazione fallisce
                            }
                            continue
                        
                        similarity_score = calcola_similarita_normalizzata(q_data['expected_answer'], actual_answer, k1=k1_bm25, b=b_bm25)
                        match_level = "alto" if similarity_score >= high_threshold_bm25_val else ("medio" if similarity_score >= medium_threshold_bm25_val else "basso")
                        missing_keywords, extra_keywords = analizza_parole_chiave(q_data['expected_answer'], actual_answer)
                        suggestions = genera_suggerimenti(missing_keywords, match_level)

                        results[q_id] = {
                            'question': q_data['question'], 
                            'expected_answer': q_data['expected_answer'], 
                            'actual_answer': actual_answer,
                            'similarity_score': similarity_score, 
                            'match_level': match_level, 
                            'missing_keywords': missing_keywords, 
                            'extra_keywords': extra_keywords, 
                            'suggestions': suggestions,
                            'evaluation': {'score': similarity_score, 'explanation': suggestions}, # Adattare per coerenza
                            'generation_api_details': generation_api_details # Dettagli API della GENERAZIONE
                        }
                
                # Salva e visualizza risultati
                if results:
                    avg_score = sum(r['similarity_score'] for r in results.values()) / len(results) if results else 0
                    result_data = {
                        'set_name': selected_set['name'], 
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'avg_score': avg_score, 
                        'sample_type': 'Generata da LLM', 
                        'method': 'BM25',
                        'generation_preset': gen_preset_config['name'],
                        'parameters': {
                            'k1': k1_bm25, 
                            'b': b_bm25, 
                            'high_threshold': high_threshold_bm25_val, 
                            'medium_threshold': medium_threshold_bm25_val
                        },
                        'questions': results
                    }
                    result_id = add_test_result(selected_set_id, result_data)
                    st.success(f"Test BM25 completato! Punteggio medio: {avg_score:.2f}%")
                    
                    # Visualizzazione risultati dettagliati
                    st.subheader("Risultati Dettagliati")
                    for q_id, result in results.items():
                        with st.expander(f"Domanda: {result['question'][:50]}..."):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**Domanda:**", result['question'])
                                st.write("**Risposta Attesa:**", result['expected_answer'])
                                st.write("**Risposta Generata:**", result['actual_answer'])
                            with col2:
                                st.write("**Punteggio Similarità:**", f"{result['similarity_score']:.1f}%")
                                st.write("**Livello Match:**", result['match_level'])
                                st.write("**Parole Chiave Mancanti:**", ", ".join(result['missing_keywords']) if result['missing_keywords'] else "Nessuna")
                                st.write("**Suggerimenti:**", result['suggestions'])
