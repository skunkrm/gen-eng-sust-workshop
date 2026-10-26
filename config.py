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
    timeout=120,
    max_retries=0,  # nessun nuovo tentativo automatico: se il modello non risponde lo vediamo subito
)

# Il modello è il "motore": per cambiarlo basta cambiare questa riga
MODEL = "anthropic.claude-haiku-5-5"

# Prezzi in dollari per milione di token (input, output): servono per mostrare il costo della sessione
PREZZI = {
    "anthropic.claude-haiku-5-5": (0.11, 0.55),
    "anthropic.claude-sonnet-5-5": (2.20, 11.0),
    "amazon.nova-lite-v1:0": (0.0824, 0.3193),
}

# Tetto ai token di risposta: i modelli più recenti "ragionano" prima di rispondere e quel ragionamento
# consuma token, quindi con un tetto basso la risposta può arrivare vuota
MAX_TOKENS = 16000

# Alcuni modelli hanno un tetto più basso: Nova Lite accetta al massimo 10.000 token di risposta
LIMITI_TOKEN = {"amazon.nova-lite-v1:0": 8000}


def max_tokens(modello):
    """Il tetto di token di risposta per il modello scelto."""
    return LIMITI_TOKEN.get(modello, MAX_TOKENS)

# Il system prompt: il nostro mestiere, scritto in italiano
SYSTEM_PROMPT = """Sei un consulente senior di sostenibilità, esperto di CSRD, ESRS e GHG Protocol.
Rispondi in italiano, in modo sintetico, con tabelle quando confronti dati.
Usa il formato Markdown: le tabelle sempre in Markdown, mai in HTML.
Quando ricevi dati numerici, prima di qualsiasi considerazione controlla la qualità dei dati
(unità incoerenti, valori anomali rispetto agli altri mesi, dati mancanti) e segnala cosa trovi.
Cita un fattore di emissione solo se la domanda lo richiede, sempre con valore e fonte.
Se non sei certo di un'informazione o di un numero, dillo esplicitamente: meglio «non lo so» che un dato inventato."""
