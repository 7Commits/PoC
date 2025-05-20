import os
import json
import streamlit as st
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError
import traceback

DEFAULT_MODEL = "gpt-4o" # Assicurati che sia un modello valido per i tuoi test
DEFAULT_ENDPOINT = "https://api.openai.com/v1" # Endpoint di default

# Modelli disponibili per diversi provider (esempio)
OPENAI_MODELS = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
ANTHROPIC_MODELS = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
# Aggiungi altri provider e modelli se necessario
# XAI_MODELS = ["grok-1"] 

def get_openai_client(api_key: str, base_url: str = None):
    """
    Crea e restituisce un client OpenAI configurato.
    Args:
        api_key: La chiave API.
        base_url: L'URL base dell'endpoint API (opzionale, default a OpenAI).
    Returns:
        Un'istanza del client OpenAI o None se la chiave API non è fornita.
    """
    if not api_key:
        # st.error("Tentativo di creare un client OpenAI senza una chiave API.") # Commentato per ridurre output UI
        print("DEBUG: Tentativo di creare client OpenAI senza chiave API.")
        return None
    try:
        # Se base_url è None, "custom", o vuoto, usa il default di OpenAI.
        # Altrimenti, usa il base_url fornito.
        effective_base_url = base_url if base_url and base_url.strip() and base_url != "custom" else DEFAULT_ENDPOINT
        return OpenAI(api_key=api_key, base_url=effective_base_url)
    except Exception as e:
        st.error(f"Errore durante la creazione del client OpenAI: {e}")
        return None

