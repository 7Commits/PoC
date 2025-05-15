import streamlit as st
import os
import sys
import uuid # Aggiunto per generare ID per i preset
import pandas as pd # Aggiunto per DataFrame dei preset

# Aggiungi la directory genitore al percorso in modo da poter importare da utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.openai_utils import (
    test_api_connection, DEFAULT_MODEL, DEFAULT_ENDPOINT,
    OPENAI_MODELS, ANTHROPIC_MODELS, XAI_MODELS,
    get_available_models_for_endpoint
)
from utils.ui_utils import add_page_header, add_section_title, create_card
from utils.data_utils import load_api_presets, save_api_presets, initialize_data # Import per i preset

# Inizializza i file di dati, inclusi i preset API, se non esistono.
initialize_data()

# Aggiungi un\\'intestazione stilizzata
add_page_header(
    "Configurazione API LLM",
    icon="🔌",
    description="Configura il tuo provider API, modello e impostazioni di connessione"
)

# Definizioni costanti per chiarezza
ENDPOINT_OPTIONS = {
    "OpenAI": "https://api.openai.com/v1",
    "Anthropic": "https://api.anthropic.com/v1",
    "X.AI (Grok)": "https://api.x.ai/v1",
    "Personalizzato": "custom"
}

def handle_provider_change():
    selected_provider_name = st.session_state.api_provider_selectbox
    if selected_provider_name == "Personalizzato":
        current_custom_url = st.session_state.get("custom_endpoint_text_input", "")
        st.session_state.endpoint = current_custom_url if current_custom_url else "custom"
    else:
        st.session_state.endpoint = ENDPOINT_OPTIONS[selected_provider_name]

    current_model = st.session_state.get("model", DEFAULT_MODEL)
    models_for_new_endpoint = get_available_models_for_endpoint(st.session_state.endpoint)
    if st.session_state.endpoint == "custom":
        pass # Non cambiare modello automaticamente per custom
    elif current_model not in models_for_new_endpoint:
        if models_for_new_endpoint:
            st.session_state.model = models_for_new_endpoint[0]
        else:
            st.session_state.model = ""
            st.session_state.use_custom_model_checkbox = True

def handle_custom_endpoint_change():
    custom_url = st.session_state.custom_endpoint_text_input
    if custom_url:
        st.session_state.endpoint = custom_url
    elif st.session_state.api_provider_selectbox == "Personalizzato":
        st.session_state.endpoint = "custom"

# Callback function for applying preset from selectbox
def apply_preset_from_selectbox_callback():
    selected_preset_id = st.session_state.get("preset_action_selectbox")
    if selected_preset_id and selected_preset_id != "": # Check it\\\'s not the placeholder value ""
        presets_df = st.session_state.api_presets
        preset_to_apply_df = presets_df[presets_df["id"] == selected_preset_id]

        if not preset_to_apply_df.empty:
            preset_to_apply = preset_to_apply_df.iloc[0]
            st.session_state.api_provider_selectbox = preset_to_apply["provider_name"]
            st.session_state.endpoint = preset_to_apply["endpoint"]
            st.session_state.api_key = preset_to_apply["api_key"]
            st.session_state.model = preset_to_apply["model"]
            st.session_state.temperature = float(preset_to_apply["temperature"])
            st.session_state.max_tokens = int(preset_to_apply["max_tokens"])

            available_models_for_loaded = get_available_models_for_endpoint(st.session_state.endpoint)
            if st.session_state.endpoint == "custom" or \
               not available_models_for_loaded or \
               st.session_state.model not in available_models_for_loaded:
                st.session_state.use_custom_model_checkbox = True
            else:
                st.session_state.use_custom_model_checkbox = False

            if preset_to_apply["provider_name"] == "Personalizzato":
                st.session_state.custom_endpoint_text_input = preset_to_apply["endpoint"]
            else:
                if "custom_endpoint_text_input" in st.session_state: # Clear if it exists and provider is not custom
                    st.session_state.custom_endpoint_text_input = ""
            
            st.success(f"Preset 	\'{preset_to_apply['name']}	\' applicato.")
            st.rerun()

