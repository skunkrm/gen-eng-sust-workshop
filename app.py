"""Interfaccia web del consulente ESG con upload di documenti. Avvio: uv run streamlit run app.py"""

import streamlit as st

from config import MODEL, MODELS
from engine import reply
from extractor import build_knowledge_base

st.set_page_config(page_title="ESG Copilot", page_icon="🌱")
st.title("🌱 ESG Copilot")
st.caption("Il tuo consulente CSRD ed ESRS, costruito sul Generative Engine")

for chiave, valore in (("messages", []), ("tokens", 0), ("kb_text", ""), ("kb_names", [])):
    if chiave not in st.session_state:
        st.session_state[chiave] = valore

with st.sidebar:
    st.subheader("Modello")
    modello = st.selectbox("Modello", list(MODELS), index=list(MODELS).index(MODEL),
                           format_func=lambda m: f"{m} — {MODELS[m]}", label_visibility="collapsed")

    st.subheader("Documenti")
    files = st.file_uploader("Carica PDF, Word o Excel", type=["pdf", "docx", "xlsx"],
                             accept_multiple_files=True)
    nomi = sorted(f.name for f in files or [])
    if nomi != st.session_state.kb_names:  # rileggiamo i file solo se sono cambiati
        st.session_state.kb_text = build_knowledge_base(files) if files else ""
        st.session_state.kb_names = nomi
    if nomi:
        st.success(f"{len(nomi)} documento/i in memoria")

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
        with st.spinner(f"Il consulente sta pensando ({modello})…"):
            try:
                testo, token = reply(domanda, st.session_state.messages, st.session_state.kb_text, modello)
            except Exception as errore:
                testo, token = f"⚠️ Errore nella chiamata al modello: {errore}", 0
        st.markdown(testo)
    st.session_state.messages += [
        {"role": "user", "content": domanda},
        {"role": "assistant", "content": testo},
    ]
    st.session_state.tokens += token
    st.rerun()