def evaluate_answer(question: str, expected_answer: str, actual_answer: str, 
                    client_config: dict, show_api_details: bool = False):
    """
    Valuta una risposta utilizzando un LLM specificato tramite client_config.
    Args:
        question: La domanda.
        expected_answer: La risposta attesa.
        actual_answer: La risposta effettiva da valutare.
        client_config: Dizionario contenente {api_key, endpoint, model, temperature, max_tokens}.
        show_api_details: Se True, include i dettagli della richiesta/risposta API.
    Returns:
        Un dizionario con il punteggio e la spiegazione, o un risultato di errore.
    """
    client = get_openai_client(api_key=client_config.get("api_key"), base_url=client_config.get("endpoint"))
    if not client:
        return {"score": 0, "explanation": "Errore: Client API per la valutazione non configurato.", "similarity": 0, "correctness": 0, "completeness": 0}

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
        - score: il punteggio complessivo (numero)
        - explanation: la tua spiegazione (stringa)
        - similarity: punteggio di somiglianza (numero)
        - correctness: punteggio di correttezza (numero)
        - completeness: punteggio di completezza (numero)
    """
    
    api_request_details = {
        "model": client_config.get("model", DEFAULT_MODEL),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": client_config.get("temperature", 0.0),
        "max_tokens": client_config.get("max_tokens", 250), # Aumentato leggermente per JSON più complesso
        "response_format": {"type": "json_object"}
    }
    
    api_details_for_log = {}
    if show_api_details:
        # Copia i dettagli della richiesta per loggarli, escludendo dati sensibili se necessario
        # (in questo caso, la chiave API è gestita dal client e non è direttamente nei dettagli della richiesta)
        api_details_for_log["request"] = api_request_details.copy()

    try:
        response = client.chat.completions.create(**api_request_details)
        content = response.choices[0].message.content or "{}"
        if show_api_details:
            api_details_for_log["response_content"] = content

        try:
            evaluation = json.loads(content)
            required_keys = ['score', 'explanation', 'similarity', 'correctness', 'completeness']
            if not all(key in evaluation for key in required_keys):
                st.warning(f"Risposta JSON dalla valutazione LLM incompleta: {content}. Verranno usati valori di default.")
                for key in required_keys:
                    if key not in evaluation:
                        evaluation[key] = 0 if key != 'explanation' else "Valutazione incompleta o formato JSON non corretto."
            
            evaluation['api_details'] = api_details_for_log
            return evaluation
        except json.JSONDecodeError:
            st.error(f"Errore: Impossibile decodificare la risposta JSON dalla valutazione LLM: {content}")
            return {
                "score": 0, "explanation": f"Errore di decodifica JSON: {content[:100]}...", 
                "similarity": 0, "correctness": 0, "completeness": 0,
                "api_details": api_details_for_log
            }

    except (APIConnectionError, RateLimitError, APIStatusError) as e:
        st.error(f"Errore API durante la valutazione: {type(e).__name__} - {e}")
        api_details_for_log["error"] = str(e)
        return {
            "score": 0, "explanation": f"Errore API: {type(e).__name__}", 
            "similarity": 0, "correctness": 0, "completeness": 0,
            "api_details": api_details_for_log
        }
    except Exception as e:
        st.error(f"Errore imprevisto durante la valutazione: {type(e).__name__} - {e}")
        # print(f"DEBUG: Unexpected Error in evaluate_answer: {traceback.format_exc()}")
        api_details_for_log["error"] = str(e)
        return {
            "score": 0, "explanation": f"Errore imprevisto: {type(e).__name__}",
            "similarity": 0, "correctness": 0, "completeness": 0,
            "api_details": api_details_for_log
        }

def generate_example_answer_with_llm(question: str, client_config: dict, show_api_details: bool = False):
    """
    Genera una risposta di esempio per una domanda utilizzando un LLM.
    Args:
        question: La domanda per cui generare una risposta.
        client_config: Dizionario contenente {api_key, endpoint, model, temperature, max_tokens}.
        show_api_details: Se True, include i dettagli della chiamata API nel risultato.
    Returns:
        Un dizionario con { "answer": "risposta generata" | None, "api_details": {...} | None }.
    """
    client = get_openai_client(api_key=client_config.get("api_key"), base_url=client_config.get("endpoint"))
    if not client:
        st.error("Client API per la generazione risposte non configurato.")
        return {"answer": None, "api_details": {"error": "Client API non configurato"} if show_api_details else None}

    # Controllo se la domanda è None o una stringa vuota
    if question is None or not isinstance(question, str) or question.strip() == "":
        st.error("La domanda fornita è vuota o non valida.")
        return {"answer": None, "api_details": {"error": "Domanda vuota o non valida"} if show_api_details else None}

    prompt = f"Rispondi alla seguente domanda in modo conciso e accurato: {question}"
    
    api_request_details = {
        "model": client_config.get("model", DEFAULT_MODEL),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": client_config.get("temperature", 0.7),
        "max_tokens": client_config.get("max_tokens", 500) 
    }
    
    api_details_for_log = {}
    if show_api_details:
        api_details_for_log["request"] = api_request_details.copy()

    try:
        response = client.chat.completions.create(**api_request_details)
        answer = response.choices[0].message.content.strip() if response.choices and response.choices[0].message.content else None
        if show_api_details:
            api_details_for_log["response_content"] = response.choices[0].message.content if response.choices else "Nessun contenuto"
        return {"answer": answer, "api_details": api_details_for_log if show_api_details else None}
    
    except (APIConnectionError, RateLimitError, APIStatusError) as e:
        st.error(f"Errore API durante la generazione della risposta di esempio: {type(e).__name__} - {e}")
        if show_api_details:
            api_details_for_log["error"] = str(e)
        return {"answer": None, "api_details": api_details_for_log if show_api_details else None}
    except Exception as e:
        st.error(f"Errore imprevisto durante la generazione della risposta: {type(e).__name__} - {e}")
        if show_api_details:
            api_details_for_log["error"] = str(e)
        return {"answer": None, "api_details": api_details_for_log if show_api_details else None}

def test_api_connection(api_key: str, endpoint: str, model: str, temperature: float, max_tokens: int):
    """Testa la connessione all'API LLM con i parametri forniti."""
    client = get_openai_client(api_key=api_key, base_url=endpoint)
    if not client:
        return False, "Client API non inizializzato. Controlla chiave API e endpoint."

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Test connessione. Rispondi solo con: 'Connessione riuscita.'"}],
            temperature=temperature,
            max_tokens=max_tokens # Assicurati che sia sufficiente per la risposta attesa
        )
        content = response.choices[0].message.content or ""
        if "Connessione riuscita." in content:
            return True, "Connessione API riuscita!"
        else:
            return False, f"Risposta inattesa dall'API (potrebbe indicare un problema con il modello o l'endpoint): {content[:200]}..."
    except APIConnectionError as e:
        return False, f"Errore di connessione API: {e}"
    except RateLimitError as e:
        return False, f"Errore di Rate Limit API: {e}"
    except APIStatusError as e:
        return False, f"Errore di stato API (es. modello '{model}' non valido per l'endpoint '{endpoint}', autenticazione fallita, quota superata): {e.status_code} - {e.message}"
    except Exception as e:
        # print(f"DEBUG: Unexpected Error in test_api_connection: {traceback.format_exc()}")
        return False, f"Errore imprevisto durante il test della connessione: {type(e).__name__} - {e}"

