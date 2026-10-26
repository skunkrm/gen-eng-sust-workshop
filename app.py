"""Sustainability Copilot: l'agente che legge, calcola e crea report. Avvio: uv run streamlit run app.py"""

import time

import streamlit as st

from config import MODEL, MODELS, PREZZI
from engine import reply
from extractor import build_knowledge_base
from ui import AVATAR_AGENTE, AVATAR_UTENTE, NOME, misure, stile, testata

st.set_page_config(page_title=NOME, page_icon="🌱", layout="wide", initial_sidebar_state="expanded")
stile()
intestazione = st.empty()  # la riempiamo dopo la sidebar, quando sappiamo modello e documenti

# tokens (di cui tok_in di input e tok_out di output), costo e secondi: totali della sessione;
# ultima: misure dell'ultima richiesta
DEFAULT = {"messages": [], "tokens": 0, "tok_in": 0, "tok_out": 0, "costo": 0.0, "secondi": 0.0, "ultima": {}, "kb_text": "", "kb_names": [], "allegati": {},
           "foto_inviate": set(), "stato": {}}
for chiave, valore in DEFAULT.items():
    if chiave not in st.session_state:
        st.session_state[chiave] = valore

IMMAGINI = ("png", "jpg", "jpeg")

with st.sidebar:
    st.subheader("Modello")
    modello = st.selectbox("Modello", list(MODELS), index=list(MODELS).index(MODEL),
                           format_func=lambda m: f"{m} — {MODELS[m]}", label_visibility="collapsed")

    st.subheader("Documenti e foto")
    files = st.file_uploader("PDF, Word, Excel o foto", type=["pdf", "docx", "xlsx", *IMMAGINI],
                             accept_multiple_files=True) or []
    documenti = [f for f in files if not f.name.lower().endswith(IMMAGINI)]
    foto = [f for f in files if f.name.lower().endswith(IMMAGINI)]

    nomi = sorted(f.name for f in documenti)
    if nomi != st.session_state.kb_names:  # rileggiamo i documenti solo se sono cambiati
        st.session_state.kb_text = build_knowledge_base(documenti) if documenti else ""
        st.session_state.kb_names = nomi
    if nomi:
        st.success(f"{len(nomi)} documento/i in memoria")
    nuove_foto = [f for f in foto if f.name not in st.session_state.foto_inviate]
    if nuove_foto:
        st.info(f"{len(nuove_foto)} foto verranno inviate con la prossima domanda")

    st.subheader("Sessione")
    if st.button("Nuova conversazione"):
        for chiave in ("messages", "allegati", "stato"):  # token, costo e tempo restano: sono della sessione
            st.session_state[chiave] = type(DEFAULT[chiave])()
        st.rerun()


def aggiorna_testata(inizio=None, entrata=0, uscita=0, costo_richiesta=0.0):
    """inizio: istante di partenza della richiesta in corso (None se l'agente è fermo);
    entrata, uscita, costo_richiesta: token e costo della richiesta in corso, da sommare ai totali."""
    s = st.session_state
    testata(intestazione, modello, len(s.kb_names), s.tokens, s.costo, s.secondi, s.ultima,
            inizio=inizio, token_richiesta=entrata + uscita, costo_richiesta=costo_richiesta,
            tok_in=s.tok_in + entrata, tok_out=s.tok_out + uscita)


aggiorna_testata()


def mostra_allegati(indice):
    for i, a in enumerate(st.session_state.allegati.get(indice, [])):
        if a["tipo"] == "chart":
            st.image(a["png"], caption=a["titolo"])
            st.download_button("⬇️ Scarica grafico (PNG)", a["png"], file_name="grafico.png",
                               mime="image/png", key=f"g{indice}_{i}")
        elif a["tipo"] == "file":
            st.download_button(f"⬇️ Scarica {a['filename']}", a["data"], file_name=a["filename"],
                               mime=a["mime"], key=f"f{indice}_{i}")
        elif a["tipo"] == "foto":
            st.image(a["data"], width=260)
        elif a["tipo"] == "misure":
            misure(a)
        elif a["tipo"] == "passi":
            with st.expander("Passaggi dell'agente"):
                st.markdown("\n".join(f"- {r}" for r in a["righe"]))


def avatar(ruolo):
    return AVATAR_UTENTE if ruolo == "user" else AVATAR_AGENTE


domanda = st.chat_input("Chiedi qualcosa al consulente di sostenibilità…")

# Pagina iniziale: solo un invito, la domanda la scrive l'utente
if not st.session_state.messages and not domanda:
    st.html('<div class="esg-invito"><h2>Da dove partiamo?</h2>'
            '<p>Carica i documenti nella barra a sinistra e scrivi la tua domanda qui sotto.</p></div>')

for indice, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"], avatar=avatar(m["role"])):
        st.markdown(m["content"])
        mostra_allegati(indice)

