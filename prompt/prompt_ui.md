# Come è nata l'interfaccia (ui.py e .streamlit/config.toml)

L'interfaccia non è stata generata con un prompt solo: è stata costruita parlando con l'AI, una richiesta alla volta,
guardando il risultato a ogni passaggio. Il file di riferimento è ui.py, uguale in tutti i branch dallo step 1 in poi.
Qui sotto trovi (1) il prompt che descrive l'interfaccia finale, per rifarla da zero, e (2) le richieste
nell'ordine in cui sono state fatte. Il risultato grafico di un LLM può cambiare da una volta all'altra:
se vuoi esattamente questa interfaccia, usa ui.py del branch.

## 1. Il prompt che descrive l'interfaccia finale

Agisci come un web designer esperto di Streamlit. Crea ui.py, un modulo che contiene tutto l'aspetto grafico
del Sustainability Copilot, separato dalla logica di app.py, e il file .streamlit/config.toml.

Vincoli tecnici:
- Streamlit recente (il progetto usa la 1.66), niente librerie esterne: CSS e JavaScript puro, inseriti con
  st.html(..., unsafe_allow_javascript=True)
- il filtro di st.html scarta i tag <style> quando ci sono anche script e qualunque testo simile a un tag dentro
  uno script: inserisci il CSS dal JavaScript e scrivi i "<" delle stringhe come <
- st.html scarta i tag SVG: le icone e le linee decorative vanno come immagini data:image/svg+xml nel CSS
- React riscrive le classi degli elementi di Streamlit: per segnare lo stato usa attributi data-* su <html>
  o sui contenitori (per esempio data-esg-attivo mentre l'agente lavora), e un MutationObserver con throttle
- l'area principale si seleziona con .stMain

Cosa deve esporre ui.py:
- NOME = "Sustainability Copilot", AVATAR_UTENTE = ":material/person:", AVATAR_AGENTE = ":material/eco:",
  BUDGET_MENSILE = 4.0, FRASI (sovrascrivibili da ogni step)
- STILE letto da ESG_STILE nel .env: "carta" (predefinito), "aurora", "ardesia"
- stile(): inserisce CSS e JavaScript, da chiamare una volta dopo st.set_page_config
- testata(contenitore, modello, documenti, token, dollari, secondi, ultima, inizio=None, token_richiesta=0,
  costo_richiesta=0.0, tok_in=0, tok_out=0, frasi=None)
- misure(a) con a = {"secondi", "token", "costo", "modello"}
- importa PREZZI da config.py per mostrare il prezzo del modello scelto

Aspetto:
- leggibilità e accessibilità prima di tutto: sfondo bianco, testo scuro ad alto contrasto, caratteri grandi
  (Schibsted Grotesk, 17 px), pochi elementi; l'effetto wow in un punto solo
- intestazione bianca con il nome dell'agente, lo stato ("Pronto" o "L'agente sta lavorando") e una frase che
  si scrive da sola ("L'agente legge bilanci…"); in basso una linea delle emissioni che scorre e diventa ambra
  quando l'agente lavora; l'animazione d'ingresso parte solo la prima volta
- pannello "Tempi e costi" fisso a destra (290 px), richiudibile in una pillola con tempo e costo: tempo della
  richiesta (il cronometro scorre nel browser) e totale della sessione; costo della sessione sempre in dollari
  con 4 decimali sotto il dollaro e la virgola italiana, con il costo della richiesta in corso; barra del budget
  mensile di 4 $; token di input e di output; modello con i prezzi per milione di token; documenti letti
- numeri che salgono con un'animazione quando cambiano
- sotto ogni risposta una riga di misure: tempo, token, costo, modello
- bordo luminoso che gira attorno al pannello dell'agente mentre lavora
- pulsante tema chiaro o scuro (predefinito chiaro, scelta salvata nel browser con localStorage)
  e pulsante tutto schermo (si esce con Esc)
- chat con avatar Material, tabelle Markdown leggibili, invito iniziale "Da dove partiamo?"
- stile "ardesia": scuro, con un campo di particelle in ambra che diventano verdi e accelerano quando l'agente
  lavora; stile "aurora": come carta, con una luce pastello animata nell'intestazione

.streamlit/config.toml: tema base light, sfondo bianco, colore primario #2E7D47, barra laterale #F5F7F6,
toolbarMode "minimal", carattere Schibsted Grotesk e JetBrains Mono per il codice.

Output: ui.py e .streamlit/config.toml completi.

## 2. Le richieste, nell'ordine in cui sono state fatte

1. "Rendi l'interfaccia più accattivante: stile scuro con la possibilità di passare al chiaro, effetti e animazioni."
2. "Il nome dell'agente dev'essere generico sulla sostenibilità, non solo ESG."
3. "Togli i pulsanti con le domande preimpostate: la domanda la scrive l'utente."
4. "Rendi la barra laterale richiudibile."
5. "Aggiungi il tempo di ogni richiesta e della sessione, e il costo calcolato con il prezzo del modello scelto."
6. "Sposta le schede con le informazioni in un pannello a destra, richiudibile."
7. "Il costo sempre in dollari, con i token divisi in input e output, così si può rifare il conto a mano."
8. "Stessa interfaccia in tutti gli step, dal primo all'ultimo."
9. "Aggiungi il pulsante per il tutto schermo."
10. "Pulisci l'interfaccia a favore della lettura e dell'accessibilità: sfondo bianco e pochi fronzoli.
    Fammi due o tre prototipi e scelgo il migliore." (scelto: carta)

## 3. Per cambiarla

Incolla ui.py all'agente del Generative Engine e scrivi cosa vuoi, in italiano: "i colori del cliente", "il logo
in alto", oppure allega lo screenshot di un sito che ti piace e chiedi "fallo così". Chiedi sempre leggibilità,
contrasto e caratteri grandi. La logica non si tocca: cambia solo ui.py.
