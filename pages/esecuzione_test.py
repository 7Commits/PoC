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
    evaluate_answer, generate_example_answer_with_llm  # Client viene creato internamente
)
from utils.ui_utils import add_page_header, add_section_title, create_card


# === FUNZIONI DI CALLBACK ===

def set_llm_mode_callback():
    """Funzione di callback: imposta la modalità LLM"""
    if st.session_state.test_mode != "Valutazione Automatica con LLM":
        st.session_state.test_mode = "Valutazione Automatica con LLM"
        st.session_state.mode_changed = True


def run_llm_test_callback():
    """Funzione di callback: esegue il test LLM"""
    st.session_state.run_llm_test = True


# === Inizializzazione delle variabili di stato ===
if 'test_mode' not in st.session_state:
    st.session_state.test_mode = "Valutazione Automatica con LLM"
if 'mode_changed' not in st.session_state:
    st.session_state.mode_changed = False
if 'run_llm_test' not in st.session_state:
    st.session_state.run_llm_test = False
if 'run_bm25_test' not in st.session_state:
    st.session_state.run_bm25_test = False

# Gestisce il cambio di modalità
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
    st.error(
        "Nessun preset API configurato. Vai alla pagina 'Gestione Preset API' per crearne almeno uno prima di eseguire i test.")
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
    index=0 if preset_display_names else None,  # Seleziona il primo di default
    key="generation_preset_select",
    help="Il preset API utilizzato per generare la risposta alla domanda."
)
st.session_state.selected_generation_preset_name = generation_preset_name

# Seleziona preset per valutazione (solo per modalità LLM)
if st.session_state.test_mode == "Valutazione Automatica con LLM":
    evaluation_preset_name = st.selectbox(
        "Seleziona Preset per Valutazione Risposta LLM",
        options=preset_display_names,
        index=0 if preset_display_names else None,  # Seleziona il primo di default
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

    # Pulsante che utilizza la funzione di callback
    st.button(
        "🚀 Esegui Test con LLM",
        key="run_llm_test_btn",
        on_click=run_llm_test_callback
    )

    # Gestisce l'esecuzione del test
    if st.session_state.run_llm_test:
        st.session_state.run_llm_test = False  # Resetta lo stato

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
                        generation_output = generate_example_answer_with_llm(q_data['question'],
                                                                             client_config=gen_preset_config,
                                                                             show_api_details=show_api_details)
                        actual_answer = generation_output["answer"]
                        generation_api_details = generation_output["api_details"]

                        if actual_answer is None:
                            # Gestione errore generazione
                            results[q_id] = {
                                'question': q_data['question'],
                                'expected_answer': q_data['expected_answer'],
                                'actual_answer': "Errore Generazione",
                                'evaluation': {'score': 0, 'explanation': 'Generazione fallita'},
                                'generation_api_details': generation_api_details
                                # Salva anche se la generazione fallisce
                            }
                            continue

                        evaluation = evaluate_answer(q_data['question'], q_data['expected_answer'], actual_answer,
                                                     client_config=eval_preset_config,
                                                     show_api_details=show_api_details)
                        results[q_id] = {
                            'question': q_data['question'],
                            'expected_answer': q_data['expected_answer'],
                            'actual_answer': actual_answer,
                            'evaluation': evaluation,  # Questo conterrà i dettagli API della VALUTAZIONE
                            'generation_api_details': generation_api_details  # Dettagli API della GENERAZIONE
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