if domanda:
    immagini = [{"data": f.getvalue(), "mime": f.type or "image/jpeg", "name": f.name} for f in nuove_foto]
    indice_utente = len(st.session_state.messages)
    st.session_state.allegati[indice_utente] = [{"tipo": "foto", "data": i["data"]} for i in immagini]
    with st.chat_message("user", avatar=AVATAR_UTENTE):
        st.markdown(domanda)
        mostra_allegati(indice_utente)

    if immagini:  # le foto restano disponibili per i documenti (es. il verbale con la foto)
        st.session_state.stato["foto"] = [i["data"] for i in immagini]

    # Gli Excel caricati servono così come sono allo strumento calcola_inventario
    st.session_state.stato["file_excel"] = [(f.name, f.getvalue()) for f in documenti
                                            if f.name.lower().endswith(".xlsx")]

    indice_risposta = indice_utente + 1
    allegati, nomi_file, testo, passi = [], [], "", []
    inizio = time.time()
    entrata_tot, uscita_tot, costo_richiesta = 0, 0, 0.0  # token e costo di questa richiesta
    aggiorna_testata(inizio)
    with st.chat_message("assistant", avatar=AVATAR_AGENTE):
        with st.status("L'agente sta lavorando…", expanded=True) as pannello:
            try:
                for tipo, dati in reply(domanda, st.session_state.messages, st.session_state.kb_text,
                                        modello, immagini, st.session_state.stato):
                    if tipo == "step":
                        st.markdown(dati)
                        passi.append(dati)
                    elif tipo == "calc":
                        if dati["totale_t_CO2e"] >= 1:
                            sintesi = ", ".join(f"{k} = {v:,.1f} t CO2e" for k, v in dati["totali_per_scope_t_CO2e"].items())
                        else:  # valori piccoli, per esempio un singolo prodotto: meglio in kg
                            sintesi = f"totale = {dati['totale_kg_CO2e']:,.2f} kg CO2e"
                        st.markdown(f"🧮 Calcolate **{dati['numero_voci']} voci**: {sintesi}")
                        passi.append(f"🧮 Calcolate {dati['numero_voci']} voci: {sintesi}")
                    elif tipo == "chart":
                        allegati.append({"tipo": "chart", **dati})
                        st.markdown(f"📊 Grafico creato: {dati['titolo']}")
                    elif tipo == "check":
                        st.markdown(f"🔎 **Verifica delle fonti non superata**: {len(dati['errori'])} problemi, "
                                    "il modello deve correggere")
                        passi.append(f"🔎 Verifica delle fonti non superata: {len(dati['errori'])} problemi")
                        for errore in dati["errori"][:5]:
                            st.markdown(f"- {errore}")
                            passi.append(f"    {errore}")
                    elif tipo == "file":
                        allegati.append({"tipo": "file", **dati})
                        nomi_file.append(dati["filename"])
                        st.markdown(f"📄 File creato: {dati['filename']}")
                        if dati.get("verifica"):
                            v = dati["verifica"]
                            st.markdown(f"🔎 Verifica delle fonti superata: {v['citazioni_verificate']} citazioni "
                                        f"trovate nei documenti, {v['campi_mancanti']} campi mancanti dichiarati")
                            passi.append(f"🔎 Verifica superata: {v['citazioni_verificate']} citazioni, "
                                         f"{v['campi_mancanti']} campi mancanti")
                        passi.append(f"📄 File creato: {dati['filename']}")
                    elif tipo == "tokens":  # token e costo, col prezzo del modello scelto, in tempo reale
                        entrata, uscita = dati
                        prezzo_in, prezzo_out = PREZZI.get(modello, (0, 0))
                        entrata_tot += entrata
                        uscita_tot += uscita
                        costo_richiesta += (entrata * prezzo_in + uscita * prezzo_out) / 1_000_000
                        aggiorna_testata(inizio, entrata_tot, uscita_tot, costo_richiesta)
                    elif tipo == "done":
                        testo = dati
                pannello.update(label="Fatto", state="complete", expanded=False)
            except Exception as errore:
                testo = f"⚠️ Errore nella chiamata al modello: {errore}"
                pannello.update(label="Errore", state="error")

    # Misure della richiesta: si sommano ai totali della sessione
    durata = time.time() - inizio
    st.session_state.ultima = {"secondi": durata, "token": entrata_tot + uscita_tot, "costo": costo_richiesta,
                               "modello": modello}
    st.session_state.secondi += durata
    st.session_state.tokens += entrata_tot + uscita_tot
    st.session_state.tok_in += entrata_tot
    st.session_state.tok_out += uscita_tot
    st.session_state.costo += costo_richiesta
    allegati.insert(0, {"tipo": "misure", **st.session_state.ultima})

    # Lasciamo traccia dei file nella conversazione, così il modello sa cosa ha già creato
    if nomi_file:
        testo += "\n\n_File creati: " + ", ".join(nomi_file) + "_"
    st.session_state.foto_inviate.update(i["name"] for i in immagini)
    st.session_state.messages += [
        {"role": "user", "content": domanda},
        {"role": "assistant", "content": testo},
    ]
    if passi:
        allegati.append({"tipo": "passi", "righe": passi})
    st.session_state.allegati[indice_risposta] = allegati
    st.rerun()
