import streamlit as st
import json
from utils import *
from domande import *

st.set_page_config(page_title="Artificial QI - PoC", layout="wide")
st.title("Artificial QI - Proof of Concept")
 
domande = carica_domande()

col1, col2 = st.columns([1, 2])

# Sezione "Gestione domande"
with col1:
    st.header("📁 Gestione domande")
    
    # Caricamento da file JSON (UC1.2)
    uploaded_file = st.file_uploader("📄 Carica file domande")
    
    if uploaded_file:
        try:
            domande_caricate = json.load(uploaded_file)
            st.success("✅ File caricato con successo")
            if st.button("📥 Importa nel database locale"):
                domande_correnti = carica_domande()
                domande_correnti.extend(domande_caricate)
                salva_domande(domande_correnti)
                st.success("Domande importate correttamente.")
        except Exception as e:
            st.error(f"❌ Errore nel file: {e}")

    # Inserimento manuale (UC1.1)
    st.markdown("---")
    st.subheader("Inserisci manualmente una domanda")

    with st.form("inserimento_domanda"):
        nuova_domanda = st.text_input("Domanda")
        nuova_risposta = st.text_area("Risposta attesa")
        categoria = st.text_input("Categoria (es. Python, Algoritmi, Capitali ecc.)")

        invia = st.form_submit_button("✅ Aggiungi")
        
        if invia and nuova_domanda.strip() and nuova_risposta.strip() and categoria.strip():
            aggiungi_domanda(
                nuova_domanda.strip(),
                nuova_risposta.strip(),
                categoria.strip()
            )
            st.success("Domanda aggiunta con successo.")
            st.rerun()

st.empty()

# Sezione "User input"
with col2:
    st.header("Esegui Test")
        
    # Cronologia chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "ai", "content": "Ciao! Come posso aiutarti?"}]
  
    # Mostra i messaggi della chat dalla cronologia
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Test da domande caricate
    if domande:
        scelta = st.selectbox("Seleziona una domanda", [d["domanda"] for d in domande])
        if st.button("Invia al modello simulato"):
            st.session_state.messages.append({"role": "user", "content": scelta})
            risposta = simula_risposta(scelta)
            st.session_state.messages.append({"role": "ai", "content": risposta})
            st.rerun()  # aggiornare l’interfaccia dopo il click

    # Chat libera
    if prompt := st.chat_input("Scrivi una domanda"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        risposta = simula_risposta(prompt)
        st.session_state.messages.append({"role": "ai", "content": risposta})
        st.rerun()
   
    st.markdown("---")
   
    st.subheader("📊 Risultato")
    
    st.write("Qui verrà mostrata la risposta generata e  la valutazione (da fare)")

