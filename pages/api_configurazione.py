import streamlit as st
import os
import sys
import uuid
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.openai_utils import (
    test_api_connection, DEFAULT_MODEL, DEFAULT_ENDPOINT,
    OPENAI_MODELS, ANTHROPIC_MODELS, 
    get_available_models_for_endpoint
)
from utils.ui_utils import add_page_header, add_section_title, create_card
from utils.data_utils import load_api_presets, save_api_presets, initialize_data

initialize_data()

add_page_header(
    "Gestione Preset API",
    icon="⚙️",
    description="Crea, visualizza, testa ed elimina i preset di configurazione API per LLM."
)

# Stato della sessione per la gestione del form di creazione/modifica preset
if "editing_preset" not in st.session_state: st.session_state.editing_preset = False
if "current_preset_edit_id" not in st.session_state: st.session_state.current_preset_edit_id = None # None per nuovo, ID per modifica
if "preset_form_data" not in st.session_state: st.session_state.preset_form_data = {}

# Carica i preset API (DataFrame)
if "api_presets" not in st.session_state:
    st.session_state.api_presets = load_api_presets()

ENDPOINT_OPTIONS = {
    "OpenAI": DEFAULT_ENDPOINT,
    "Anthropic": "https://api.anthropic.com/v1", # Esempio, potrebbe variare
    # Aggiungi altri provider predefiniti qui
    "Personalizzato": "custom" 
}

# Funzioni di callback per i pulsanti del form
def start_new_preset_edit():
    st.session_state.editing_preset = True
    st.session_state.current_preset_edit_id = None # Indica nuovo preset
    st.session_state.preset_form_data = {
        "name": "",
        "provider_name": list(ENDPOINT_OPTIONS.keys())[0],
        "endpoint": list(ENDPOINT_OPTIONS.values())[0],
        "api_key": "",
        "model": DEFAULT_MODEL,
        "temperature": 0.0,
        "max_tokens": 1000
    }
    # Aggiorna i modelli disponibili per il provider di default
    st.session_state.preset_form_data["available_models"] = get_available_models_for_endpoint(
        st.session_state.preset_form_data["provider_name"],
        st.session_state.preset_form_data["endpoint"],
        st.session_state.preset_form_data["api_key"]
    )
    if st.session_state.preset_form_data["available_models"]:
         st.session_state.preset_form_data["model"] = st.session_state.preset_form_data["available_models"][0]
    else:
        st.session_state.preset_form_data["model"] = DEFAULT_MODEL

def start_existing_preset_edit(preset_id):
    preset_to_edit = st.session_state.api_presets[st.session_state.api_presets["id"] == preset_id].iloc[0].to_dict()
    st.session_state.editing_preset = True
    st.session_state.current_preset_edit_id = preset_id
    st.session_state.preset_form_data = preset_to_edit.copy()
    # Assicura che i campi numerici siano del tipo corretto per gli slider/number_input
    st.session_state.preset_form_data["temperature"] = float(st.session_state.preset_form_data.get("temperature", 0.0))
    st.session_state.preset_form_data["max_tokens"] = int(st.session_state.preset_form_data.get("max_tokens", 1000))
    st.session_state.preset_form_data["available_models"] = get_available_models_for_endpoint(
        st.session_state.preset_form_data["provider_name"],
        st.session_state.preset_form_data["endpoint"],
        st.session_state.preset_form_data["api_key"]
    )
    # Se il modello salvato non è nella lista, mantienilo ma avvisa o permetti di cambiarlo
    if st.session_state.preset_form_data["model"] not in st.session_state.preset_form_data["available_models"]:
        st.session_state.preset_form_data["available_models"].append(st.session_state.preset_form_data["model"]) # Aggiungilo per permettere la selezione

def cancel_preset_edit():
    st.session_state.editing_preset = False
    st.session_state.current_preset_edit_id = None
    st.session_state.preset_form_data = {}

