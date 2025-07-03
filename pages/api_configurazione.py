import streamlit as st
import os
import sys
import uuid
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.openai_utils import (
    test_api_connection, DEFAULT_MODEL, DEFAULT_ENDPOINT
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


# Funzioni di callback per i pulsanti del form
def start_new_preset_edit():
    st.session_state.editing_preset = True
    st.session_state.current_preset_edit_id = None # Indica nuovo preset
    st.session_state.preset_form_data = {
        "name": "",
        "endpoint": DEFAULT_ENDPOINT,
        "api_key": "",
        "model": DEFAULT_MODEL,
        "temperature": 0.0,
        "max_tokens": 1000
    }

def start_existing_preset_edit(preset_id):
    preset_to_edit = st.session_state.api_presets[st.session_state.api_presets["id"] == preset_id].iloc[0].to_dict()
    st.session_state.editing_preset = True
    st.session_state.current_preset_edit_id = preset_id
    st.session_state.preset_form_data = preset_to_edit.copy()
    # Assicura che i campi numerici siano del tipo corretto per gli slider/number_input
    st.session_state.preset_form_data["temperature"] = float(st.session_state.preset_form_data.get("temperature", 0.0))
    st.session_state.preset_form_data["max_tokens"] = int(st.session_state.preset_form_data.get("max_tokens", 1000))
    if "endpoint" not in st.session_state.preset_form_data:
        st.session_state.preset_form_data["endpoint"] = DEFAULT_ENDPOINT

def cancel_preset_edit():
    st.session_state.editing_preset = False
    st.session_state.current_preset_edit_id = None
    st.session_state.preset_form_data = {}

def save_preset_from_form():
    # Ottiene direttamente il valore dal campo input tramite session_state
    form_data = st.session_state.preset_form_data.copy()
    preset_name = st.session_state.get("preset_name", "").strip()
    
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
        "name": preset_name,  # Usa il valore validato
        "endpoint": form_data.get("endpoint"),
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
        # Usa un key specifico per il campo nome e aggiorna il form_data
        form_data["name"] = st.text_input(
            "Nome del Preset", 
            value=form_data.get("name", ""),
            key="preset_name",  # Key esplicita per il campo nome
            help="Un nome univoco per questo preset."
        )
        
        # Campo chiave API con key esplicita
        form_data["api_key"] = st.text_input(
            "Chiave API", 
            value=form_data.get("api_key", ""), 
            type="password", 
            key="preset_api_key",  # Key esplicita per la chiave API
            help="La tua chiave API per il provider selezionato."
        )
        
        # Campo endpoint con key esplicita
        form_data["endpoint"] = st.text_input(
            "Provider Endpoint", 
            value=form_data.get("endpoint", DEFAULT_ENDPOINT),
            placeholder="https://api.openai.com/v1",
            key="preset_endpoint",  # Key esplicita per l'endpoint
            help="Inserisci l'endpoint del provider API (es: https://api.openai.com/v1)"
        )
        
        # Modello sempre personalizzabile
        form_data["model"] = st.text_input(
            "Modello", 
            value=form_data.get("model", DEFAULT_MODEL),
            placeholder="gpt-4o",
            key="preset_model",  # Key esplicita per il modello
            help="Inserisci il nome del modello (es: gpt-4o, claude-3-sonnet, ecc.)"
        )

        form_data["temperature"] = st.slider("Temperatura", 0.0, 2.0, float(form_data.get("temperature", 0.0)), 0.1)
        form_data["max_tokens"] = st.number_input("Max Tokens", min_value=50, max_value=8000, value=int(form_data.get("max_tokens", 1000)), step=50)
        
        # Campo Test Connessione e pulsanti di salvataggio/annullamento
        # Pulsante Test Connessione
        if st.form_submit_button("⚡ Testa Connessione API"):
            # Usa direttamente i valori dal session_state per il test
            api_key_to_test = st.session_state.get("preset_api_key", "")
            endpoint_to_test = st.session_state.get("preset_endpoint", DEFAULT_ENDPOINT)
            model_to_test = st.session_state.get("preset_model", DEFAULT_MODEL)
            
            with st.spinner("Test in corso..."):
                success, message = test_api_connection(
                    api_key=api_key_to_test,
                    endpoint=endpoint_to_test,
                    model=model_to_test,
                    temperature=form_data.get("temperature", 0.0),
                    max_tokens=form_data.get("max_tokens", 1000)
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # Pulsanti Salva e Annulla
        cols_form_buttons = st.columns(2)
        with cols_form_buttons[0]:
            if st.form_submit_button("💾 Salva Preset", on_click=save_preset_from_form, type="primary", use_container_width=True):
                pass  # Il callback gestisce il salvataggio
        with cols_form_buttons[1]:
            if st.form_submit_button("❌ Annulla", on_click=cancel_preset_edit, use_container_width=True):
                pass  # Il callback gestisce il cambio di stato
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
                    st.caption(f"Modello: {preset.get('model', 'N/A')}")
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

