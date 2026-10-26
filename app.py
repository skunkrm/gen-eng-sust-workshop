"""Sustainability Copilot, step 1: il consulente di sostenibilità in chat. Avvio: uv run streamlit run app.py"""

import time

import streamlit as st

from config import MODEL, PREZZI
from engine import reply
from ui import AVATAR_AGENTE, AVATAR_UTENTE, NOME, misure, stile, testata

FRASI = ["risponde su CSRD, ESRS e GHG Protocol.", "parla la nostra lingua.",
         "controlla i dati prima di commentarli.", "indica sempre fattori e fonti."]

st.set_page_config(page_title=NOME, page_icon="🌱", layout="wide", initial_sidebar_state="expanded")
stile()
intestazione = st.empty()  # la riempiamo dopo la sidebar, quando sappiamo modello e documenti

# tokens (di cui tok_in di input e tok_out di output), costo e secondi: totali della sessione;
# ultima: misure dell'ultima richiesta; misure: indice del messaggio -> misure di quella risposta
DEFAULT = {"messages": [], "tokens": 0, "tok_in": 0, "tok_out": 0, "costo": 0.0, "secondi": 0.0,
           "ultima": {}, "misure": {}}
for chiave, valore in DEFAULT.items():
    if chiave not in st.session_state:
        st.session_state[chiave] = valore

with st.sidebar:
    st.subheader("Modello")
    modello = MODEL  # in questo step il modello è fisso: si cambia in config.py
    st.code(modello, language=None)

    st.subheader("Sessione")
    if st.button("Nuova conversazione"):  # token, costo e tempo restano: sono della sessione
        st.session_state.messages, st.session_state.misure = [], {}
        st.rerun()


def aggiorna_testata(inizio=None):
    """inizio: istante di partenza della richiesta in corso (None se il consulente è fermo)."""
    s = st.session_state
    testata(intestazione, modello, 0, s.tokens, s.costo, s.secondi, s.ultima,
            inizio=inizio, tok_in=s.tok_in, tok_out=s.tok_out, frasi=FRASI)


aggiorna_testata()


def avatar(ruolo):
    return AVATAR_UTENTE if ruolo == "user" else AVATAR_AGENTE


domanda = st.chat_input("Chiedi qualcosa al consulente di sostenibilità…")

if not st.session_state.messages and not domanda:
    st.html('<div class="esg-invito"><h2>Da dove partiamo?</h2>'
            '<p>Scrivi la tua domanda qui sotto: il consulente risponde con il suo mestiere, senza documenti.</p></div>')

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
        with st.spinner("Il consulente sta pensando…"):
            try:
                testo, (entrata, uscita) = reply(domanda, st.session_state.messages)
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