def get_available_models_for_endpoint(provider_name: str, endpoint_url: str = None, api_key: str = None):
    """
    Restituisce una lista di modelli disponibili basata sul provider o tenta di elencarli dall'endpoint.
    Args:
        provider_name: Nome del provider (es. "OpenAI", "Anthropic", "Personalizzato").
        endpoint_url: URL dell'endpoint (rilevante per "Personalizzato").
        api_key: Chiave API per autenticarsi (necessaria per elencare modelli da endpoint personalizzati).
    Returns:
        Una lista di stringhe di nomi di modelli.
    """
    if provider_name == "OpenAI":
        return OPENAI_MODELS
    elif provider_name == "Anthropic":
        return ANTHROPIC_MODELS
    # Aggiungi altri provider predefiniti qui
    # elif provider_name == "XAI":
    #     return XAI_MODELS
    elif provider_name == "Personalizzato":
        if not api_key or not endpoint_url or endpoint_url == "custom" or not endpoint_url.strip():
            # Se non ci sono informazioni sufficienti, restituisce una lista di fallback
            return ["(Endpoint personalizzato non specificato)", DEFAULT_MODEL, "gpt-4", "gpt-3.5-turbo"]
        
        client = get_openai_client(api_key=api_key, base_url=endpoint_url)
        if not client:
            return ["(Errore creazione client API)", DEFAULT_MODEL]
        try:
            models = client.models.list()
            # Filtra per modelli che non sono di embedding e, se possibile, che contengono "chat", "instruct" o "gpt"
            # Questo è un euristica e potrebbe necessitare di aggiustamenti
            filtered_models = sorted([
                model.id for model in models 
                if not any(term in model.id.lower() for term in ["embed", "embedding", "ada", "babbage", "curie", "davinci", "text-"]) 
                and (any(term in model.id.lower() for term in ["chat", "instruct", "gpt", "claude", "grok"]) or len(model.id.split('-')) > 2)
            ])
            if not filtered_models:
                 # Se il filtro aggressivo non trova nulla, restituisci tutti i modelli non di embedding
                 filtered_models = sorted([model.id for model in models if not any(term in model.id.lower() for term in ["embed", "embedding"])])
            return filtered_models if filtered_models else ["(Nessun modello compatibile trovato)", DEFAULT_MODEL]
        except Exception as e:
            # st.warning(f"Impossibile recuperare i modelli dall'endpoint personalizzato '{endpoint_url}': {e}")
            return ["(Errore recupero modelli)", DEFAULT_MODEL]
    return [DEFAULT_MODEL] # Default generale se il provider non è riconosciuto
