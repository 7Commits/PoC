import os
import json
import uuid
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

# Informazioni sul provider API
API_PROVIDERS = {
    "OpenAI": {
        "name": "OpenAI",
        "display_name": "OpenAI",
        "endpoint": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "icon": "🔵"
    },
    "Anthropic": {
        "name": "Anthropic",
        "display_name": "Anthropic Claude",
        "endpoint": "https://api.anthropic.com/v1",
        "env_key": "ANTHROPIC_API_KEY",
        "icon": "🟣"
    },
    "XAI": {
        "name": "XAI",
        "display_name": "X.AI (Grok)",
        "endpoint": "https://api.x.ai/v1",
        "env_key": "XAI_API_KEY",
        "icon": "⚪"
    },
    "Custom": {
        "name": "Custom",
        "display_name": "Provider personalizzato", # Già in italiano
        "endpoint": "custom",
        "env_key": "API_KEY",
        "icon": "🔌"
    }
}

def initialize_api_data():
    """Inizializza le directory e i file dei dati API se non esistono."""
    # Crea la directory dei dati se non esiste
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Crea api_keys.csv se non esiste
    api_keys_path = data_dir / "api_keys.csv"
    if not api_keys_path.exists():
        # Crea un DataFrame vuoto
        api_keys_df = pd.DataFrame({
            "id": [],
            "name": [],
            "provider": [],
            "endpoint": [],
            "api_key": [],
            "is_default": [],
            "created_at": [],
            "last_used": []
        })
        # Salva il DataFrame in CSV
        api_keys_df.to_csv(api_keys_path, index=False)
        
        # Inizializza lo stato della sessione
        st.session_state.api_keys = api_keys_df
    else:
        # Carica le chiavi API esistenti nello stato della sessione se non già caricate
        if 'api_keys' not in st.session_state:
            st.session_state.api_keys = pd.read_csv(api_keys_path)


def load_api_keys():
    """Carica le chiavi API dal file CSV."""
    # Crea la directory dei dati se non esiste
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Crea api_keys.csv se non esiste
    api_keys_path = data_dir / "api_keys.csv"
    if not api_keys_path.exists():
        initialize_api_data()
        
    # Restituisce un DataFrame vuoto se il file non esiste o è vuoto
    try:
        api_keys_df = pd.read_csv(api_keys_path)
        return api_keys_df
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        # Restituisce un DataFrame vuoto se il file è vuoto o corrotto
        return pd.DataFrame({
            "id": [],
            "name": [],
            "provider": [],
            "endpoint": [],
            "api_key": [],
            "is_default": [],
            "created_at": [],
            "last_used": []
        })


def save_api_keys(api_keys_df):
    """Salva le chiavi API nel file CSV."""
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    api_keys_path = data_dir / "api_keys.csv"
    api_keys_df.to_csv(api_keys_path, index=False)
    
    # Aggiorna lo stato della sessione
    st.session_state.api_keys = api_keys_df


def add_api_key(name, provider, endpoint, api_key, is_default=False):
    """Aggiunge una nuova configurazione di chiave API."""
    # Carica le chiavi API esistenti
    api_keys_df = load_api_keys()
    
    # Genera un ID univoco per la nuova chiave API
    key_id = str(uuid.uuid4())
    
    # Crea una nuova riga per la chiave API
    new_row = pd.DataFrame({
        "id": [key_id],
        "name": [name],
        "provider": [provider],
        "endpoint": [endpoint],
        "api_key": [api_key],
        "is_default": [is_default],
        "created_at": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "last_used": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    })
    
    # Se questa è la chiave predefinita, deseleziona qualsiasi predefinita esistente
    if is_default:
        api_keys_df.loc[:, "is_default"] = False
    
    # Accoda la nuova riga
    api_keys_df = pd.concat([api_keys_df, new_row], ignore_index=True)
    
    # Salva il DataFrame aggiornato
    save_api_keys(api_keys_df)
    
    return key_id


