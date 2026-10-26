Trasforma questo progetto in un chatbot web con Streamlit: un consulente ESG.

Ecco il main.py dello step precedente:

[incolla qui il contenuto di main.py]

Struttura da generare: config.py, engine.py, app.py

config.py:
- legge GEN_ENGINE_API_KEY e GEN_ENGINE_BASE_URL dal file .env; se la chiave manca, termina con un messaggio chiaro
- crea il client OpenAI come variabile di modulo
- MODEL = "amazon.nova-lite-v1:0" e MAX_TOKENS = 4096
- SYSTEM_PROMPT con questo testo:
  "Sei un consulente senior di sostenibilità, esperto di CSRD, ESRS e GHG Protocol.
  Rispondi in italiano, in modo sintetico, con tabelle quando confronti dati.
  Quando ricevi dati numerici, prima di qualsiasi considerazione controlla la qualità dei dati
  (unità incoerenti, valori anomali rispetto agli altri mesi, dati mancanti) e segnala cosa trovi.
  Cita un fattore di emissione solo se la domanda lo richiede, sempre con valore e fonte.
  Se non sei certo di un'informazione o di un numero, dillo esplicitamente: meglio «non lo so» che un dato inventato."

engine.py:
- funzione reply(message, history) che restituisce (testo della risposta, token totali usati)
- IMPORTANTE: alcuni modelli del Generative Engine non accettano il ruolo "system".
  Il system prompt va inserito come primo scambio della conversazione:
    {"role": "user", "content": SYSTEM_PROMPT}
    {"role": "assistant", "content": "Ho capito. Come posso aiutarti?"}
  poi tutta la history, poi il nuovo messaggio dell'utente

app.py:
- titolo "🌱 ESG Copilot" e sottotitolo "Il tuo consulente CSRD ed ESRS, costruito sul Generative Engine"
- cronologia della chat in st.session_state.messages, mostrata in markdown
- st.chat_input per le domande, con uno spinner mentre il modello risponde
- sidebar con il nome del modello, un contatore dei token usati nella sessione e un pulsante "Nuova conversazione"
- se la chiamata fallisce, mostra l'errore nella chat invece di bloccare l'app

Regole: codice semplice, senza classi, commenti in italiano.
Per installare i pacchetti usa: uv add streamlit

Output: solo i file completi, pronti da eseguire con: uv run streamlit run app.py
