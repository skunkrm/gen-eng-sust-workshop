Agisci come un Senior Python Engineer. Trasforma il Sustainability Copilot in un agente che usa strumenti:
calcola le emissioni con codice tracciabile, verifica le fonti, crea grafici, report, passaporti di prodotto
e verbali HSE scaricabili, e accetta foto.

Ecco i file attuali:

[incolla qui il contenuto di config.py, extractor.py, engine.py e app.py]

Nuova struttura: config.py, extractor.py (invariato), ui.py (invariato), tools.py (nuovo), inventario.py (nuovo),
generator.py (nuovo), engine.py, app.py

## config.py
- MODELS: "anthropic.claude-haiku-5-5" ("Veloce ed economico (0,11 / 0,55 $), supporta tool e immagini"),
  "anthropic.claude-sonnet-5-5" ("Più preciso e più costoso (2,20 / 11 $), supporta tool e immagini"),
  "amazon.nova-lite-v1:0" ("Economico (0,08 / 0,32 $), senza tool"); MODEL = "anthropic.claude-haiku-5-5"
- client con timeout=180 e max_retries=0; PREZZI, MAX_TOKENS = 16000, LIMITI_TOKEN e max_tokens() come prima
- MAX_ITERATIONS = 12: giri massimi del ciclo agentico (modello -> strumento -> modello ...)
- SYSTEM_PROMPT: identità e formato come prima (Markdown, tabelle mai in HTML), più queste regole:
  "Quando ricevi dati numerici:
   1. prima di qualsiasi calcolo controlla la qualità dei dati (unità incoerenti, valori anomali rispetto agli
      altri mesi, dati mancanti), segnala cosa trovi e dichiara le correzioni che applichi;
   2. non fare mai calcoli a mente (somme, medie, percentuali, conversioni): per l'Excel dei consumi usa
      calcola_inventario, per poche voci singole calcola_emissioni;
   3. nelle risposte e nei documenti riporta solo i numeri restituiti dagli strumenti;
   4. per l'Excel dell'inventario usa crea_report_inventario, non crea_documento;
   5. indica sempre il fattore di emissione e la fonte usati."
  Poi l'elenco degli strumenti, una riga ciascuno (calcola_inventario, crea_report_inventario, calcola_emissioni,
  crea_grafico, crea_documento, crea_verbale_hse).
- nel SYSTEM_PROMPT anche le regole del Digital Product Passport, così all'utente basta una frase
  («Crea il Digital Product Passport della staffa SP-220 dai documenti caricati, in JSON e in PDF»):
  1. usa SOLO i documenti caricati e non inventare mai un dato;
  2. ogni campo ha la forma {"valore", "fonte", "citazione", "stato"}: fonte è il nome del file, citazione un estratto
     BREVE (5-12 parole) copiato parola per parola, perché il codice la verifica; stato è "documentato",
     "calcolato", "dato secondario" o "mancante"; se il dato non c'è, valore null e stato "mancante";
  3. un dato di un componente non vale per un altro;
  4. la carbon footprint è dalla culla al cancello e si calcola solo con calcola_emissioni, includendo TUTTI
     i componenti della distinta base e i consumi di processo per pezzo: se il fornitore dichiara un fattore (EPD)
     usa quello; se no, per l'acciaio usa acciaio_media_mondiale e marca il campo "dato secondario"; riporta
     il totale per pezzo e la quota da dati secondari. "calcolato" = ottenuto da uno strumento con dati dei
     documenti; "dato secondario" = usa un fattore generico di banca dati;
  5. se due documenti dicono cose diverse, riporta entrambi i valori in "incoerenze";
  6. sezioni: identificazione, produttore, composizione per componente, provenienza, contenuto riciclato per
     componente, carbon footprint, sostanze, smontaggio, fine vita, dati_mancanti, incoerenze;
  7. crea prima il JSON con crea_documento; se la verifica fallisce, richiama subito lo strumento con le citazioni
     corrette; poi il PDF con formato pdf e da_json_verificato true, senza riscrivere il contenuto;
  8. segnala le affermazioni non supportate e indica che il DPP è dimostrativo (atti delegati ESPR).
- in chiusura del SYSTEM_PROMPT:
  "Se l'utente manda una foto, descrivi solo ciò che vedi davvero e segnala i dubbi;
   per un verbale o un'ispezione HSE usa lo strumento crea_verbale_hse (non crea_documento): impagina il codice.
   Se un'informazione non è nei documenti caricati o non ne sei certo, dillo esplicitamente:
   meglio «non lo so» che un dato inventato."

