# -*- coding: utf-8 -*-
"""
UC2: Gestione dei set di domande (Manage question sets)
PoC Python Example

Questo script dimostra le funzionalità di base per la gestione dei set di domande,
come descritto in UC2 e nei suoi sottocasi (UC2.1-UC2.4).
I dati vengono memorizzati in memoria per semplicità.
Si assume che esista un meccanismo per gestire le domande (come in UC1),
qui simuleremo un archivio di domande preesistente.
"""

# Simulazione di un archivio di domande esistente (da UC1)
# Ogni domanda ha un ID univoco e un testo.
archivio_domande_globale = {
    1: {"domanda": "Qual è la capitale d'Italia?", "risposta_attesa": "Roma"},
    2: {"domanda": "Chi ha scritto 'I Promessi Sposi'?", "risposta_attesa": "Alessandro Manzoni"},
    3: {"domanda": "Qual è il fiume più lungo d'Italia?", "risposta_attesa": "Po"},
    4: {"domanda": "Quanto fa 2+2?", "risposta_attesa": "4"},
    5: {"domanda": "Colore del cavallo bianco di Napoleone?", "risposta_attesa": "Bianco"}
}

# Dizionario in memoria per i set di domande
# Chiave: nome_set, Valore: lista di id_domanda
set_di_domande = {}

def mostra_domande_disponibili():
    print("\n--- Domande Disponibili nell'Archivio Globale ---")
    if not archivio_domande_globale:
        print("Nessuna domanda disponibile nell'archivio globale.")
        return
    for id_domanda, dettagli in archivio_domande_globale.items():
        print(f"ID: {id_domanda}, Domanda: 	'{dettagli['domanda']}'")
    print("--------------------------------------------------")

def crea_set_domande(nome_set, ids_domande_iniziali=None):
    """Crea un nuovo set di domande. (Parte di UC2)"""
    if nome_set in set_di_domande:
        print(f"Errore: Il set 	'{nome_set}	' esiste già.")
        return False
    
    domande_valide_nel_set = []
    if ids_domande_iniziali:
        for q_id in ids_domande_iniziali:
            if q_id in archivio_domande_globale:
                domande_valide_nel_set.append(q_id)
            else:
                print(f"Attenzione: Domanda ID {q_id} non trovata nell'archivio globale, non aggiunta al set.")
                
    set_di_domande[nome_set] = domande_valide_nel_set
    print(f"Set 	'{nome_set}	' creato con {len(domande_valide_nel_set)} domande.")
    return True

# UC2.1: Visualizzazione set
def visualizza_set(nome_set=None):
    """Visualizza un set specifico o tutti i set di domande."""
    if not set_di_domande:
        print("Nessun set di domande creato.")
        return

    if nome_set:
        if nome_set in set_di_domande:
            print(f"\n--- Dettaglio Set: {nome_set} ---")
            ids_nel_set = set_di_domande[nome_set]
            if not ids_nel_set:
                print("Questo set è vuoto.")
            else:
                for q_id in ids_nel_set:
                    domanda_testo = archivio_domande_globale.get(q_id, {}).get("domanda", "Domanda non trovata")
                    print(f"  ID: {q_id}, Domanda: 	'{domanda_testo}	'")
            print("--------------------------------")
        else:
            print(f"Set 	'{nome_set}	' non trovato.")
    else:
        print("\n--- Tutti i Set di Domande ---")
        for nome, ids in set_di_domande.items():
            print(f"Set: 	'{nome}	' (Contiene {len(ids)} domande)")
        print("------------------------------")

