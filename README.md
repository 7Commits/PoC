# 📌 PoC

Questa repository contiene il **Proof of Concept** per la fase di **Requirements and Technology Baseline** del **[capitolato 1](https://www.math.unipd.it/~tullio/IS-1/2024/Progetto/C1.pdf)**, proposto dall'azienda **[Zucchetti](https://www.zucchetti.it/it/cms/home.html)**.

```
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
```
