# -*- coding: utf-8 -*-
"""
UC1: Gestione domande e risposte attese (Manage questions and expected answers)
PoC Python Example

Questo script dimostra le funzionalità di base per la gestione di domande e risposte attese,
come descritto in UC1 e nei suoi sottocasi (UC1.1-UC1.5).
I dati vengono memorizzati in una lista in memoria per semplicità.
Supporta l'importazione di domande solo da file JSON.
"""
import json # Assicurarsi che json sia importato

# Lista in memoria per archiviare domande e risposte
# Ogni elemento è un dizionario con "id", "domanda", "risposta_attesa"
archivio_domande = []
next_id = 1

def mostra_archivio():
    """Visualizza tutte le domande e risposte nell'archivio."""
    if not archivio_domande:
        print("L'archivio è vuoto.")
        return
    print("\n--- Archivio Domande ---")
    for item in archivio_domande:
        print(f"ID: {item['id']}, Domanda: '{item['domanda']}', Risposta Attesa: '{item['risposta_attesa']}'")
    print("------------------------")

# UC1.1: Aggiunta manuale domanda
def aggiunta_manuale_domanda(domanda_testo, risposta_attesa_testo):
    """Aggiunge manualmente una nuova domanda e la sua risposta attesa."""
    global next_id
    nuova_domanda = {
        "id": next_id,
        "domanda": domanda_testo,
        "risposta_attesa": risposta_attesa_testo
    }
    archivio_domande.append(nuova_domanda)
    next_id += 1
    print(f"Domanda ID {nuova_domanda['id']} aggiunta manualmente.")
    return nuova_domanda['id']

# UC1.2: Aggiunta da file JSON (modificato per supportare solo JSON)
def aggiunta_da_file_json(file_content_str):
    """
    Simula l'aggiunta di domande da un file JSON.
    Per il PoC, 'file_content_str' è una stringa che rappresenta il contenuto del file JSON.
    Formato JSON atteso: lista di oggetti [{"domanda": "...", "risposta_attesa": "..."}, ...]
    """
    added_ids = []
    try:
        items = json.loads(file_content_str)
        if not isinstance(items, list):
            print("Errore: Il contenuto JSON deve essere una lista di oggetti.")
            return added_ids
        for item in items:
            if isinstance(item, dict) and "domanda" in item and "risposta_attesa" in item:
                added_id = aggiunta_manuale_domanda(item["domanda"], item["risposta_attesa"])
                added_ids.append(added_id)
            else:
                print(f"Elemento JSON ignorato (formato non corretto o campi mancanti): {item}")
    except json.JSONDecodeError:
        print("Errore nella decodifica del JSON.")
    
    if added_ids:
        print(f"Aggiunte {len(added_ids)} domande da file JSON.")
    return added_ids

# Funzione helper per trovare una domanda per ID
def _trova_domanda_per_id(id_domanda):
    for item in archivio_domande:
        if item["id"] == id_domanda:
            return item
    return None

# UC1.3: Modifica domanda
def modifica_domanda(id_domanda, nuovo_testo_domanda):
    """Modifica il testo di una domanda esistente."""
    item = _trova_domanda_per_id(id_domanda)
    if item:
        item["domanda"] = nuovo_testo_domanda
        print(f"Domanda ID {id_domanda} modificata.")
        return True
    else:
        print(f"Domanda ID {id_domanda} non trovata.")
        return False

# UC1.4: Modifica risposta attesa
def modifica_risposta_attesa(id_domanda, nuova_risposta_attesa):
    """Modifica la risposta attesa di una domanda esistente."""
    item = _trova_domanda_per_id(id_domanda)
    if item:
        item["risposta_attesa"] = nuova_risposta_attesa
        print(f"Risposta attesa per la domanda ID {id_domanda} modificata.")
        return True
    else:
        print(f"Domanda ID {id_domanda} non trovata.")
        return False

# UC1.5: Eliminazione domanda
def eliminazione_domanda(id_domanda):
    """Elimina una domanda dall'archivio."""
    global archivio_domande
    item = _trova_domanda_per_id(id_domanda)
    if item:
        archivio_domande = [d for d in archivio_domande if d["id"] != id_domanda]
        print(f"Domanda ID {id_domanda} eliminata.")
        return True
    else:
        print(f"Domanda ID {id_domanda} non trovata.")
        return False

if __name__ == "__main__":
    print("### Inizio Demo UC1: Gestione domande e risposte attese (Solo JSON) ###")

    # UC1.1: Aggiunta manuale
    id1 = aggiunta_manuale_domanda("Qual è la capitale d'Italia?", "Roma")
    id2 = aggiunta_manuale_domanda("Chi ha scritto 'I Promessi Sposi'?", "Alessandro Manzoni")
    mostra_archivio()
    
    # UC1.2: Aggiunta da file strutturato (solo JSON)
    contenuto_json = '[{"domanda": "Colore del cavallo bianco di Napoleone?", "risposta_attesa": "Bianco"}, {"domanda": "Anno scoperta America?", "risposta_attesa": "1492"}]'
    print("\nSimulazione aggiunta da JSON:")
    aggiunta_da_file_json(contenuto_json)
    mostra_archivio()

    # Esempio di JSON malformato
    contenuto_json_errato = '[{"domanda": "Domanda valida?", "risposta_attesa": "Sì"}, {"manca_domanda": "Valore"}]'
    print("\nSimulazione aggiunta da JSON (con errore di formato elemento):")
    aggiunta_da_file_json(contenuto_json_errato)
    mostra_archivio()

    contenuto_json_non_lista = '{"domanda": "Non una lista?", "risposta_attesa": "No"}'
    print("\nSimulazione aggiunta da JSON (non una lista):")
    aggiunta_da_file_json(contenuto_json_non_lista)
    mostra_archivio()

    # UC1.3: Modifica domanda
    print(f"\nModifica domanda ID {id1}:")
    modifica_domanda(id1, "Qual è la capitale attuale d'Italia?")
    mostra_archivio()

    # UC1.4: Modifica risposta attesa
    print(f"\nModifica risposta attesa per ID {id2}:")
    modifica_risposta_attesa(id2, "A. Manzoni")
    mostra_archivio()

    # UC1.5: Eliminazione domanda
    print(f"\nEliminazione domanda ID {id1}:")
    eliminazione_domanda(id1)
    mostra_archivio()
    
    print(f"\nEliminazione domanda ID 99 (non esistente):")
    eliminazione_domanda(99)
    mostra_archivio()

    print("\n### Fine Demo UC1 (Solo JSON) ###")

