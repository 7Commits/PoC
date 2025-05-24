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
├── app.py # Main application script
├── requirements.txt # Lista dipendenze
├── pages/ # Page-specific scripts
│ ├── api_configurazione.py # Configurazione API
│ ├── esecuzione_test.py # Esecuzione test su domande
│ ├── gestione_domande.py # Gestione domande
│ ├── visualizza_risultati.py # Visualizzazione risultati test
│ └── gestione_set.py # Gestione set di domande
├── utils/ # Utility scripts
│ ├── api_utils.py # Gestione Api utils
│ ├── data_utils.py # Gestione dati utils
│ ├── openai_utils.py # Gestione utils openai
│ └── ui_utils.py # UI utils
├── data/ # Data files (CSV)
│ ├── questions.csv # Dati domande
│ ├── question_sets.csv # Dati set domande
│ ├──test_results.csv # Dati risultati test
│ └── ... #Altri file (Set domande json ecc)
