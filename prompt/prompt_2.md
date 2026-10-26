Estendi il progetto: il Sustainability Copilot deve leggere i documenti caricati dall'utente.

Ecco i file attuali:

[incolla qui il contenuto di config.py, engine.py e app.py]

Nuova struttura: config.py, engine.py, app.py, extractor.py (ui.py resta invariato)

extractor.py (nuovo):
- extract_text(file): riceve un UploadedFile di Streamlit (ha l'attributo .name) e restituisce il testo
- PDF con pypdf (from pypdf import PdfReader), indicando il numero di pagina
- Word con python-docx (import docx), compresi i testi delle tabelle
- Excel con openpyxl (data_only=True): per ogni foglio scrivi "[Foglio: nome]" e poi ogni riga
  non vuota con i valori separati da " | "
- build_knowledge_base(files): unisce i testi, ciascuno preceduto da "===== DOCUMENTO: nome ====="

config.py:
- aggiungi MODELS, un dizionario modello -> descrizione:
  "amazon.nova-lite-v1:0": "Economico, meno preciso"
  "anthropic.claude-haiku-5-5": "Veloce, preciso, costa poco"
  "anthropic.claude-sonnet-5-5": "Più costoso, più preciso"
- MODEL = "amazon.nova-lite-v1:0": si parte dal più economico per confrontarlo con gli altri
- timeout del client a 180 secondi: con i documenti le risposte sono più lunghe
- PREZZI, MAX_TOKENS = 16000 e LIMITI_TOKEN (Nova Lite 8.000) restano come sono
- nel system prompt sostituisci le ultime due righe con:
  "Quando usi un fattore di emissione, indica valore e fonte; se la domanda non lo richiede, non citarne.
  Se un'informazione non è nei documenti caricati o non ne sei certo, dillo esplicitamente:
  meglio «non lo so» che un dato inventato."

engine.py:
- reply(message, history, knowledge_base="", model=MODEL), sempre con risultato (testo, (input, output))
  e max_tokens(model) come tetto
- se c'è una knowledge_base, aggiungila in coda al system prompt con l'istruzione:
  "L'utente ha caricato questi documenti. Usali per rispondere e cita il documento da cui prendi ogni informazione."

app.py:
- FRASI: "legge bilanci, Word ed Excel.", "fa la gap analysis sugli ESRS.",
  "cita il documento da cui prende ogni dato.", "controlla i dati prima di commentarli."
- nella sidebar un selectbox per scegliere il modello tra quelli di MODELS (con la descrizione accanto al nome)
- nella sidebar un file_uploader per PDF, DOCX e XLSX con accept_multiple_files=True
- il testo estratto va in st.session_state.kb_text; rileggi i file solo quando cambia
  la lista dei nomi caricati (st.session_state.kb_names)
- testata() riceve il modello scelto e il numero di documenti letti; il costo si calcola con il prezzo
  del modello scelto, così cambiando modello si vede subito la differenza
- l'invito a chat vuota diventa: "Carica i documenti nella barra a sinistra e scrivi la tua domanda qui sotto."

Regole: non cambiare l'architettura senza motivo, codice semplice, commenti in italiano.
Per installare i pacchetti usa: uv add pypdf python-docx openpyxl

Output: solo i file completi, nuovi e modificati, pronti da eseguire con: uv run streamlit run app.py
