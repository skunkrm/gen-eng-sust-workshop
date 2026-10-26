"""Il ciclo agentico: il modello ragiona, chiama gli strumenti, legge i risultati e prosegue.

reply() è un generatore: restituisce eventi man mano che succedono, così l'interfaccia
può mostrare all'utente cosa sta facendo l'agente. Tipi di evento:
  ("step", testo)   avanzamento del ciclo
  ("calc", dati)    risultato del calcolo delle emissioni
  ("chart", dati)   grafico creato
  ("file", dati)    file creato, da scaricare
  ("check", dati)   verifica delle fonti non superata
  ("tokens", n)     token usati da una chiamata
  ("done", testo)   risposta finale
"""

import base64
import json

from openai import BadRequestError, PermissionDeniedError

from config import MAX_ITERATIONS, MAX_TOKENS, MODEL, SYSTEM_PROMPT, client
from tools import TOOLS, execute_tool


def _contenuto_utente(message, images):
    """Testo dell'utente più eventuali foto, nel formato OpenAI per le immagini."""
    if not images:
        return message
    parti = [{"type": "text", "text": message}]
    for img in images:
        b64 = base64.b64encode(img["data"]).decode()
        parti.append({"type": "image_url", "image_url": {"url": f"data:{img['mime']};base64,{b64}"}})
    return parti


def build_messages(message, history, knowledge_base="", images=None):
    """Alcuni modelli del Generative Engine non accettano il ruolo "system":
    le istruzioni (e i documenti) vanno come primo scambio utente/assistente."""
    istruzioni = SYSTEM_PROMPT
    if knowledge_base:
        istruzioni += (
            "\n\nL'utente ha caricato questi documenti. Usali per rispondere e cita il documento "
            "da cui prendi ogni informazione.\n\n" + knowledge_base
        )
    return [
        {"role": "user", "content": istruzioni},
        {"role": "assistant", "content": "Ho capito. Come posso aiutarti?"},
        *history,
        {"role": "user", "content": _contenuto_utente(message, images)},
    ]


def reply(message, history, knowledge_base="", model=MODEL, images=None, stato=None):
    stato = {} if stato is None else stato
    stato["documenti"] = knowledge_base  # serve alla verifica delle fonti
    messages = build_messages(message, history, knowledge_base, images)

    try:
        for giro in range(1, MAX_ITERATIONS + 1):
            yield ("step", f"Giro {giro}: il modello sta ragionando…")
            risposta = client.chat.completions.create(
                model=model, messages=messages, tools=TOOLS, max_tokens=MAX_TOKENS,
            )
            if risposta.usage:
                yield ("tokens", risposta.usage.total_tokens)
            scelta = risposta.choices[0]
            msg = scelta.message

            if not msg.tool_calls:
                if scelta.finish_reason == "length":
                    yield ("step", "⚠️ Risposta troncata: aumenta MAX_TOKENS in config.py")
                yield ("step", f"Giro {giro}: nessuno strumento da usare, risposta pronta.")
                yield ("done", msg.content or "")
                return

            # Il modello vuole usare uno o più strumenti: li eseguiamo tutti
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                nome = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = None
                if args is None:
                    risultato, evento = "Argomenti non validi (JSON non leggibile): riprova.", None
                else:
                    yield ("step", f"Giro {giro}: uso lo strumento **{nome}**")
                    risultato, evento = execute_tool(nome, args, stato)
                if evento:
                    yield evento
                # Il risultato torna al modello con ruolo "tool", collegato alla sua chiamata
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": risultato})

        yield ("step", f"Raggiunto il limite di {MAX_ITERATIONS} giri: mi fermo.")
        yield ("done", "Ho raggiunto il numero massimo di passaggi. Prova a dividere la richiesta in parti più piccole.")

    except (BadRequestError, PermissionDeniedError) as errore:
        # Il modello scelto non supporta gli strumenti (o le immagini): rispondiamo solo con testo
        yield ("step", f"⚠️ Il modello ha rifiutato la richiesta: {errore}")
        yield ("step", "Riprovo senza strumenti e senza immagini…")
        semplici = build_messages(message, history, knowledge_base)
        risposta = client.chat.completions.create(model=model, messages=semplici, max_tokens=MAX_TOKENS)
        if risposta.usage:
            yield ("tokens", risposta.usage.total_tokens)
        yield ("done", (risposta.choices[0].message.content or "")
               + "\n\n---\n⚠️ *Questo modello non supporta gli strumenti: calcoli, grafici e file non sono disponibili.*")