# Callback function for saving a new preset
def save_preset_callback():
    preset_name_from_input = st.session_state.get("new_preset_name_input_field", "")
    if preset_name_from_input:
        if preset_name_from_input in st.session_state.api_presets["name"].values:
            st.warning(f"Un preset con nome 	\'{preset_name_from_input}	\' esiste già.")
        else:
            new_id = str(uuid.uuid4())
            new_preset_df = pd.DataFrame([{
                "id": new_id,
                "name": preset_name_from_input,
                "provider_name": st.session_state.api_provider_selectbox,
                "endpoint": st.session_state.endpoint,
                "api_key": st.session_state.api_key, 
                "model": st.session_state.model,
                "temperature": st.session_state.temperature,
                "max_tokens": st.session_state.max_tokens
            }])
            st.session_state.api_presets = pd.concat([st.session_state.api_presets, new_preset_df], ignore_index=True)
            save_api_presets(st.session_state.api_presets)
            st.success(f"Preset 	\'{preset_name_from_input}	\' salvato.")
            
            if "new_preset_name_input_field" in st.session_state:
                del st.session_state.new_preset_name_input_field # Clears the input field for next use
            
            st.session_state.preset_action_selectbox = new_id # Select the newly saved preset
            st.rerun()
    else:
        st.warning("Inserisci un nome per salvare il preset.")

# Inizializzazione dello stato della sessione
if "endpoint" not in st.session_state: st.session_state.endpoint = DEFAULT_ENDPOINT
if "model" not in st.session_state: st.session_state.model = DEFAULT_MODEL
if "api_key" not in st.session_state: st.session_state.api_key = ""
if "temperature" not in st.session_state: st.session_state.temperature = 0.0
if "max_tokens" not in st.session_state: st.session_state.max_tokens = 1000
if "use_custom_model_checkbox" not in st.session_state: st.session_state.use_custom_model_checkbox = False
if "api_presets" not in st.session_state: st.session_state.api_presets = load_api_presets()
if "preset_action_selectbox" not in st.session_state: st.session_state.preset_action_selectbox = "" 
if "new_preset_name_input_field" not in st.session_state: st.session_state.new_preset_name_input_field = ""

if "api_provider_selectbox" not in st.session_state:
    current_endpoint_in_state_init = st.session_state.endpoint
    initial_provider_name_for_selectbox_init = "Personalizzato"
    if current_endpoint_in_state_init == "custom":
        initial_provider_name_for_selectbox_init = "Personalizzato"
    elif current_endpoint_in_state_init in ENDPOINT_OPTIONS.values():
        for name, url_val in ENDPOINT_OPTIONS.items():
            if url_val == current_endpoint_in_state_init:
                initial_provider_name_for_selectbox_init = name
                break
    st.session_state.api_provider_selectbox = initial_provider_name_for_selectbox_init

tabs = st.tabs(["Configurazione Generale", "Impostazioni Avanzate", "Linee Guida per l\\'Utilizzo dell\\'API"])

