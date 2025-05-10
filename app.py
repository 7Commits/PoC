import streamlit as st
from utils import carica_domande_da_json, simula_risposta

st.set_page_config(page_title="Artificial QI - PoC", layout="wide")
st.title("Artificial QI - Proof of Concept")
 
col1, col2 = st.columns([1, 2])

# Sezione "Gestione domande"
with col1:
    st.header("Gestione domande")
    
    uploaded_file = st.file_uploader("📄 Carica file domande")
    
    domande = []
    if uploaded_file:
        domande = carica_domande_da_json(uploaded_file)
        st.success("✅ File caricato con successo")
    
    st.markdown("---")
    
    if domande:
        with st.expander("📋 Visualizza domande caricate"):
            for i, d in enumerate(domande, 1):
                st.markdown(f"**{i}.** {d['domanda']}")
    else:
        st.info("Nessuna domanda caricata")


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
   
    st.subheader("📊 Risultato")
    
    st.write("Qui verrà mostrata la risposta generata e  la valutazione (da fare)")

