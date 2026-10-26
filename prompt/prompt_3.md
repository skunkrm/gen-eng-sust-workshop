Agisci come un Senior Python Engineer. Trasforma il consulente ESG in un agente che usa strumenti:
calcola le emissioni con codice tracciabile, crea grafici e file scaricabili, e accetta foto.

Ecco i file attuali:

[incolla qui il contenuto di config.py, extractor.py, engine.py e app.py]

Nuova struttura: config.py, extractor.py (invariato), tools.py (nuovo), generator.py (nuovo), engine.py, app.py

config.py:
- MODELS: "anthropic.claude-sonnet-4-6" ("Preciso, supporta tool e immagini") e
  "amazon.nova-lite-v1:0" ("Economico, senza tool"); MODEL = "anthropic.claude-sonnet-4-6"
- MAX_TOKENS = 8192, MAX_ITERATIONS = 8
- aggiungi al system prompt queste regole:
  "1. prima di qualsiasi calcolo controlla la qualità dei dati, segnala cosa trovi e dichiara le correzioni;
   2. non calcolare mai le emissioni a mente: usa sempre lo strumento calcola_emissioni, passando i valori
      singoli così come sono nei dati (per sito e mese, per veicolo, per viaggio) senza sommarli tu;
   3. indica sempre fattore di emissione e fonte.
   Per un Digital Product Passport usa solo dati presenti nei documenti, indica la fonte di ogni campo,
   elenca i dati mancanti senza inventarli e segnala le affermazioni non supportate.
   Se l'utente manda una foto, descrivi solo ciò che vedi davvero e segnala i dubbi."

tools.py:
- FATTORI: dizionario chiave -> (valore, unità, fonte), con questi valori:
  elettricita_rete 0.213 kg CO2/kWh (ISPRA ed. 2026, valore 2025); gas_naturale 2.02633 kg CO2e/Smc;
  gasolio 2.58354 kg CO2e/l; benzina 2.075 kg CO2e/l (DESNZ/DEFRA 2026); R410A 1924 e R32 677 kg CO2e/kg (IPCC AR5);
  "Treno AV" 0.03092, "Aereo nazionale" 0.22928, "Aereo corto raggio" 0.12786, "Aereo lungo raggio" 0.15282
  kg CO2e per passeggero-km; "Auto propria" 0.17265 kg CO2e/km per veicolo (DESNZ/DEFRA 2026);
  acciaio_media_mondiale 1.92 kg CO2/kg (worldsteel, Sustainability Indicators 2025, dato secondario)
- TOOLS: definizione OpenAI di tre strumenti
  - calcola_emissioni(voci): ogni voce ha descrizione, scope (enum Scope 1/2/3), fattore (enum delle chiavi di FATTORI),
    quantita, e per i viaggi andata_ritorno (bool) e persone (int). Raddoppia se andata_ritorno, moltiplica per persone
    solo per treni e aerei. Accetta anche fattore "dichiarato_fornitore" con valore_fattore, unita_fattore e
    fonte_fattore presi da un documento (es. EPD). Restituisce le voci calcolate in kg e t CO2e, i totali per scope
    in t e in kg, il totale e la quota di emissioni calcolata con dati secondari
  - crea_grafico(titolo, etichette, valori, unita, serie_confronto facoltativa, nomi_serie facoltativo)
  - crea_documento(formato pdf|docx|xlsx|json, nome_file, titolo, contenuto in markdown semplice o JSON, includi_grafico)
- execute_tool(name, args, stato) -> (risultato testuale per il modello, evento per l'interfaccia o None);
  stato è un dizionario di sessione dove salvi l'ultimo grafico; gli errori tornano al modello come testo

generator.py (tutto in memoria con BytesIO, mai file su disco):
- make_chart(...) -> PNG con matplotlib (backend "Agg"), barre affiancate se c'è la serie di confronto
- make_document(formato, nome_file, titolo, contenuto, grafico=None) -> (bytes, nome file, mime)
- il contenuto usa "# " e "## " per i titoli, "- " per gli elenchi, righe con "|" per le tabelle
  (salta le righe |---|); in Excel converti i numeri in formato italiano (1.234,5 e 12%) in numeri veri
- PDF con fpdf2 (from fpdf import FPDF): i font standard sono latin-1, quindi sostituisci € ’ “ ” – — ₂ → ecc.
- json: verifica che il contenuto sia JSON valido (togli eventuali ```json), salvalo indentato in UTF-8;
  se non è valido, solleva un errore chiaro così il modello può correggersi
- verifica delle fonti (in tools.py): prima di creare un JSON, per ogni campo {"valore", "fonte", "citazione", "stato"}
  con stato "documentato" controlla che la citazione (normalizzata: minuscole, spazi compattati) compaia nel testo
  dei documenti caricati; i campi "mancante" non devono avere un valore. Se il controllo fallisce, non creare
  il file e restituisci al modello l'elenco dei campi da correggere

engine.py:
- reply(message, history, knowledge_base="", model=MODEL, images=None, stato=None) è un GENERATORE di eventi:
  ("step", testo), ("calc", dati), ("chart", dati), ("file", dati), ("tokens", n), ("done", testo)
- system prompt come primo scambio utente/assistente (il ruolo "system" non è accettato)
- le foto vanno nel messaggio dell'utente come parti {"type": "image_url", "image_url": {"url": "data:<mime>;base64,..."}}
- ciclo di al massimo MAX_ITERATIONS giri con tools=TOOLS; se il modello chiama strumenti, gestiscili TUTTI:
  aggiungi un messaggio assistant con tutti i tool_calls, poi un messaggio role "tool" per ciascuno con il suo tool_call_id
- se il modello non supporta tool o immagini (BadRequestError, PermissionDeniedError), riprova senza e avvisa l'utente

app.py:
- layout wide, titolo "🌱 ESG Copilot"
- sidebar: pulsante "📦 Prompt Digital Product Passport" che invia il prompt PROMPT_DPP definito in config.py; scelta del modello, uploader per pdf, docx, xlsx, png, jpg (documenti nella knowledge base,
  foto inviate solo con la domanda successiva), contatore token, "Nuova conversazione"
- durante la risposta mostra i passaggi in un st.status; grafici con st.image, file con st.download_button
  sotto il messaggio giusto (st.session_state.allegati: indice del messaggio -> lista)
- non mettere mai i bytes dei file nei messaggi inviati al modello; aggiungi in fondo alla risposta
  "File creati: ..." così il modello sa cosa ha già prodotto

Per installare i pacchetti usa: uv add fpdf2 matplotlib

Output: solo i file completi, pronti da eseguire con: uv run streamlit run app.py
