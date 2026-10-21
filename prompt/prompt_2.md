Estendi il progetto: il consulente ESG deve leggere i documenti caricati dall'utente.

Ecco i file attuali:

[incolla qui il contenuto di config.py, engine.py e app.py]

Nuova struttura: config.py, engine.py, app.py, extractor.py

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
  "anthropic.claude-sonnet-4-6": "Più costoso, più preciso"
- MODEL resta "amazon.nova-lite-v1:0"

engine.py:
- reply(message, history, knowledge_base="", model=MODEL)
- se c'è una knowledge_base, aggiungila in coda al system prompt con l'istruzione di usare
  i documenti e di citare il documento da cui prende ogni informazione

app.py:
- nella sidebar un selectbox per scegliere il modello tra quelli di MODELS
- nella sidebar un file_uploader per PDF, DOCX e XLSX con accept_multiple_files=True
- il testo estratto va in st.session_state.kb_text; rileggi i file solo quando cambia
  la lista dei nomi caricati

Regole: non cambiare l'architettura senza motivo, codice semplice, commenti in italiano.
Per installare i pacchetti usa: uv add pypdf python-docx openpyxl

Output: solo i file completi, nuovi e modificati, pronti da eseguire con: uv run streamlit run app.py