def save_preset_from_form():
    form_data = st.session_state.preset_form_data
    preset_name = form_data.get("name", "").strip()
    if not preset_name:
        st.error("Il nome del preset non può essere vuoto.")
        return

    current_id = st.session_state.current_preset_edit_id
    presets_df = st.session_state.api_presets

    # Controlla se il nome del preset esiste già (escludendo il preset corrente se in modifica)
    existing_names = presets_df["name"].tolist()
    if current_id:
        current_preset_original_name = presets_df[presets_df["id"] == current_id].iloc[0]["name"]
        if preset_name != current_preset_original_name and preset_name in existing_names:
            st.error(f"Un altro preset con nome '{preset_name}' esiste già.")
            return
    elif preset_name in existing_names:
        st.error(f"Un preset con nome '{preset_name}' esiste già.")
        return

    # Prepara i dati del preset da salvare
    preset_data_to_save = {
        "name": preset_name,
        "provider_name": form_data.get("provider_name"),
        "endpoint": form_data.get("endpoint_to_save", form_data.get("endpoint")), # Usa endpoint_to_save se presente
        "api_key": form_data.get("api_key"),
        "model": form_data.get("model"),
        "temperature": float(form_data.get("temperature", 0.0)),
        "max_tokens": int(form_data.get("max_tokens", 1000))
    }

    if current_id: # Modifica preset esistente
        idx = presets_df.index[presets_df["id"] == current_id].tolist()[0]
        for key, value in preset_data_to_save.items():
            presets_df.loc[idx, key] = value
        st.success(f"Preset '{preset_name}' aggiornato con successo!")
    else: # Crea nuovo preset
        new_id = str(uuid.uuid4())
        preset_data_to_save["id"] = new_id
        new_preset_df = pd.DataFrame([preset_data_to_save])
        presets_df = pd.concat([presets_df, new_preset_df], ignore_index=True)
        st.success(f"Preset '{preset_name}' creato con successo!")
    
    st.session_state.api_presets = presets_df
    save_api_presets(presets_df)
    cancel_preset_edit() # Chiudi il form

def delete_preset(preset_id):
    presets_df = st.session_state.api_presets
    preset_name_to_delete = presets_df[presets_df["id"] == preset_id].iloc[0]["name"]
    st.session_state.api_presets = presets_df[presets_df["id"] != preset_id]
    save_api_presets(st.session_state.api_presets)
    st.success(f"Preset '{preset_name_to_delete}' eliminato.")
    if st.session_state.current_preset_edit_id == preset_id:
        cancel_preset_edit() # Se stavamo modificando il preset eliminato, chiudi il form

