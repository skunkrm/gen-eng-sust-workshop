"""ESG Copilot: l'agente che legge, calcola e crea report. Avvio: uv run streamlit run app.py"""

import streamlit as st

from config import MODEL, MODELS, PROMPT_DPP
from engine import reply
from extractor import build_knowledge_base

st.set_page_config(page_title="ESG Copilot", page_icon="🌱", layout="wide")
st.title("🌱 ESG Copilot")
st.caption("Il consulente CSRD ed ESRS che legge i documenti, calcola le emissioni e prepara i report")

DEFAULT = {"messages": [], "tokens": 0, "kb_text": "", "kb_names": [], "allegati": {},
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

    st.subheader("Prompt pronti")
    if st.button("📦 Prompt Digital Product Passport"):
        st.session_state.prompt_pronto = PROMPT_DPP

    st.metric("Token usati in questa sessione", f"{st.session_state.tokens:,}".replace(",", "."))
    if st.button("Nuova conversazione"):
        for chiave in ("messages", "allegati", "stato"):
            st.session_state[chiave] = type(DEFAULT[chiave])()
        st.rerun()


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


for indice, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        mostra_allegati(indice)

domanda = st.chat_input("Chiedi qualcosa al consulente ESG…") or st.session_state.pop("prompt_pronto", None)
if domanda:
    immagini = [{"data": f.getvalue(), "mime": f.type or "image/jpeg", "name": f.name} for f in nuove_foto]
    indice_utente = len(st.session_state.messages)
    st.session_state.allegati[indice_utente] = [{"tipo": "foto", "data": i["data"]} for i in immagini]
    with st.chat_message("user"):
        st.markdown(domanda)
        mostra_allegati(indice_utente)

    # Gli Excel caricati servono così come sono allo strumento calcola_inventario
    st.session_state.stato["file_excel"] = [(f.name, f.getvalue()) for f in documenti
                                            if f.name.lower().endswith(".xlsx")]

    indice_risposta = indice_utente + 1
    allegati, nomi_file, testo = [], [], ""
    with st.chat_message("assistant"):
        with st.status("L'agente sta lavorando…", expanded=True) as pannello:
            try:
                for tipo, dati in reply(domanda, st.session_state.messages, st.session_state.kb_text,
                                        modello, immagini, st.session_state.stato):
                    if tipo == "step":
                        st.markdown(dati)
                    elif tipo == "calc":
                        if dati["totale_t_CO2e"] >= 1:
                            sintesi = ", ".join(f"{k} = {v:,.1f} t CO2e" for k, v in dati["totali_per_scope_t_CO2e"].items())
                        else:  # valori piccoli, per esempio un singolo prodotto: meglio in kg
                            sintesi = f"totale = {dati['totale_kg_CO2e']:,.2f} kg CO2e"
                        st.markdown(f"🧮 Calcolate **{dati['numero_voci']} voci**: {sintesi}")
                    elif tipo == "chart":
                        allegati.append({"tipo": "chart", **dati})
                        st.markdown(f"📊 Grafico creato: {dati['titolo']}")
                    elif tipo == "check":
                        st.markdown(f"🔎 **Verifica delle fonti non superata**: {len(dati['errori'])} problemi, "
                                    "il modello deve correggere")
                        for errore in dati["errori"][:5]:
                            st.markdown(f"- {errore}")
                    elif tipo == "file":
                        allegati.append({"tipo": "file", **dati})
                        nomi_file.append(dati["filename"])
                        st.markdown(f"📄 File creato: {dati['filename']}")
                        if dati.get("verifica"):
                            v = dati["verifica"]
                            st.markdown(f"🔎 Verifica delle fonti superata: {v['citazioni_verificate']} citazioni "
                                        f"trovate nei documenti, {v['campi_mancanti']} campi mancanti dichiarati")
                    elif tipo == "tokens":
                        st.session_state.tokens += dati
                    elif tipo == "done":
                        testo = dati
                pannello.update(label="Fatto", state="complete", expanded=False)
            except Exception as errore:
                testo = f"⚠️ Errore nella chiamata al modello: {errore}"
                pannello.update(label="Errore", state="error")

    # Lasciamo traccia dei file nella conversazione, così il modello sa cosa ha già creato
    if nomi_file:
        testo += "\n\n_File creati: " + ", ".join(nomi_file) + "_"
    st.session_state.foto_inviate.update(i["name"] for i in immagini)
    st.session_state.messages += [
        {"role": "user", "content": domanda},
        {"role": "assistant", "content": testo},
    ]
    st.session_state.allegati[indice_risposta] = allegati
    st.rerun()
