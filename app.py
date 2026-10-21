"""Interfaccia web del consulente ESG. Avvio: uv run streamlit run app.py"""

import streamlit as st

from config import MODEL
from engine import reply

st.set_page_config(page_title="ESG Copilot", page_icon="🌱")
st.title("🌱 ESG Copilot")
st.caption("Il tuo consulente CSRD ed ESRS, costruito sul Generative Engine")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "tokens" not in st.session_state:
    st.session_state.tokens = 0

with st.sidebar:
    st.subheader("Impostazioni")
    st.write(f"**Modello:** `{MODEL}`")
    st.metric("Token usati in questa sessione", f"{st.session_state.tokens:,}".replace(",", "."))
    if st.button("Nuova conversazione"):
        st.session_state.messages = []
        st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if domanda := st.chat_input("Chiedi qualcosa al consulente ESG…"):
    with st.chat_message("user"):
        st.markdown(domanda)
    with st.chat_message("assistant"):
        with st.spinner("Il consulente sta pensando…"):
            try:
                testo, token = reply(domanda, st.session_state.messages)
            except Exception as errore:  # mostriamo l'errore invece di bloccare l'app
                testo, token = f"⚠️ Errore nella chiamata al modello: {errore}", 0
        st.markdown(testo)
    st.session_state.messages += [
        {"role": "user", "content": domanda},
        {"role": "assistant", "content": testo},
    ]
    st.session_state.tokens += token
    st.rerun()
