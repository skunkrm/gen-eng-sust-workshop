Crea un semplice script Python, main.py, che si colleghi al Generative Engine di Capgemini.

Requisiti:
- il Generative Engine è compatibile con le API OpenAI: usa la libreria openai con
  base_url letto da GEN_ENGINE_BASE_URL (default "https://openai.generative.engine.capgemini.com/v1")
- la API key si legge da GEN_ENGINE_API_KEY nel file .env, con python-dotenv
- se la chiave manca, termina con un messaggio chiaro in italiano
- usa il modello amazon.nova-lite-v1:0
- manda al modello la domanda "Spiegami in due frasi cos'è la doppia materialità nella CSRD."
- stampa la risposta e i token usati in ingresso e in uscita
- gestisci gli errori di connessione e gli errori HTTP con messaggi in italiano
- codice minimale e commentato in italiano

Per installare i pacchetti usa: uv add openai python-dotenv

Output: solo il file completo, pronto da eseguire con: uv run main.py
