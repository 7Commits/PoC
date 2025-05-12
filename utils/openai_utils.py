import os
import json
import streamlit as st
from openai import OpenAI

DEFAULT_MODEL = "gpt-4o"
DEFAULT_ENDPOINT = "https://api.openai.com/v1"

# Modelli disponibili per diversi provider
OPENAI_MODELS = ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]
ANTHROPIC_MODELS = ["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
XAI_MODELS = ["grok-2-1212", "grok-vision-beta", "grok-beta"]

def get_openai_client():
    """Ottiene il client OpenAI con la chiave API dalla configurazione attiva."""
    from utils.api_utils import get_active_api_key
    
    # Prima prova a ottenere la chiave API attiva
    active_key = get_active_api_key()
    
    if active_key:
        # Usa la configurazione della chiave attiva
        api_key = active_key.get('api_key', '')
        endpoint = active_key.get('endpoint', DEFAULT_ENDPOINT)
        
        # Imposta la configurazione attiva nello stato della sessione per altri componenti
        st.session_state.api_key = api_key
        st.session_state.endpoint = endpoint
    else:
        # Ripiega sullo stato della sessione o sulle variabili d'ambiente
        api_key = st.session_state.get('api_key', os.environ.get('OPENAI_API_KEY', ''))
        endpoint = st.session_state.get('endpoint', DEFAULT_ENDPOINT)
    
    if not api_key:
        st.error("La chiave API non è configurata. Vai alla pagina Configurazione API per impostarla.")
        return None
    
    return OpenAI(base_url=endpoint, api_key=api_key)

def evaluate_answer(question, expected_answer, actual_answer, client=None, show_api_details=False):
    """
    Valuta una risposta utilizzando l'API LLM.
    
    Parametri:
    - question: La domanda che è stata posta
    - expected_answer: La risposta attesa
    - actual_answer: La risposta effettiva fornita
    - client: Client OpenAI, se None ne verrà creato uno nuovo
    - show_api_details: Se includere i dettagli della richiesta e della risposta API nel risultato
    
    Restituisce:
    - Dizionario con i risultati della valutazione
    """
    if client is None:
        client = get_openai_client()
        if client is None:
            return {
                "score": 0,
                "explanation": "Impossibile valutare la risposta: chiave API non configurata.",
                "similarity": 0,
                "correctness": 0,
                "completeness": 0
            }
    
    try:
        model = st.session_state.get('model', DEFAULT_MODEL)
        
        prompt = f"""
        Sei un valutatore esperto che valuta la qualità delle risposte alle domande.

        Domanda: {question}
        Risposta Attesa: {expected_answer}
        Risposta Effettiva: {actual_answer}

        Valuta la risposta effettiva rispetto alla risposta attesa in base a:
        1. Somiglianza (0-100): Quanto è semanticamente simile la risposta effettiva a quella attesa?
        2. Correttezza (0-100): Le informazioni nella risposta effettiva sono fattualmente corrette?
        3. Completezza (0-100): La risposta effettiva contiene tutti i punti chiave della risposta attesa?

        Calcola un punteggio complessivo (0-100) basato su queste metriche.

        Fornisci una breve spiegazione della tua valutazione (max 100 parole).

        Formatta la tua risposta come un oggetto JSON con questi campi:
        - score: il punteggio complessivo (numero tra 0 e 100)
        - explanation: breve spiegazione della valutazione
        - similarity: punteggio di somiglianza (numero tra 0 e 100)
        - correctness: punteggio di correttezza (numero tra 0 e 100)
        - completeness: punteggio di completezza (numero tra 0 e 100)
        """

        # Ottiene temperatura e max token dallo stato della sessione
        temperature = st.session_state.get('temperature', 0.0)
        max_tokens = st.session_state.get('max_tokens', 1000)
        
        # Prepara la richiesta API
        api_request = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Sei un valutatore esperto di risposte a domande."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }
        
        # Esegue la chiamata API
        response = client.chat.completions.create(**api_request)
        
        # Elabora la risposta
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        
        # Assicura che tutti i campi attesi siano presenti
        required_fields = ["score", "explanation", "similarity", "correctness", "completeness"]
        for field in required_fields:
            if field not in result:
                result[field] = 0 if field != "explanation" else "Campo mancante nella risposta di valutazione"
        
        # Aggiunge i dettagli della richiesta/risposta API se richiesto
        if show_api_details:
            # Include i dettagli della richiesta API (rimuove la chiave API effettiva)
            endpoint = st.session_state.get('endpoint', DEFAULT_ENDPOINT)
            result["api_details"] = {
                "endpoint": endpoint,
                "request": {
                    "model": model,
                    "messages": api_request["messages"],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"}
                },
                "response": {
                    "model": response.model,
                    "choices": [
                        {
                            "message": {
                                "role": choice.message.role,
                                "content": choice.message.content
                            },
                            "finish_reason": choice.finish_reason,
                            "index": choice.index
                        } for choice in response.choices
                    ],
                    "usage": {
                        "completion_tokens": response.usage.completion_tokens,
                        "prompt_tokens": response.usage.prompt_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            }
        
        return result
    
    except Exception as e:
        error_result = {
            "score": 0,
            "explanation": f"Errore: {str(e)}",
            "similarity": 0,
            "correctness": 0,
            "completeness": 0
        }
        
        if show_api_details:
            error_result["api_details"] = {
                "error": str(e),
                "endpoint": st.session_state.get('endpoint', DEFAULT_ENDPOINT),
                "model": st.session_state.get('model', DEFAULT_MODEL)
            }
            
        st.error(f"Errore durante la valutazione della risposta: {str(e)}")
        return error_result

def test_api_connection():
    """Testa la connessione all'API LLM."""
    client = get_openai_client()
    if client is None:
        return False, "Chiave API non configurata."
    
    try:
        model = st.session_state.get('model', DEFAULT_MODEL)
        
        # Ottiene la temperatura dallo stato della sessione
        temperature = st.session_state.get('temperature', 0.0)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Test connessione. Rispondi con 'Connessione riuscita.'"}
            ],
            temperature=temperature,
            max_tokens=10
        )
        
        content = response.choices[0].message.content or ""
        if "Connessione riuscita" in content: # Nota: "Connection successful" è stato tradotto qui ma il confronto rimane con la stringa originale per il test effettivo della risposta dell'API
            return True, "Connessione riuscita! La chiave API è valida."
        else:
            return True, "Connessione stabilita, ma con risposta imprevista."
    
    except Exception as e:
        return False, f"Connessione fallita: {str(e)}"

def get_available_models_for_endpoint(endpoint):
    """Restituisce i modelli disponibili per un determinato endpoint."""
    if "openai.com" in endpoint.lower():
        return OPENAI_MODELS
    elif "anthropic.com" in endpoint.lower() or "claude" in endpoint.lower():
        return ANTHROPIC_MODELS
    elif "x.ai" in endpoint.lower() or "xai" in endpoint.lower():
        return XAI_MODELS
    else:
        # Per endpoint personalizzati, restituisce tutti i modelli
        return OPENAI_MODELS + ANTHROPIC_MODELS + XAI_MODELS