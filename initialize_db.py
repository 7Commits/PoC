import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from utils.db_utils import init_db
except ModuleNotFoundError as exc:
    print("Modulo mancante: sqlalchemy. Installa le dipendenze con 'pip install -r requirements.txt'")
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