with tabs[0]:
    st.subheader("Preset API")
    
    def get_preset_display_options_for_apply():
        presets = st.session_state.api_presets
        options = {"": "--- Seleziona Preset ---"} 
        for _, row in presets.iterrows():
            options[row["id"]] = row["name"]
        return options

    preset_apply_options = get_preset_display_options_for_apply()

    def delete_selected_preset_callback():
        id_to_delete = st.session_state.get("preset_action_selectbox", "")
        preset_name_to_delete = preset_apply_options.get(id_to_delete, "Selezionato")
        if not isinstance(st.session_state.api_presets, pd.DataFrame) or 'id' not in st.session_state.api_presets.columns:
            st.error("Errore interno: la tabella dei preset non è configurata correttamente.")
            return
        st.session_state.api_presets = st.session_state.api_presets[st.session_state.api_presets["id"] != id_to_delete]
        save_api_presets(st.session_state.api_presets)
        st.success(f"Preset '{preset_name_to_delete}' eliminato.")
        st.session_state.preset_action_selectbox = "" 
        st.rerun()

    current_selectbox_preset_id = st.session_state.get("preset_action_selectbox", "")
    options_keys = list(preset_apply_options.keys())
    try:
        idx = options_keys.index(current_selectbox_preset_id)
    except ValueError:
        idx = 0 

    col_name, col_select, col_save, col_delete = st.columns([3, 3, 1, 1]) 

    with col_name:
        st.text_input(
            "Nome Preset:", 
            placeholder="Es. Config OpenAI", 
            key="new_preset_name_input_field",
            label_visibility="collapsed"
        )

    with col_select:
        st.selectbox(
            "Carica/Elimina Preset:",
            options=options_keys,
            format_func=lambda x: preset_apply_options.get(x, "Seleziona..."),
            key="preset_action_selectbox",
            on_change=apply_preset_from_selectbox_callback,
            index=idx,
            label_visibility="collapsed", 
            help="Seleziona un preset per caricarlo o per prepararlo all\\'eliminazione."
        )

    with col_save:
        st.button("💾", 
                  on_click=save_preset_callback, 
                  key="save_current_as_preset_icon_btn", 
                  use_container_width=True, 
                  help="Salva le impostazioni API correnti come un nuovo preset.")

    with col_delete:
        id_to_delete_check = st.session_state.get("preset_action_selectbox", "")
        can_delete = id_to_delete_check and id_to_delete_check != "" and \
                     isinstance(st.session_state.api_presets, pd.DataFrame) and \
                     'id' in st.session_state.api_presets.columns and \
                     not st.session_state.api_presets[st.session_state.api_presets["id"] == id_to_delete_check].empty

        st.button("🗑️", 
                  key="delete_selected_preset_icon_btn", 
                  use_container_width=True, 
                  help=f"Elimina: {preset_apply_options.get(id_to_delete_check, 'Nessuno') if can_delete else 'Seleziona un preset'}", 
                  disabled=not can_delete,
                  on_click=delete_selected_preset_callback
        )
    st.markdown("---")

    add_section_title("Provider & Modello API", icon="🌐")
    col_config, col_info = st.columns([2, 1])

    with col_config:
        current_endpoint_in_state = st.session_state.endpoint
        initial_provider_name_for_selectbox = "Personalizzato"
        if current_endpoint_in_state == "custom":
            initial_provider_name_for_selectbox = "Personalizzato"
        elif current_endpoint_in_state in ENDPOINT_OPTIONS.values():
            for name, url_val in ENDPOINT_OPTIONS.items():
                if url_val == current_endpoint_in_state:
                    initial_provider_name_for_selectbox = name
                    break
        
        st.selectbox(
            "Seleziona Provider API",
            options=list(ENDPOINT_OPTIONS.keys()),
            index=list(ENDPOINT_OPTIONS.keys()).index(initial_provider_name_for_selectbox),
            key="api_provider_selectbox",
            on_change=handle_provider_change
        )
        selected_provider = st.session_state.api_provider_selectbox

        if selected_provider == "Personalizzato":
            custom_endpoint_initial_value = ""
            if st.session_state.endpoint != "custom" and st.session_state.endpoint not in ENDPOINT_OPTIONS.values():
                custom_endpoint_initial_value = st.session_state.endpoint
            st.text_input(
                "Endpoint API Personalizzato",
                value=st.session_state.get("custom_endpoint_text_input", custom_endpoint_initial_value),
                placeholder="Inserisci l\\'URL del tuo endpoint API personalizzato...",
                key="custom_endpoint_text_input",
                on_change=handle_custom_endpoint_change
            )

        api_key_label = "Chiave API"
        env_key_name = "API_KEY"
        if selected_provider == "OpenAI": api_key_label = "Chiave API OpenAI"; env_key_name = "OPENAI_API_KEY"
        elif selected_provider == "Anthropic": api_key_label = "Chiave API Anthropic"; env_key_name = "ANTHROPIC_API_KEY"
        elif selected_provider == "X.AI (Grok)": api_key_label = "Chiave API X.AI"; env_key_name = "XAI_API_KEY"
        
        env_api_key = os.environ.get(env_key_name, "")
        if env_api_key:
            st.success(f"{api_key_label} è configurata nelle variabili d\\'ambiente.")
            override_env_key = st.checkbox(f"Sovrascrivi {api_key_label} d\\'ambiente", value=st.session_state.get(f"override_{env_key_name}", False), key=f"override_{env_key_name}")
            if override_env_key:
                api_key_input_val = st.text_input(api_key_label, value=st.session_state.api_key, type="password", placeholder=f"Inserisci la tua {api_key_label}...")
                if api_key_input_val != st.session_state.api_key: st.session_state.api_key = api_key_input_val
            else: st.session_state.api_key = env_api_key
        else:
            api_key_input_val = st.text_input(api_key_label, value=st.session_state.api_key, type="password", placeholder=f"Inserisci la tua {api_key_label}...")
            if api_key_input_val != st.session_state.api_key: st.session_state.api_key = api_key_input_val

        available_models = get_available_models_for_endpoint(st.session_state.endpoint)
        current_model_in_state = st.session_state.get("model", DEFAULT_MODEL)
        if st.session_state.endpoint == "custom" or not available_models or current_model_in_state not in available_models:
            st.session_state.use_custom_model_checkbox = True
        elif available_models and current_model_in_state in available_models:
             st.session_state.use_custom_model_checkbox = False

        use_custom_model = st.checkbox("Usa nome modello personalizzato", value=st.session_state.use_custom_model_checkbox, key="use_custom_model_checkbox_widget")
        st.session_state.use_custom_model_checkbox = use_custom_model

        if use_custom_model:
            custom_model_name = st.text_input("Inserisci nome modello personalizzato", value=current_model_in_state if st.session_state.use_custom_model_checkbox else "", placeholder="Inserisci il nome esatto del modello...")
            if custom_model_name != current_model_in_state: st.session_state.model = custom_model_name
        else:
            if available_models:
                try: model_idx = available_models.index(current_model_in_state)
                except ValueError: model_idx = 0; st.session_state.model = available_models[model_idx]
                selected_model_from_list = st.selectbox("Seleziona Modello", options=available_models, index=model_idx)
                if selected_model_from_list != current_model_in_state: st.session_state.model = selected_model_from_list
            else: st.warning("Nessun modello predefinito disponibile. Inserisci un nome modello personalizzato sopra.")

        st.markdown("---")
        st.markdown("### Salva Impostazioni API")
        if st.button("Salva Impostazioni API Correnti", key="salva_impostazioni_api_btn", use_container_width=True):
            st.success("Impostazioni API correnti confermate e attive per questa sessione.")

        st.markdown("### Test di Connessione")
        test_col1_btn, test_col2_btn = st.columns([2, 1])
        with test_col1_btn:
            st.write("Testa la tua connessione API per assicurarti che le tue credenziali funzionino correttamente.")
        with test_col2_btn:
            if st.button("Testa Connessione API", use_container_width=True):
                if not st.session_state.api_key:
                    create_card("Chiave API Mancante", "Inserisci una chiave API prima di testare la connessione.", is_error=True, icon="🔑")
                else:
                    with st.spinner("Test della connessione..."):
                        success, message = test_api_connection()
                        if success:
                            create_card("Connessione Riuscita", message, is_success=True, icon="✅")
                        else:
                            create_card("Connessione Fallita", message, is_error=True, icon="⚠️")

    with col_info:
        st.subheader("Dettagli Endpoint e Chiamata API")
        provider_to_display_info = st.session_state.api_provider_selectbox
        actual_endpoint_to_display = st.session_state.endpoint
        api_usage_details = {
            "OpenAI": {"base_endpoint": ENDPOINT_OPTIONS["OpenAI"], "example_path": "/chat/completions", "method": "POST", "notes": "Utilizzato per generazione di testo, chat, embeddings, ecc.", "payload_example": f"```json\n{{\n  \"model\": \"{st.session_state.get('model', 'gpt-4o-mini')}\",\n  \"messages\": [\n    {{\"role\": \"user\", \"content\": \"Scrivi una poesia sui gatti.\"}}\n  ],\n  \"temperature\": {st.session_state.get('temperature', 0.0)},\n  \"max_tokens\": {st.session_state.get('max_tokens', 1000)}\n}}\n```"},
            "Anthropic": {"base_endpoint": ENDPOINT_OPTIONS["Anthropic"], "example_path": "/messages", "method": "POST", "notes": "Focalizzato su IA conversazionale sicura e affidabile.", "payload_example": f"```json\n{{\n  \"model\": \"{st.session_state.get('model', 'claude-3-opus-20240229')}\",\n  \"max_tokens\": {st.session_state.get('max_tokens', 1000)},\n  \"messages\": [\n    {{\"role\": \"user\", \"content\": \"Spiega la relatività generale.\"}}\n  ],\n  \"temperature\": {st.session_state.get('temperature', 0.0)}\n}}\n```"},
            "X.AI (Grok)": {"base_endpoint": ENDPOINT_OPTIONS["X.AI (Grok)"], "example_path": "/chat/completions", "method": "POST", "notes": "Modelli più recenti.", "payload_example": "*(Esempio non disponibile)*"},
            "Personalizzato": {"base_endpoint": actual_endpoint_to_display if actual_endpoint_to_display != 'custom' else 'Non specificato', "example_path": "/your_path", "method": "POST/GET", "notes": "Dipende dalla tua API.", "payload_example": "*(Dipende dalla tua API)*"}
        }
        if provider_to_display_info in api_usage_details:
            detail = api_usage_details[provider_to_display_info]
            st.markdown(f"**Provider:** {provider_to_display_info}")
            st.markdown(f"**Endpoint:** `{detail['base_endpoint']}`")
            st.markdown(f"**Percorso Esempio:** `{detail['example_path']}`")
            st.markdown(f"**Metodo:** `{detail['method']}`")
            st.markdown(f"**Note:** {detail['notes']}")
            st.markdown("**Payload Esempio:**")
            st.markdown(detail["payload_example"])
        else: st.info("Seleziona un provider.")