# UC2.2: Modifica set (aggiungendo o rimuovendo domande)
def modifica_composizione_set(nome_set, ids_da_aggiungere=None, ids_da_rimuovere=None):
    """Modifica la composizione di un set esistente. (Anche UC8)"""
    if nome_set not in set_di_domande:
        print(f"Errore: Set 	'{nome_set}	' non trovato.")
        return False

    modificato = False
    # Aggiungi domande
    if ids_da_aggiungere:
        for q_id in ids_da_aggiungere:
            if q_id in archivio_domande_globale:
                if q_id not in set_di_domande[nome_set]:
                    set_di_domande[nome_set].append(q_id)
                    print(f"Domanda ID {q_id} aggiunta al set 	'{nome_set}	'.")
                    modificato = True
                else:
                    print(f"Domanda ID {q_id} è già nel set 	'{nome_set}	'.")
            else:
                print(f"Attenzione: Domanda ID {q_id} non trovata nell'archivio globale, non aggiunta.")
    
    # Rimuovi domande
    if ids_da_rimuovere:
        for q_id in ids_da_rimuovere:
            if q_id in set_di_domande[nome_set]:
                set_di_domande[nome_set].remove(q_id)
                print(f"Domanda ID {q_id} rimossa dal set 	'{nome_set}	'.")
                modificato = True
            else:
                print(f"Domanda ID {q_id} non trovata nel set 	'{nome_set}	' per la rimozione.")
    
    if modificato:
        print(f"Set 	'{nome_set}	' aggiornato.")
    else:
        print(f"Nessuna modifica apportata al set 	'{nome_set}	'.")
    return modificato

# UC2.3: Eliminazione set
def eliminazione_set(nome_set):
    """Elimina un set di domande. Le domande stesse non vengono cancellate. (Anche UC7)"""
    if nome_set in set_di_domande:
        del set_di_domande[nome_set]
        print(f"Set 	'{nome_set}	' eliminato.")
        # UC7.1 (Annullamento eliminazione set) sarebbe gestito a livello di UI con una conferma prima di chiamare questa funzione.
        return True
    else:
        print(f"Errore: Set 	'{nome_set}	' non trovato per l'eliminazione.")
        return False

# UC2.4: Rinomina set di domande
def rinomina_set(nome_attuale, nuovo_nome):
    """Modifica il nome di un set di domande esistente."""
    if nome_attuale not in set_di_domande:
        print(f"Errore: Set 	'{nome_attuale}	' non trovato.")
        return False
    if nuovo_nome in set_di_domande:
        print(f"Errore: Un set con nome 	'{nuovo_nome}	' esiste già.")
        return False
    
    set_di_domande[nuovo_nome] = set_di_domande.pop(nome_attuale)
    print(f"Set 	'{nome_attuale}	' rinominato in 	'{nuovo_nome}	'.")
    return True

if __name__ == "__main__":
    print("### Inizio Demo UC2: Gestione dei set di domande ###")
    mostra_domande_disponibili()

    # UC2: Creazione set
    print("\nCreazione Set 'Quiz Italia':")
    crea_set_domande("Quiz Italia", [1, 3, 7]) # ID 7 non esiste
    visualizza_set("Quiz Italia")

    print("\nCreazione Set 'Matematica Base':")
    crea_set_domande("Matematica Base", [4])
    visualizza_set("Matematica Base")
    
    print("\nCreazione Set 'Vuoto':")
    crea_set_domande("Set Vuoto")
    visualizza_set("Set Vuoto")

    # UC2.1: Visualizzazione (già usata sopra, ora visualizza tutti)
    print("\nVisualizzazione di tutti i set:")
    visualizza_set()

    # UC2.2 / UC8: Modifica composizione set
    print("\nModifica Set 'Quiz Italia': aggiungo ID 2, rimuovo ID 3, provo ad aggiungere ID 1 (già presente) e ID 8 (non esistente)")
    modifica_composizione_set("Quiz Italia", ids_da_aggiungere=[2, 1, 8], ids_da_rimuovere=[3])
    visualizza_set("Quiz Italia")
    
    print("\nModifica Set 'Set Vuoto': aggiungo ID 5")
    modifica_composizione_set("Set Vuoto", ids_da_aggiungere=[5])
    visualizza_set("Set Vuoto")

    # UC2.4: Rinomina set
    print("\nRinomina Set 'Quiz Italia' in 'Domande Italiane':")
    rinomina_set("Quiz Italia", "Domande Italiane")
    visualizza_set("Domande Italiane")
    visualizza_set("Quiz Italia") # Dovrebbe non essere trovato

    # UC2.3 / UC7: Eliminazione set
    print("\nEliminazione Set 'Matematica Base':")
    eliminazione_set("Matematica Base")
    visualizza_set()
    
    print("\nEliminazione Set 'Non Esistente':")
    eliminazione_set("Non Esistente")

    print("\n### Fine Demo UC2 ###")

