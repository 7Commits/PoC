# 📌 PoC

Questa repository contiene il **Proof of Concept** per la fase di **Requirements and Technology Baseline** del **[capitolato 1](https://www.math.unipd.it/~tullio/IS-1/2024/Progetto/C1.pdf)**, proposto dall'azienda **[Zucchetti](https://www.zucchetti.it/it/cms/home.html)**.

---

## Artificial QI - LLM Test Evaluation Platform

Una piattaforma per creare, organizzare e testare domande su modelli LLM, con valutazione automatica e analisi dei risultati.

---

## Installazione

1. **Clona il progetto**
```bash
git clone https://github.com/7Commits/PoC.git
cd PoC
```

2. **Installa le dipendenze** 
```bash
pip install -r requirements.txt
```

3. **Avvia l'applicazione**
```bash
streamlit run app.py
```
L'app si aprirà su http://localhost:8501

### API Key OpenAI
Configura la tua chiave API OpenAI:

##### Linux / macOS
```bash
export OPENAI_API_KEY="la-tua-api-key"
```

##### Windows (CMD)
```bash
set OPENAI_API_KEY=la-tua-api-key
```

##### Windows (PowerShell)
```bash
$env:OPENAI_API_KEY="la-tua-api-key"
```

## **Struttura del progetto**
```md
PoC/
├── app.py                     # Script principale dell'app Streamlit
├── requirements.txt           # Lista delle dipendenze
├── README.md                  # Documentazione del progetto
├── .gitignore                 # File di configurazione Git per ignorare file
├── data/                      # File di dati (CSV e JSON)
│   ├── api_presets.csv        # Preset per configurazioni API
│   ├── basic_math.json        # Set di domande su matematica di base
│   ├── capital_cities.json    # Set di domande sulle capitali
│   ├── question_sets.csv      # Set di domande in formato CSV
│   ├── questions.csv          # Domande singole in formato CSV
│   └── test_results.csv       # Risultati dei test eseguiti
├── pages/                     # Script delle pagine Streamlit
│   ├── api_configurazione.py  # Configurazione delle API
│   ├── esecuzione_test.py     # Esecuzione dei test sulle domande
│   ├── gestione_domande.py    # Gestione del database delle domande
│   ├── gestione_set.py        # Gestione dei set di domande
│   └── visualizza_risultati.py# Visualizzazione dei risultati dei test
├── utils/                     # Script di utilità
│   ├── data_utils.py          # Utility per la gestione dei dati
│   ├── openai_utils.py        # Utility per l'interazione con OpenAI
│   ├── ui_utils.py            # Utility per l'interfaccia utente Streamlit
│   └── db_utils.py            # Utility per le operazioni di database

## Esecuzione con Docker

Per avviare la piattaforma tramite *Docker* è possibile utilizzare
`docker-compose`:

```bash
docker-compose up --build
```

Nel file `docker-compose.yml` il servizio MySQL utilizza
`MYSQL_ROOT_HOST: '%'` per consentire la connessione dal container
dell'applicazione. Assicurati che in `db.config` siano configurati
`host=db` e `port=3306`.

# PocReal
