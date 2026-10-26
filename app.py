"""Sustainability Copilot, step 2: il consulente legge i documenti caricati. Avvio: uv run streamlit run app.py"""

import time

import streamlit as st

from config import MODEL, MODELS, PREZZI
from engine import reply
from extractor import build_knowledge_base
from ui import AVATAR_AGENTE, AVATAR_UTENTE, NOME, misure, stile, testata

FRASI = ["legge bilanci, Word ed Excel.", "fa la gap analysis sugli ESRS.",
         "cita il documento da cui prende ogni dato.", "controlla i dati prima di commentarli."]

st.set_page_config(page_title=NOME, page_icon="🌱", layout="wide", initial_sidebar_state="expanded")
stile()
intestazione = st.empty()  # la riempiamo dopo la sidebar, quando sappiamo modello e documenti

# tokens (di cui tok_in di input e tok_out di output), costo e secondi: totali della sessione;
# ultima: misure dell'ultima richiesta; misure: indice del messaggio -> misure di quella risposta
DEFAULT = {"messages": [], "tokens": 0, "tok_in": 0, "tok_out": 0, "costo": 0.0, "secondi": 0.0,
           "ultima": {}, "misure": {}, "kb_text": "", "kb_names": []}
for chiave, valore in DEFAULT.items():
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

    st.subheader("Sessione")
    if st.button("Nuova conversazione"):  # token, costo e tempo restano: sono della sessione
        st.session_state.messages, st.session_state.misure = [], {}
        st.rerun()


def aggiorna_testata(inizio=None):
    """inizio: istante di partenza della richiesta in corso (None se il consulente è fermo)."""
    s = st.session_state
    testata(intestazione, modello, len(s.kb_names), s.tokens, s.costo, s.secondi, s.ultima,
            inizio=inizio, tok_in=s.tok_in, tok_out=s.tok_out, frasi=FRASI)


aggiorna_testata()


def avatar(ruolo):
    return AVATAR_UTENTE if ruolo == "user" else AVATAR_AGENTE


domanda = st.chat_input("Chiedi qualcosa al consulente di sostenibilità…")

if not st.session_state.messages and not domanda:
    st.html('<div class="esg-invito"><h2>Da dove partiamo?</h2>'
            '<p>Carica i documenti nella barra a sinistra e scrivi la tua domanda qui sotto.</p></div>')

for indice, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"], avatar=avatar(m["role"])):
        st.markdown(m["content"])
        if indice in st.session_state.misure:
            misure(st.session_state.misure[indice])

if domanda:
    with st.chat_message("user", avatar=AVATAR_UTENTE):
        st.markdown(domanda)
    inizio = time.time()
    aggiorna_testata(inizio)  # il cronometro del pannello parte
    with st.chat_message("assistant", avatar=AVATAR_AGENTE):
        with st.spinner(f"Il consulente sta leggendo e pensando ({modello})…"):
            try:
                testo, (entrata, uscita) = reply(domanda, st.session_state.messages,
                                                 st.session_state.kb_text, modello)
            except Exception as errore:
                testo, entrata, uscita = f"⚠️ Errore nella chiamata al modello: {errore}", 0, 0

    # Misure della richiesta, con il prezzo del modello scelto: si sommano ai totali della sessione
    prezzo_in, prezzo_out = PREZZI.get(modello, (0, 0))
    costo = (entrata * prezzo_in + uscita * prezzo_out) / 1_000_000
    durata = time.time() - inizio
    s = st.session_state
    s.ultima = {"secondi": durata, "token": entrata + uscita, "costo": costo, "modello": modello}
    s.secondi += durata
    s.tokens += entrata + uscita
    s.tok_in += entrata
    s.tok_out += uscita
    s.costo += costo
    s.misure[len(s.messages) + 1] = s.ultima
    s.messages += [
        {"role": "user", "content": domanda},
        {"role": "assistant", "content": testo},
    ]
    st.rerun()
