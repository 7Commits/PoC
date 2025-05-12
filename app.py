import streamlit as st
import os
import pandas as pd
from pathlib import Path
import sys

# Aggiungi la directory corrente al percorso così possiamo importare da utils
sys.path.append(os.path.dirname(__file__))

from utils.data_utils import initialize_data, load_questions, load_question_sets, load_results

# Imposta la configurazione della pagina
st.set_page_config(
    page_title="LLM Test Evaluation Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializza lo stato della sessione
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

# Inizializza i file di dati se non esistono
if not st.session_state.initialized:
    initialize_data()
    st.session_state.initialized = True

# Carica i dati nello stato della sessione se non sono già caricati
if 'questions' not in st.session_state:
    st.session_state.questions = load_questions()

if 'question_sets' not in st.session_state:
    st.session_state.question_sets = load_question_sets()

if 'results' not in st.session_state:
    st.session_state.results = load_results()

# Configurazione API
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.environ.get('OPENAI_API_KEY', '')

if 'endpoint' not in st.session_state:
    st.session_state.endpoint = 'https://api.openai.com/v1'

if 'model' not in st.session_state:
    st.session_state.model = 'gpt-4o'

if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.0

if 'max_tokens' not in st.session_state:
    st.session_state.max_tokens = 1000

# Applicazione principale
st.title("🧠 LLM Test Evaluation Platform - Artificial QI")

# Importa utilità UI
from utils.ui_utils import add_global_styles, add_page_header

# Aggiungi CSS personalizzato e stili globali
add_global_styles()

st.markdown("""
<style>
    /* Stile migliorato per il box delle funzionalità */
    .feature-box {
        background-color: white;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        border-top: 4px solid #4F6AF0;
        box-shadow: 0 6px 18px rgba(79, 106, 240, 0.1);
        transition: all 0.3s ease;
    }
    
    .feature-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(79, 106, 240, 0.15);
    }
    
    .feature-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 15px;
        color: #333;
        display: flex;
        align-items: center;
    }
    
    .feature-description {
        font-size: 1rem;
        color: #555;
        line-height: 1.5;
    }
    
    .icon-large {
        font-size: 2rem;
        margin-right: 0.75rem;
        background: linear-gradient(135deg, #F0F4FF, #E6EBFF);
        width: 50px;
        height: 50px;
        line-height: 50px;
        text-align: center;
        border-radius: 50%;
        box-shadow: 0 4px 10px rgba(79, 106, 240, 0.1);
    }
    
    .welcome-section {
        margin-bottom: 2.5rem;
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #4F6AF0;
    }
    
    .welcome-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #4F6AF0;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #555;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    
    /* Sezione per iniziare */
    .getting-started {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.05);
        border-left: 5px solid #4F6AF0;
    }
    
    .getting-started h3 {
        color: #4F6AF0;
        margin-bottom: 1rem;
    }
    
    .getting-started ol {
        padding-left: 1.5rem;
    }
    
    .getting-started li {
        margin-bottom: 0.75rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# Pagina di benvenuto dell'app principale
st.markdown("""
<div class="welcome-section">
    <h1 class="welcome-title">🧠 Piattaforma di Valutazione LLM</h1>
    <p class="subtitle">Una piattaforma completa per valutare le risposte LLM con diversi provider AI tra cui OpenAI, Anthropic e X.AI</p>
</div>
""", unsafe_allow_html=True)

# Box delle funzionalità con icone e stile migliorato
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">
            <span class="icon-large">📋</span>
            Gestione delle Domande
        </p>
        <p class="feature-description">
            Crea, modifica e organizza le tue domande di test con le risposte previste.
            Costruisci set di test completi per valutare le risposte LLM in modo efficiente.
        </p>
    </div>
    
    <div class="feature-box">
        <p class="feature-title">
            <span class="icon-large">🔌</span>
            Supporto Multi-Provider API
        </p>
        <p class="feature-description">
            Connettiti a OpenAI, Anthropic o X.AI con selezione personalizzata del modello.
            Configura parametri API e verifica le connessioni con feedback in tempo reale.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <p class="feature-title">
            <span class="icon-large">🧪</span>
            Valutazione Automatizzata
        </p>
        <p class="feature-description">
            Esegui test con punteggio automatico rispetto alle risposte previste.
            Visualizza analisi dettagliate con metriche di somiglianza, correttezza e completezza.
        </p>
    </div>
    
    <div class="feature-box">
        <p class="feature-title">
            <span class="icon-large">📊</span>
            Analisi Avanzata
        </p>
        <p class="feature-description">
            Visualizza i risultati dei test con grafici interattivi e metriche dettagliate.
            Accedi alle informazioni complete delle richieste e risposte API per debug e ottimizzazione.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="getting-started">
    <h3>🚀 Iniziare</h3>
    <ol>
        <li>Configura le tue credenziali API nella pagina <strong>Configurazione API</strong></li>
        <li>Crea domande e risposte previste nella pagina <strong>Gestione Domande</strong></li>
        <li>Organizza le domande in set nella pagina <strong>Gestione Set di Domande</strong></li>
        <li>Esegui valutazioni nella pagina <strong>Esecuzione Test</strong></li>
        <li>Visualizza e analizza i risultati nella pagina <strong>Visualizzazione Risultati</strong></li>
    </ol>
    <p>Utilizza la barra laterale a sinistra per navigare tra queste funzionalità.</p>
</div>
""", unsafe_allow_html=True)

# Crea la navigazione della barra laterale con stile migliorato
st.sidebar.markdown("""
<style>
    /* Stili migliorati per la barra laterale */
    .sidebar-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #4F6AF0;
        margin-bottom: 1.25rem;
        text-align: center;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid rgba(79, 106, 240, 0.2);
    }

    .sidebar-subtitle {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 1.25rem;
        margin-bottom: 0.75rem;
        color: #333;
        background: linear-gradient(135deg, #F0F4FF, #E6EBFF);
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
    }

    .sidebar-menu {
        margin-bottom: 2rem;
    }

    /* Rendi più attraenti le opzioni di navigazione della barra laterale */
    .sidebar .sidebar-content {
        background-color: #F8FAFF;
    }

    /* Stile degli elementi della barra laterale */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Aggiungi animazione alla barra laterale */
    @keyframes sidebar-appear {
        0% { opacity: 0; transform: translateX(-20px); }
        100% { opacity: 1; transform: translateX(0); }
    }

    .sidebar-title, .sidebar-subtitle {
        animation: sidebar-appear 0.5s ease forwards;
    }
</style>

<div class="sidebar-title">🧭 Centro di Navigazione</div>
<div class="sidebar-subtitle">📚 Funzioni Principali</div>
""", unsafe_allow_html=True)

# Opzioni di navigazione
pages = {
    "Home": "Home",
    "Gestione Domande": "pages/gestione_domande.py",
    "Gestione Set di Domande": "pages/gestione_set.py",
    "Configurazione API": "pages/api_configurazione.py",
    "Esecuzione Test": "pages/esecuzione_test.py",
    "Visualizzazione Risultati": "pages/visualizza_risultati.py"
}

# Home è gestita in questo file, le altre sono in file separati
