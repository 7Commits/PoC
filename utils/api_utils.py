import os
import json
import uuid
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime



API_PRESETS_FILE = Path("./data/api_presets.csv")

def load_api_presets():
    """Carica i preset API dal file CSV."""
    if API_PRESETS_FILE.exists():
        try:
            df = pd.read_csv(API_PRESETS_FILE)
            # Assicura i tipi di dati corretti, specialmente per i numerici
            df['id'] = df['id'].astype(str)
            df['name'] = df['name'].astype(str).fillna("")
            df['provider_name'] = df['provider_name'].astype(str).fillna("")
            df['endpoint'] = df['endpoint'].astype(str).fillna("")
            df['api_key'] = df['api_key'].astype(str).fillna("")
            df['model'] = df['model'].astype(str).fillna("")
            df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce').fillna(0.0)
            df['max_tokens'] = pd.to_numeric(df['max_tokens'], errors='coerce').fillna(1000).astype(int)
            return df
        except pd.errors.EmptyDataError:
            pass # Restituisce DataFrame vuoto sotto
        except Exception as e:
            st.error(f"Errore durante la lettura di {API_PRESETS_FILE}: {e}")
    
    return pd.DataFrame({
        'id': pd.Series(dtype='str'),
        'name': pd.Series(dtype='str'),
        'provider_name': pd.Series(dtype='str'),
        'endpoint': pd.Series(dtype='str'),
        'api_key': pd.Series(dtype='str'),
        'model': pd.Series(dtype='str'),
        'temperature': pd.Series(dtype='float'),
        'max_tokens': pd.Series(dtype='int')
    })


def save_api_presets(presets_df):
    """Salva i preset API nel file CSV."""
    # Assicura che le colonne siano nell'ordine desiderato e abbiano il tipo corretto
    expected_columns = ['id', 'name', 'provider_name', 'endpoint', 'api_key', 'model', 'temperature', 'max_tokens']
    df_to_save = pd.DataFrame(columns=expected_columns)

    for col in expected_columns:
        if col in presets_df.columns:
            if presets_df[col].dtype == 'float64': # Gestione specifica per float
                 df_to_save[col] = presets_df[col].astype(float)
            elif presets_df[col].dtype == 'int64' or presets_df[col].dtype == 'int32': # Gestione specifica per int
                 df_to_save[col] = presets_df[col].astype(int)
            else:
                 df_to_save[col] = presets_df[col].astype(str)
        else:
            # Assegna un tipo di default se la colonna manca (non dovrebbe accadere)
            if col in ['temperature']: 
                df_to_save[col] = pd.Series(dtype='float')
            elif col in ['max_tokens']: 
                df_to_save[col] = pd.Series(dtype='int')
            else:
                df_to_save[col] = pd.Series(dtype='str')

    df_to_save.to_csv(API_PRESETS_FILE, index=False)
    if 'api_presets' in st.session_state: # Aggiorna lo stato della sessione se esiste
        st.session_state.api_presets = df_to_save.copy() # Salva una copia per evitare modifiche per riferimento

