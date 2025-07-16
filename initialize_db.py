import os
import sys

# Aggiungi la directory corrente al percorso
sys.path.append(os.path.dirname(__file__))

try:
    from utils.db_utils import init_db
except ModuleNotFoundError as exc:
    print("Modulo mancante. Installa le dipendenze con 'pip install -r requirements.txt'")
    print(f"Errore specifico: {exc}")
    raise exc

if __name__ == '__main__':
    print("Inizializzazione del database in corso...")
    try:
        init_db()
        print("Database inizializzato con successo!")
    except Exception as e:
        print(f"Errore durante l'inizializzazione del database: {e}")
        import traceback
        print("Traceback dettagliato:")
        print(traceback.format_exc())

