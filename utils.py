import json
import streamlit as st


def carica_domande_da_json(file):
    # Carica un file JSON e restituisce una lista di domande.
    try:
        data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("Il file JSON deve contenere una lista di domande.")
        for d in data:
            if "domanda" not in d or "risposta_attesa" not in d:
                raise ValueError("Ogni voce deve contenere 'domanda' e 'risposta_attesa'.")
        return data
    except Exception as e:
        st.error(f"❌ Errore nel caricamento del file JSON: {e}")
        return []


def simula_risposta(domanda: str) -> str:
    # Genera una risposta simulata per testing
    return f"🧠 Risposta simulata: il sistema ha ricevuto la domanda:\n\n*{domanda}*\n\nE ha generato una risposta coerente (simulata)."