with tabs[1]: 
    add_section_title("Impostazioni Avanzate LLM", icon="⚙️")
    st.slider("Temperatura", min_value=0.0, max_value=2.0, value=st.session_state.temperature, step=0.01, key="temperature_slider", help="Controlla la casualità dell\\'output. Valori più bassi rendono l\\'output più deterministico.")
    if st.session_state.temperature_slider != st.session_state.temperature: st.session_state.temperature = st.session_state.temperature_slider
    
    st.number_input("Massimo Token", min_value=50, max_value=8000, value=st.session_state.max_tokens, step=10, key="max_tokens_input", help="Numero massimo di token da generare nell\\'output.")
    if st.session_state.max_tokens_input != st.session_state.max_tokens: st.session_state.max_tokens = st.session_state.max_tokens_input
    
    st.info("Le impostazioni di Temperatura e Massimo Token sono applicate globalmente quando si interagisce con l\\'LLM.")

with tabs[2]: 
    add_section_title("Linee Guida per l\\'Utilizzo Responsabile dell\\'API", icon="📜")
    st.markdown("""
    Quando si utilizzano API LLM, è fondamentale considerare le implicazioni etiche e di costo.
    - **Costi**: Le chiamate API possono comportare costi. Monitora il tuo utilizzo.
    - **Sicurezza**: Non esporre mai le tue chiavi API pubblicamente. Utilizza variabili d\\'ambiente o file di configurazione sicuri.
    - **Bias**: I modelli LLM possono riflettere bias presenti nei dati di addestramento. Sii consapevole e critico riguardo agli output.
    - **Privacy**: Non inviare informazioni sensibili o personali tramite API a meno che non sia strettamente necessario e conforme alle normative sulla privacy.
    - **Limiti di Rate**: Rispetta i limiti di rate dell\\'API per evitare interruzioni del servizio.
    """)


