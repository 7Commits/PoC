import json
import os

# implementazione UC1.1-1.5 (1.2 già implementato)

PERCORSO_DOMANDE = "dati/domande.json"

def carica_domande():
    if not os.path.exists(PERCORSO_DOMANDE):
        return []
    with open(PERCORSO_DOMANDE, "r", encoding="utf-8") as f:
        return json.load(f)

def salva_domande(domande):
    with open(PERCORSO_DOMANDE, "w", encoding="utf-8") as f:
        json.dump(domande, f, indent=2, ensure_ascii=False)

def aggiungi_domanda(domanda, risposta_attesa, categoria):
    domande = carica_domande()
    nuovo_id = max((d.get("id", 0) for d in domande), default=0) + 1
    
    domande.append({
        "id": nuovo_id,
        "domanda": domanda, 
        "risposta_attesa": risposta_attesa,
        "categoria": categoria
    })
    salva_domande(domande)

def modifica_domanda(indice, nuova_domanda=None, nuova_risposta=None):
    domande = carica_domande()
    if nuova_domanda:
        domande[indice]["domanda"] = nuova_domanda
    if nuova_risposta:
        domande[indice]["risposta_attesa"] = nuova_risposta
    salva_domande(domande)

def elimina_domanda(indice):
    domande = carica_domande()
    domande.pop(indice)
    salva_domande(domande)
