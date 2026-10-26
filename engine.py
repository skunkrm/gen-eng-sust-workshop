"""La logica della chat: manda la conversazione al modello e restituisce la risposta."""

from config import MAX_TOKENS, MODEL, max_tokens, SYSTEM_PROMPT, client


def build_messages(message, history):
    """Prepara i messaggi da mandare al modello.

    Alcuni modelli del Generative Engine non accettano il ruolo "system",
    quindi le istruzioni vanno come primo scambio utente/assistente.
    """
    return [
        {"role": "user", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Ho capito. Come posso aiutarti?"},
        *history,
        {"role": "user", "content": message},
    ]



def _testo(contenuto):
    """Il testo della risposta: di solito una stringa, con alcuni modelli una lista di parti."""
    if isinstance(contenuto, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(getattr(p, "text", "")) for p in contenuto)
    return contenuto or ""


def reply(message, history):
    """Restituisce (testo della risposta, (token di input, token di output))."""
    risposta = client.chat.completions.create(
        model=MODEL,
        messages=build_messages(message, history),
        max_tokens=max_tokens(MODEL),
    )
    scelta = risposta.choices[0]
    testo = _testo(scelta.message.content)
    if not testo.strip():  # niente testo: diciamo perché, invece di mostrare un riquadro vuoto
        if scelta.finish_reason == "length":
            testo = ("⚠️ Il modello ha esaurito i token a disposizione prima di scrivere la risposta "
                     f"(MAX_TOKENS = {MAX_TOKENS} in config.py). Riprova, o alza il valore.")
        else:
            testo = f"⚠️ Il modello non ha restituito testo (motivo: {scelta.finish_reason}). Riprova."
    uso = risposta.usage
    token = (uso.prompt_tokens, uso.completion_tokens) if uso else (0, 0)  # input e output: costano diversamente
    return testo, token