def update_api_key(key_id, name=None, provider=None, endpoint=None, api_key=None, is_default=None):
    """Aggiorna una configurazione di chiave API esistente."""
    # Carica le chiavi API esistenti
    api_keys_df = load_api_keys()
    
    # Trova la chiave API con l'ID specificato
    key_index = api_keys_df.index[api_keys_df["id"] == key_id].tolist()
    
    if not key_index:
        return False
    
    # Aggiorna i campi se forniti
    if name is not None:
        api_keys_df.loc[key_index[0], "name"] = name
    
    if provider is not None:
        api_keys_df.loc[key_index[0], "provider"] = provider
    
    if endpoint is not None:
        api_keys_df.loc[key_index[0], "endpoint"] = endpoint
    
    if api_key is not None:
        api_keys_df.loc[key_index[0], "api_key"] = api_key
    
    if is_default is not None:
        # Se questa viene impostata come predefinita, deseleziona qualsiasi predefinita esistente
        if is_default:
            api_keys_df.loc[:, "is_default"] = False
        
        api_keys_df.loc[key_index[0], "is_default"] = is_default
    
    # Aggiorna il timestamp dell'ultimo utilizzo
    api_keys_df.loc[key_index[0], "last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Salva il DataFrame aggiornato
    save_api_keys(api_keys_df)
    
    return True


def delete_api_key(key_id):
    """Elimina una configurazione di chiave API."""
    # Carica le chiavi API esistenti
    api_keys_df = load_api_keys()
    
    # Verifica se la chiave esiste
    if key_id not in api_keys_df["id"].values:
        return False
    
    # Verifica se la chiave è quella predefinita
    is_default = api_keys_df.loc[api_keys_df["id"] == key_id, "is_default"].values[0]
    
    # Rimuovi la chiave
    api_keys_df = api_keys_df[api_keys_df["id"] != key_id]
    
    # Se la chiave era quella predefinita, imposta una nuova predefinita se sono rimaste delle chiavi
    if is_default and not api_keys_df.empty:
        api_keys_df.loc[api_keys_df.index[0], "is_default"] = True
    
    # Salva il DataFrame aggiornato
    save_api_keys(api_keys_df)
    
    return True


def get_default_api_key():
    """Ottiene la configurazione della chiave API predefinita."""
    # Carica le chiavi API
    api_keys_df = load_api_keys()
    
    # Trova la chiave predefinita
    default_keys = api_keys_df[api_keys_df["is_default"]]
    
    if default_keys.empty:
        # Se non è impostata alcuna chiave predefinita, ma esistono delle chiavi, imposta la prima come predefinita
        if not api_keys_df.empty:
            api_keys_df.loc[api_keys_df.index[0], "is_default"] = True
            save_api_keys(api_keys_df)
            return api_keys_df.iloc[0].to_dict()
        return None
    
    # Restituisce la chiave predefinita come dizionario
    return default_keys.iloc[0].to_dict()


def get_active_api_key():
    """Ottiene la configurazione della chiave API attualmente attiva."""
    # Verifica se active_api_key_id è nello stato della sessione
    if 'active_api_key_id' in st.session_state:
        active_key_id = st.session_state.active_api_key_id
        
        # Carica le chiavi API
        api_keys_df = load_api_keys()
        
        # Trova la chiave attiva
        active_keys = api_keys_df[api_keys_df["id"] == active_key_id]
        
        if not active_keys.empty:
            # Aggiorna il timestamp dell'ultimo utilizzo
            api_keys_df.loc[api_keys_df["id"] == active_key_id, "last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_api_keys(api_keys_df)
            
            return active_keys.iloc[0].to_dict()
    
    # Se non è impostata alcuna chiave attiva o non esiste, restituisce la chiave predefinita
    return get_default_api_key()


def set_active_api_key(key_id):
    """Imposta la chiave API attiva tramite ID."""
    # Carica le chiavi API
    api_keys_df = load_api_keys()
    
    # Verifica se la chiave esiste
    if key_id not in api_keys_df["id"].values:
        return False
    
    # Imposta l'ID della chiave attiva nello stato della sessione
    st.session_state.active_api_key_id = key_id
    
    # Aggiorna il timestamp dell'ultimo utilizzo
    api_keys_df.loc[api_keys_df["id"] == key_id, "last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_api_keys(api_keys_df)
    
    return True


def get_api_provider_by_name(provider_name):
    """Ottiene le informazioni sul provider API per nome."""
    if provider_name in API_PROVIDERS:
        return API_PROVIDERS[provider_name]
    return API_PROVIDERS["Custom"]