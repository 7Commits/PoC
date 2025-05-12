import streamlit as st
import os
import sys

# Aggiungi la directory genitore al percorso in modo da poter importare da utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.openai_utils import (
    test_api_connection, DEFAULT_MODEL, DEFAULT_ENDPOINT,
    OPENAI_MODELS, ANTHROPIC_MODELS, XAI_MODELS,
    get_available_models_for_endpoint
)
from utils.ui_utils import add_page_header, add_section_title, create_card

# Aggiungi un'intestazione stilizzata
add_page_header(
    "Configurazione API LLM",
    icon="🔌",
    description="Configura il tuo provider API, modello e impostazioni di connessione"
)

# Crea schede per diversi provider API
tabs = st.tabs(["Configurazione Generale", "Impostazioni Avanzate", "Linee Guida per l'Utilizzo dell'API"])

with tabs[0]:
    add_section_title("Provider & Modello API", icon="🌐")

    # Selezione dell'endpoint
    endpoint_options = {
        "OpenAI": "https://api.openai.com/v1",
        "Anthropic": "https://api.anthropic.com/v1",
        "X.AI (Grok)": "https://api.x.ai/v1",
        "Personalizzato": "custom"  # Tradotto "Custom" in "Personalizzato"
    }

    # Ottieni l'endpoint corrente dallo stato della sessione o predefinito
    current_endpoint = st.session_state.get('endpoint', DEFAULT_ENDPOINT)

    # Se l'endpoint corrente non è nelle nostre opzioni, è personalizzato
    selected_endpoint_name = "Personalizzato"  # Tradotto "Custom" in "Personalizzato"
    for name, url in endpoint_options.items():
        if url == current_endpoint:
            selected_endpoint_name = name
            break

    # Crea la selectbox per la selezione dell'endpoint
    endpoint_selection = st.selectbox(
        "Seleziona Provider API",
        options=list(endpoint_options.keys()),
        index=list(endpoint_options.keys()).index(selected_endpoint_name)
    )

    # Gestisci endpoint personalizzato
    if endpoint_selection == "Personalizzato":  # Tradotto "Custom" in "Personalizzato"
        custom_endpoint = st.text_input(
            "Endpoint API Personalizzato",
            value="" if current_endpoint in endpoint_options.values() else current_endpoint,
            placeholder="Inserisci l'URL del tuo endpoint API personalizzato..."
        )
        if custom_endpoint:
            st.session_state.endpoint = custom_endpoint
    else:
        st.session_state.endpoint = endpoint_options[endpoint_selection]

    # Ottieni l'etichetta della chiave API in base all'endpoint selezionato
    api_key_label = "Chiave API"
    if endpoint_selection == "OpenAI":
        api_key_label = "Chiave API OpenAI"
        env_key_name = "OPENAI_API_KEY"
    elif endpoint_selection == "Anthropic":
        api_key_label = "Chiave API Anthropic"
        env_key_name = "ANTHROPIC_API_KEY"
    elif endpoint_selection == "X.AI (Grok)":
        api_key_label = "Chiave API X.AI"
        env_key_name = "XAI_API_KEY"
    else:
        api_key_label = "Chiave API"
        env_key_name = "API_KEY"

    # Visualizza la variabile d'ambiente corrente se disponibile
    env_api_key = os.environ.get(env_key_name, '')
    if env_api_key:
        st.success(f"{api_key_label} è configurata nelle variabili d'ambiente.")

        # Opzione per sovrascrivere
        override = st.checkbox("Sovrascrivi chiave API d'ambiente", value=False)

        if override:
            api_key = st.text_input(
                api_key_label,
                value=st.session_state.get('api_key', env_api_key),
                type="password",
                placeholder=f"Inserisci la tua {api_key_label}..."
            )
        else:
            st.session_state.api_key = env_api_key
            api_key = env_api_key
    else:
        api_key = st.text_input(
            api_key_label,
            value=st.session_state.get('api_key', ''),
            type="password",
            placeholder=f"Inserisci la tua {api_key_label}..."
        )

    # Salva la chiave API nello stato della sessione
    if api_key != st.session_state.get('api_key', ''):
        st.session_state.api_key = api_key

    # Selezione del modello in base all'endpoint
    available_models = get_available_models_for_endpoint(st.session_state.get('endpoint', DEFAULT_ENDPOINT))

    # Ottieni modello corrente o predefinito
    current_model = st.session_state.get('model', DEFAULT_MODEL)

    # Opzione per utilizzare modelli predefiniti o modello personalizzato
    use_custom_model = st.checkbox("Usa nome modello personalizzato",
                                   value=current_model not in available_models)

    if use_custom_model:
        # Consenti all'utente di inserire un nome di modello personalizzato
        selected_model = st.text_input(
            "Inserisci nome modello personalizzato",
            value=current_model if current_model not in available_models else "",
            placeholder="Inserisci il nome esatto del modello (es. gpt-4o-mini, claude-3-opus-20240229)..."
        )
        # Se non viene fornito alcun modello personalizzato, utilizza quello predefinito
        if not selected_model:
            selected_model = DEFAULT_MODEL
    else:
        # Assicurati che il modello corrente sia nell'elenco dei modelli disponibili
        if current_model not in available_models:
            current_model = available_models[
                0] if available_models else DEFAULT_MODEL  # Aggiunto controllo per lista vuota

        # Utilizza selectbox per modelli predefiniti
        selected_model = st.selectbox(
            "Seleziona Modello",
            options=available_models,
            index=available_models.index(current_model) if available_models and current_model in available_models else 0
            # Aggiunto controllo
        )

    # Salva il modello nello stato della sessione
    if selected_model != st.session_state.get('model', DEFAULT_MODEL):
        st.session_state.model = selected_model

    # Crea card per il test di connessione
    st.markdown("### Test di Connessione")

    test_col1, test_col2 = st.columns([2, 1])

    with test_col1:
        st.write("Testa la tua connessione API per assicurarti che le tue credenziali funzionino correttamente.")

    with test_col2:
        # Test di connessione
        if st.button("Testa Connessione API", use_container_width=True):
            if not api_key:
                create_card("Chiave API Mancante", "Inserisci una chiave API prima di testare la connessione.",
                            is_error=True, icon="🔑")
            else:
                with st.spinner("Test della connessione..."):
                    success, message = test_api_connection()

                    if success:
                        create_card("Connessione Riuscita", message, is_success=True, icon="✅")
                    else:
                        create_card("Connessione Fallita", message, is_error=True, icon="⚠️")

