Trasforma questo progetto in un chatbot web con Streamlit: il Sustainability Copilot, un consulente di sostenibilità.

Ecco il main.py dello step precedente:

[incolla qui il contenuto di main.py]

L'interfaccia grafica sta in un file a parte, ui.py, che trovi già pronto nel branch (come è stato costruito
è descritto in prompt/prompt_ui.md). Non modificarlo: usalo da app.py così come è. Ecco cosa espone:
- NOME = "Sustainability Copilot", AVATAR_UTENTE, AVATAR_AGENTE
- stile(): da chiamare una volta, subito dopo st.set_page_config
- testata(contenitore, modello, documenti, token, dollari, secondi, ultima, inizio=None,
  token_richiesta=0, costo_richiesta=0.0, tok_in=0, tok_out=0, frasi=None): disegna l'intestazione
  e il pannello "Tempi e costi"; token, dollari e secondi sono i totali della sessione, ultima è il dizionario
  delle misure dell'ultima richiesta, inizio è time.time() della richiesta in corso (None se il consulente è fermo)
- misure(a): la riga sotto una risposta, con a = {"secondi", "token", "costo", "modello"}
- ui.py importa PREZZI da config.py

Struttura da generare: config.py, engine.py, app.py

config.py:
- legge GEN_ENGINE_API_KEY e GEN_ENGINE_BASE_URL dal file .env; se la chiave manca, termina con un messaggio chiaro
- crea il client OpenAI come variabile di modulo, con timeout=120 e max_retries=0
  (nessun nuovo tentativo automatico: se il modello non risponde lo vediamo subito)
- MODEL = "anthropic.claude-haiku-5-5"
- PREZZI, dollari per milione di token (input, output), dal Models catalog:
  "anthropic.claude-haiku-5-5": (0.11, 0.55), "anthropic.claude-sonnet-5-5": (2.20, 11.0),
  "amazon.nova-lite-v1:0": (0.0824, 0.3193)
- MAX_TOKENS = 16000: i modelli recenti ragionano prima di rispondere e il ragionamento consuma token,
  con un tetto basso la risposta può arrivare vuota
- LIMITI_TOKEN = {"amazon.nova-lite-v1:0": 8000} (Nova Lite accetta al massimo 10.000 token di risposta)
  e una funzione max_tokens(modello) che restituisce il tetto giusto
- SYSTEM_PROMPT con questo testo:
  "Sei un consulente senior di sostenibilità, esperto di CSRD, ESRS e GHG Protocol.
  Rispondi in italiano, in modo sintetico, con tabelle quando confronti dati.
  Usa il formato Markdown: le tabelle sempre in Markdown, mai in HTML.
  Quando ricevi dati numerici, prima di qualsiasi considerazione controlla la qualità dei dati
  (unità incoerenti, valori anomali rispetto agli altri mesi, dati mancanti) e segnala cosa trovi.
  Cita un fattore di emissione solo se la domanda lo richiede, sempre con valore e fonte.
  Se non sei certo di un'informazione o di un numero, dillo esplicitamente: meglio «non lo so» che un dato inventato."

engine.py:
- reply(message, history) restituisce (testo della risposta, (token di input, token di output)):
  input e output vanno tenuti separati perché costano diversamente
- IMPORTANTE: alcuni modelli del Generative Engine non accettano il ruolo "system".
  Il system prompt va inserito come primo scambio della conversazione:
    {"role": "user", "content": SYSTEM_PROMPT}
    {"role": "assistant", "content": "Ho capito. Come posso aiutarti?"}
  poi tutta la history, poi il nuovo messaggio dell'utente
- il contenuto della risposta di solito è una stringa, con alcuni modelli una lista di parti: gestisci entrambi
- se la risposta è vuota, restituisci un messaggio che spiega perché: se finish_reason è "length",
  il modello ha esaurito i token (indica MAX_TOKENS in config.py); altrimenti riporta il motivo

app.py:
- st.set_page_config(page_title=NOME, page_icon="🌱", layout="wide", initial_sidebar_state="expanded"), poi stile()
- un segnaposto st.empty() per l'intestazione, riempito con testata() dopo la sidebar
- FRASI, le frasi che si scrivono da sole nell'intestazione: "risponde su CSRD, ESRS e GHG Protocol.",
  "parla la nostra lingua.", "controlla i dati prima di commentarli.", "indica sempre fattori e fonti."
- in st.session_state: messages, tokens, tok_in, tok_out, costo, secondi (totali della sessione),
  ultima (misure dell'ultima richiesta) e misure (indice del messaggio -> misure di quella risposta)
- sidebar: il modello (fisso in questo step, si cambia in config.py) e un pulsante "Nuova conversazione"
  che svuota la chat ma lascia token, costo e tempo, che sono della sessione
- niente pulsanti con domande preimpostate: la domanda la scrive l'utente in st.chat_input
  ("Chiedi qualcosa al consulente di sostenibilità…"); a chat vuota mostra solo un invito, "Da dove partiamo?"
- a ogni domanda: fai partire il cronometro (testata con inizio), chiama reply con uno spinner, poi calcola
  il costo con PREZZI del modello (input × prezzo input + output × prezzo output, diviso un milione),
  somma tempo, token e costo ai totali della sessione e mostra misure() sotto la risposta
- se la chiamata fallisce, mostra l'errore nella chat invece di bloccare l'app

Regole: codice semplice, senza classi, commenti in italiano.
Per installare i pacchetti usa: uv add streamlit

Output: solo i file completi, pronti da eseguire con: uv run streamlit run app.py
