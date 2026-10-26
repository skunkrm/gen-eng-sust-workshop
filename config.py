"""Configurazione: chiave, endpoint, modello e istruzioni del consulente."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

if not os.getenv("GEN_ENGINE_API_KEY"):
    raise SystemExit("Manca la chiave: copia .env.example in .env e inserisci GEN_ENGINE_API_KEY.")

client = OpenAI(
    base_url=os.getenv("GEN_ENGINE_BASE_URL", "https://openai.generative.engine.capgemini.com/v1"),
    api_key=os.getenv("GEN_ENGINE_API_KEY"),
    timeout=180,
)

# Modelli a confronto: il primo è quello di partenza
MODELS = {
    "amazon.nova-lite-v1:0": "Economico, meno preciso",
    "anthropic.claude-sonnet-5-5": "Più costoso, più preciso",
}
MODEL = "amazon.nova-lite-v1:0"

# Prezzi in dollari per milione di token (input, output): servono per mostrare il costo della sessione
PREZZI = {
    "anthropic.claude-haiku-5-5": (0.11, 0.55),
    "anthropic.claude-sonnet-5-5": (2.20, 11.0),
    "amazon.nova-lite-v1:0": (0.0824, 0.3193),
}

# Tetto ai token di risposta: i modelli più recenti "ragionano" prima di rispondere e quel ragionamento
# consuma token, quindi con un tetto basso la risposta può arrivare vuota
MAX_TOKENS = 16000

# Il system prompt: il nostro mestiere, scritto in italiano
SYSTEM_PROMPT = """Sei un consulente senior di sostenibilità, esperto di CSRD, ESRS e GHG Protocol.
Rispondi in italiano, in modo sintetico, con tabelle quando confronti dati.
Usa il formato Markdown: le tabelle sempre in Markdown, mai in HTML.
Quando ricevi dati numerici, prima di qualsiasi considerazione controlla la qualità dei dati
(unità incoerenti, valori anomali rispetto agli altri mesi, dati mancanti) e segnala cosa trovi.
Indica sempre fattori di emissione e fonti quando li usi.
Se un'informazione non è nei documenti o non la conosci, dillo esplicitamente."""