# Sezione per visualizzare/modificare i preset
if st.session_state.editing_preset:
    add_section_title("Modifica/Crea Preset API", icon="✏️")
    form_data = st.session_state.preset_form_data
    
    with st.form(key="preset_form"):
        form_data["name"] = st.text_input("Nome del Preset", value=form_data.get("name", ""), help="Un nome univoco per questo preset.")
        
        selected_provider = st.selectbox(
            "Provider API", 
            options=list(ENDPOINT_OPTIONS.keys()), 
            index=list(ENDPOINT_OPTIONS.keys()).index(form_data.get("provider_name", list(ENDPOINT_OPTIONS.keys())[0])),
            key="form_provider_select"
        )
        form_data["provider_name"] = selected_provider
        
        # Gestione Endpoint
        if selected_provider == "Personalizzato":
            form_data["endpoint"] = st.text_input(
                "Endpoint API Personalizzato", 
                value=form_data.get("endpoint", ""), 
                placeholder="https://api.example.com/v1",
                key="form_custom_endpoint_input"
            )
            form_data["endpoint_to_save"] = form_data["endpoint"] # Salva l'URL personalizzato
        else:
            form_data["endpoint"] = ENDPOINT_OPTIONS[selected_provider]
            form_data["endpoint_to_save"] = form_data["endpoint"] # Salva l'URL del provider
            st.text_input("Endpoint API", value=form_data["endpoint"], disabled=True)

        form_data["api_key"] = st.text_input("Chiave API", value=form_data.get("api_key", ""), type="password", help="La tua chiave API per il provider selezionato.")
        
        # Selezione Modello
        # Aggiorna i modelli disponibili quando il provider, l'endpoint o la chiave cambiano
        # Questo richiede di mettere la logica di recupero modelli qui o in un callback.
        # Per semplicità, aggiorniamo quando cambia il provider.
        # Una soluzione più robusta potrebbe usare on_change sui campi rilevanti.
        
        # Per ora, assumiamo che l'utente inserisca il modello se personalizzato o se non trovato.
        # Una gestione più avanzata richiederebbe una chiamata API per elencare i modelli.
        
        current_models = get_available_models_for_endpoint(
            form_data["provider_name"], 
            form_data.get("endpoint_to_save", form_data.get("endpoint")),
            form_data["api_key"]
        )
        form_data["available_models"] = current_models
        
        # Se il modello attuale non è nella lista, aggiungilo temporaneamente
        current_model_in_form = form_data.get("model", DEFAULT_MODEL)
        if current_model_in_form not in current_models:
            current_models.insert(0, current_model_in_form) # Inseriscilo all'inizio per visibilità
        
        try:
            model_select_index = current_models.index(current_model_in_form)
        except ValueError:
            model_select_index = 0 # Default al primo se non trovato
            if current_models: form_data["model"] = current_models[0]

        form_data["model"] = st.selectbox(
            "Modello", 
            options=current_models, 
            index=model_select_index,
            help="Seleziona un modello o inserisci un nome modello personalizzato."
        ) 
        # Aggiungere un text_input per modello personalizzato se si vuole più flessibilità
        # if st.checkbox("Usa nome modello personalizzato", key="form_use_custom_model_name"):
        #     form_data["model"] = st.text_input("Nome Modello Personalizzato", value=form_data.get("model",""))

        form_data["temperature"] = st.slider("Temperatura", 0.0, 2.0, float(form_data.get("temperature", 0.0)), 0.1)
        form_data["max_tokens"] = st.number_input("Max Tokens", min_value=50, max_value=8000, value=int(form_data.get("max_tokens", 1000)), step=50)
        
        # Pulsante Test Connessione
        if st.form_submit_button("⚡ Testa Connessione API"):
            with st.spinner("Test in corso..."):
                success, message = test_api_connection(
                    api_key=form_data["api_key"],
                    endpoint=form_data.get("endpoint_to_save", form_data.get("endpoint")),
                    model=form_data["model"],
                    temperature=form_data["temperature"],
                    max_tokens=form_data["max_tokens"]
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # Pulsanti Salva e Annulla
        cols_form_buttons = st.columns(2)
        with cols_form_buttons[0]:
            if st.form_submit_button("💾 Salva Preset", type="primary", use_container_width=True):
                save_preset_from_form()
        with cols_form_buttons[1]:
            if st.form_submit_button("❌ Annulla", use_container_width=True):
                cancel_preset_edit()
else:
    add_section_title("Preset API Salvati", icon="🗂️")
    if st.button("➕ Crea Nuovo Preset", on_click=start_new_preset_edit, use_container_width=True):
        pass # Il callback gestisce il cambio di stato

    if st.session_state.api_presets.empty:
        st.info("Nessun preset API salvato. Clicca su 'Crea Nuovo Preset' per iniziare.")
    else:
        for index, preset in st.session_state.api_presets.iterrows():
            with st.container():
                st.markdown(f"#### {preset['name']}")
                cols_preset_details = st.columns([3, 1, 1])
                with cols_preset_details[0]:
                    st.caption(f"Provider: {preset.get('provider_name', 'N/A')} | Modello: {preset.get('model', 'N/A')}")
                    st.caption(f"Endpoint: {preset.get('endpoint', 'N/A')}")
                with cols_preset_details[1]:
                    if st.button("✏️ Modifica", key=f"edit_{preset['id']}", on_click=start_existing_preset_edit, args=(preset['id'],), use_container_width=True):
                        pass
                with cols_preset_details[2]:
                    if st.button("🗑️ Elimina", key=f"delete_{preset['id']}", on_click=delete_preset, args=(preset['id'],), type="secondary", use_container_width=True):
                        pass
                st.divider()

# Mostra messaggi di conferma dopo il ricaricamento della pagina (se impostati dai callback)
if "preset_applied_message" in st.session_state: # Questo non dovrebbe più essere usato qui
    st.success(st.session_state.preset_applied_message)
    del st.session_state.preset_applied_message
    
if "preset_saved_message" in st.session_state:
    st.success(st.session_state.preset_saved_message)
    del st.session_state.preset_saved_message
    
if "preset_deleted_message" in st.session_state:
    st.success(st.session_state.preset_deleted_message)
    del st.session_state.preset_deleted_message