with tabs[1]:
    add_section_title("Impostazioni Avanzate", icon="⚙️")

    create_card(
        "Utilizzo Impostazioni",
        "Queste impostazioni verranno applicate a tutte le richieste di valutazione sulla piattaforma.",
        icon="ℹ️"
    )

    # Impostazione della temperatura
    temperature = st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get('temperature', 0.0),
        step=0.1,
        help="Controlla la casualità: 0 è più deterministico, 1 è più creativo."
    )

    # Salva la temperatura nello stato della sessione
    if temperature != st.session_state.get('temperature', 0.0):
        st.session_state.temperature = temperature

    # Impostazione max token
    max_tokens = st.slider(
        "Token Massimi Risposta",
        min_value=100,
        max_value=4000,
        value=st.session_state.get('max_tokens', 1000),
        step=100,
        help="Numero massimo di token da generare nella risposta."
    )

    # Salva max token nello stato della sessione
    if max_tokens != st.session_state.get('max_tokens', 1000):
        st.session_state.max_tokens = max_tokens

with tabs[2]:
    add_section_title("Utilizzo API & Linee Guida", icon="📚")

    # Prima card - Come funziona l'utilizzo dell'API
    create_card(
        "Come Funziona la Valutazione API",
        """
        <ol>
          <li>Inviamo la domanda, la risposta attesa e la risposta effettiva all'API LLM selezionata</li>
          <li>Il modello AI analizza il contenuto e fornisce un punteggio dettagliato:</li>
          <ul>
            <li><b>Somiglianza (0-100)</b>: Quanto sono semanticamente simili le risposte</li>
            <li><b>Correttezza (0-100)</b>: Accuratezza fattuale della risposta effettiva</li>
            <li><b>Completezza (0-100)</b>: Se tutti i punti chiave sono coperti</li>
          </ul>
          <li>L'AI fornisce un punteggio complessivo e un feedback esplicativo</li>
        </ol>
        """,
        icon="🔄"
    )

    # Crea colonne per card aggiuntive
    col1, col2 = st.columns(2)

    with col1:
        # Considerazioni sui costi
        create_card(
            "Considerazioni sui Costi",
            """
            <ul>
              <li>L'utilizzo dei token dipende dalla lunghezza dell'input/output</li>
              <li>Domande e risposte più lunghe utilizzano più token</li>
              <li>L'app minimizza l'utilizzo dei token ove possibile</li>
              <li>Provider diversi hanno modelli di prezzo diversi</li>
              <li>I modelli avanzati costano tipicamente di più per token</li>
            </ul>
            """,
            icon="💰"
        )

    with col2:
        # Note sulla sicurezza
        create_card(
            "Note sulla Sicurezza",
            """
            <ul>
              <li>Le chiavi API sono memorizzate solo nello stato della sessione</li>
              <li>Per la produzione, utilizzare variabili d'ambiente</li>
              <li>Assicurati una corretta configurazione della fatturazione con il tuo provider</li>
              <li>Nessun dato viene memorizzato oltre la sessione del browser</li>
              <li>I risultati vengono salvati localmente nella cartella dati dell'app</li>
            </ul>
            """,
            icon="🔒"
        )

    # Card di confronto dei provider
    st.write("")  # Aggiungi un po' di spazio
    create_card(
        "Confronto Provider API",
        """
        <table style="width:100%; border-collapse: collapse;">
          <tr style="background-color: #eef2ff;">
            <th style="padding:8px; text-align:left;">Provider</th>
            <th style="padding:8px; text-align:left;">Punti di Forza</th>
            <th style="padding:8px; text-align:left;">Casi d'Uso Ideali</th>
          </tr>
          <tr>
            <td style="padding:8px;"><b>OpenAI</b></td>
            <td style="padding:8px;">Ampiamente utilizzato, documentazione estesa, vasta gamma di modelli</td>
            <td style="padding:8px;">Valutazione generale, ragionamento complesso, punteggio coerente</td>
          </tr>
          <tr style="background-color: #f8f9ff;">
            <td style="padding:8px;"><b>Anthropic</b></td>
            <td style="padding:8px;">Forte focus sulla sicurezza, gestione dettagliata del contesto</td>
            <td style="padding:8px;">Valutazione sfumata, considerazioni etiche, contenuti lunghi</td>
          </tr>
          <tr>
            <td style="padding:8px;"><b>X.AI (Grok)</b></td>
            <td style="padding:8px;">Modelli più recenti, approccio alternativo</td>
            <td style="padding:8px;">Analisi comparativa, conoscenza di dominio specializzata</td>
          </tr>
        </table>
        """,
        icon="📊"
    )