## tools.py
- FATTORI: dizionario chiave -> (valore, unità, fonte):
  elettricita_rete 0.213 kg CO2/kWh (ISPRA, Settore elettrico ed. 2026, valore 2025, location-based);
  gas_naturale 2.02633 kg CO2e/Smc; gasolio 2.58354 kg CO2e/l; benzina 2.075 kg CO2e/l (DESNZ/DEFRA 2026);
  R410A 1924 e R32 677 kg CO2e/kg (IPCC AR5, GWP 100 anni);
  "Treno AV" 0.03092, "Aereo nazionale" 0.22928, "Aereo corto raggio" 0.12786, "Aereo lungo raggio" 0.15282
  kg CO2e per passeggero-km; "Auto propria" 0.17265 kg CO2e/km per veicolo (DESNZ/DEFRA 2026);
  acciaio_media_mondiale 1.92 kg CO2/kg (worldsteel, Sustainability Indicators 2025, dato secondario)
- TOOLS: definizione OpenAI di sei strumenti, con descrizioni che dicono al modello quando usarli
  - calcola_inventario(stima_mancanti facoltativo): inventario GHG letto direttamente dall'Excel dei consumi
  - crea_report_inventario(nome_file, valori_dichiarati facoltativo, es. {"Scope 1": 1106, "Scope 2": 2657})
  - calcola_emissioni(voci): ogni voce ha descrizione, scope (enum Scope 1/2/3), fattore (enum delle chiavi di FATTORI
    più "dichiarato_fornitore"), quantita, e per i viaggi andata_ritorno (bool) e persone (int). Raddoppia se
    andata_ritorno, moltiplica per persone solo per treni e aerei. Con "dichiarato_fornitore" servono valore_fattore,
    unita_fattore e fonte_fattore presi da un documento (es. EPD). Restituisce le voci in kg e t CO2e, i totali per
    scope in t e in kg, il totale, la quota da dati secondari e il numero di voci
  - crea_grafico(titolo, etichette, valori, unita, serie_confronto facoltativa, nomi_serie facoltativo)
  - crea_documento(formato pdf|docx|xlsx|json, nome_file, titolo, contenuto in markdown semplice o JSON,
    includi_grafico, includi_foto, da_json_verificato)
  - crea_verbale_hse(nome_file, titolo, luogo, data, ispettore, oggetto,
    non_conformita [{osservazione, rischio, riferimento, priorita alta|media|bassa}],
    azioni [{azione, rif_non_conformita, priorita}], limiti [testi]): il modello decide i contenuti,
    l'impaginazione è fissa nel codice; le foto inviate entrano da sole
- verifica delle fonti (il codice controlla l'AI): prima di creare un JSON, per ogni campo {"valore", "stato", ...}
  con stato "documentato" controlla che la citazione compaia nel testo dei documenti caricati; la normalizzazione
  ignora il formato ma non il contenuto (minuscole, punteggiatura, separatori | e virgolette ignorati,
  3,21 e 3.21 equivalenti); i campi "mancante" non devono avere un valore. Se il controllo fallisce, non creare
  il file e restituisci al modello l'elenco dei campi da correggere; se passa, aggiungi al risultato
  "Verifica delle fonti superata: N citazioni trovate nei documenti, M campi dichiarati mancanti."
  e salva il JSON verificato in stato["ultimo_dpp"]
- execute_tool(name, args, stato) -> (risultato testuale per il modello, evento per l'interfaccia o None);
  stato è un dizionario di sessione con ultimo grafico, ultimo inventario, ultimo DPP, foto ed Excel caricati;
  gli errori tornano al modello come testo, così può correggersi

## inventario.py: l'inventario GHG lo calcola il codice, non il modello
- calcola(files, stima_mancanti=False): legge l'Excel caricato (fogli Consumi_energia, Flotta, Refrigeranti,
  Viaggi_lavoro, Fattori_emissione, intestazioni nella terza riga); per ogni sito controlla le serie mensili:
  un valore oltre 50 volte la mediana è un errore di unità (Wh invece di kWh), va diviso per 1000 e dichiarato;
  un mese mancante va escluso e dichiarato, oppure stimato con la media se stima_mancanti è true;
  restituisce controlli_qualita e totali per categoria, scope e sito
- pubblico(inv): il risultato per il modello, senza il dettaglio riga per riga (chiavi che iniziano con "_")
- report_excel(inventario, valori_dichiarati): Excel con fogli di dettaglio, controlli di qualità, fattori
  e un riepilogo con formule SUM/SUMIF, più il confronto con i valori dichiarati nel bilancio

## generator.py (tutto in memoria con BytesIO, mai file su disco)
- make_chart(...) -> PNG con matplotlib (backend "Agg"), barre affiancate se c'è la serie di confronto
- make_document(formato, nome_file, titolo, contenuto, grafico=None, foto=None) -> (bytes, nome file, mime)
- il contenuto usa "# " e "## " per i titoli, "- " per gli elenchi, righe con "|" per le tabelle
  (salta le righe |---|); in Excel converti i numeri in formato italiano (1.234,5 e 12%) in numeri veri
- PDF con fpdf2: una classe _Report(FPDF) con fascia scura d'intestazione e linea verde e ambra sulla prima pagina,
  testatina sulle altre, piè di pagina "Documento generato con l'AI: da verificare prima dell'uso" e
  "Pagina n di N"; tabelle a righe alterne, righe "Etichetta: valore" con l'etichetta in grassetto, elenchi
  con punto verde, un titolo non resta mai da solo in fondo alla pagina, sezione foto se richiesta
- i font standard sono latin-1: sostituisci € ’ “ ” – — ₂ ecc. con equivalenti
- foto: applica la rotazione EXIF e ridimensiona prima di inserirla
- make_verbale_hse(dati, foto) -> PDF a impaginazione fissa: riquadro con luogo, data, ispettore e fonte;
  oggetto con la foto accanto; numero di non conformità e riquadri per priorità; tabella delle non conformità
  e tabella delle azioni con la cella della priorità colorata (alta rossa, media ambra, bassa verde);
  riquadro ambra dei limiti; due riquadri per le firme
- make_dpp_pdf(dpp, nome_file, titolo, grafico=None): PDF del passaporto generato dal JSON verificato,
  con tabelle Campo / Valore / Fonte / Stato, sì e no al posto di true e false, intestazioni leggibili
  al posto dei nomi con il trattino basso
- json: verifica che il contenuto sia JSON valido (togli eventuali ```json), salvalo indentato in UTF-8;
  se non è valido, solleva un errore chiaro così il modello può correggersi

## engine.py
- reply(message, history, knowledge_base="", model=MODEL, images=None, stato=None) è un GENERATORE di eventi:
  ("step", testo), ("calc", dati), ("chart", dati), ("file", dati), ("check", esito della verifica non superata),
  ("tokens", (input, output)) dopo ogni chiamata, ("done", testo)
- system prompt e documenti come primo scambio utente/assistente (il ruolo "system" non è accettato);
  stato["documenti"] = knowledge_base, serve alla verifica delle fonti
- le foto vanno nel messaggio dell'utente come parti {"type": "image_url", "image_url": {"url": "data:<mime>;base64,..."}}
- ciclo di al massimo MAX_ITERATIONS giri con tools=TOOLS e max_tokens(model); se il modello chiama strumenti,
  gestiscili TUTTI: un messaggio assistant con tutti i tool_calls, poi un messaggio role "tool" per ciascuno
  con il suo tool_call_id
- se l'ultimo strumento è fallito (o la risposta è stata troncata) e il modello si ferma senza riprovare,
  chiedigli di completare, al massimo due volte
- se il modello non supporta tool o immagini (BadRequestError, PermissionDeniedError), riprova senza
  e avvisa l'utente in fondo alla risposta

## app.py (stessa interfaccia degli step precedenti, con ui.py)
- uploader unico nella sidebar per pdf, docx, xlsx, png, jpg, jpeg: i documenti vanno nella knowledge base,
  le foto partono solo con la domanda successiva (st.session_state.foto_inviate) e restano in stato["foto"]
  per il verbale; gli Excel passano così come sono a stato["file_excel"] (nome e bytes)
- durante la risposta mostra i passaggi in un st.status "L'agente sta lavorando…": giri, strumenti usati,
  sintesi dei calcoli, verifica delle fonti superata o non superata, file creati
- a ogni evento "tokens" calcola il costo con PREZZI del modello scelto e aggiorna subito la testata,
  così tempo, token e costo scorrono mentre l'agente lavora
- sotto ogni risposta: le misure (tempo, token, costo, modello), i grafici con st.image, i file con
  st.download_button e un expander "Passaggi dell'agente" (st.session_state.allegati: indice del messaggio -> lista)
- non mettere mai i bytes dei file nei messaggi inviati al modello; aggiungi in fondo alla risposta
  "File creati: ..." così il modello sa cosa ha già prodotto
- "Nuova conversazione" svuota messaggi, allegati e stato, ma non token, costo e tempo della sessione

Per installare i pacchetti usa: uv add fpdf2 matplotlib

Output: solo i file completi, pronti da eseguire con: uv run streamlit run app.py
