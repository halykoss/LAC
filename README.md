# Interprete Didattico LAC

Strumento per esplorare interattivamente i concetti fondamentali dei linguaggi di programmazione:

- **Scoping** — statico (lessicale) vs dinamico
- **Passaggio dei parametri** — per valore, per riferimento, per nome
- **Binding** — shallow vs deep (solo con scoping dinamico)

I programmi non vengono scritti come testo: si costruiscono direttamente come **alberi sintattici (AST)** usando oggetti Python. L'obiettivo è concentrarsi sulla semantica, non sulla sintassi.

---

## Requisiti

- **Python 3.8 o superiore** (nessuna libreria esterna richiesta)

Per verificare la versione installata:

```bash
python --version
```

---

## Struttura del progetto

```
lac/
├── interprete.py   # Core: nodi AST, valori runtime, ambiente, interprete
├── esempi.py       # Esempi pronti all'uso (eseguibili da riga di comando)
├── esercizi.md     # Esercizi guidati con soluzioni
└── README.md
```

---

## Come eseguire gli esempi

Dalla cartella `lac/`, eseguire:

```bash
# Mostra il catalogo e lancia tutti gli esempi in sequenza
python esempi.py

# Mostra solo il catalogo degli esempi disponibili
python esempi.py list

# Lancia un singolo esempio
python esempi.py classic_scoping

# Flag opzionali (combinabili tra loro)
python esempi.py classic_scoping --debug    # catena degli ambienti passo-passo
python esempi.py classic_scoping --ar       # Record di Attivazione ad ogni chiamata
python esempi.py classic_scoping --display  # Display (depth → AR corrente) ad ogni chiamata

# Esempio con tutti i flag attivi
python esempi.py classic_scoping --debug --ar --display
```

---

## Percorso consigliato

Gli esempi sono ordinati per difficoltà crescente.

| #  | Comando                                        | Argomento                                                          |
|----|------------------------------------------------|--------------------------------------------------------------------|
| 1  | `python esempi.py classic_scoping`             | Differenza base tra scoping statico e dinamico                     |
| 2  | `python esempi.py simple_passing`              | Per valore vs riferimento vs nome su `double(x)`                   |
| 3  | `python esempi.py swap_passing`                | Lo swap funziona solo per riferimento                              |
| 4  | `python esempi.py nested_scoping`              | Funzioni annidate: quale `x` vede `f` quando è chiamata da `g`?   |
| 5  | `python esempi.py name_passing_effects`        | Effetto collaterale con passaggio per nome (Jensen's device)       |
| 6  | `python esempi.py name_passing_multiple_evals` | Con passaggio per nome l'argomento viene valutato più volte        |
| 7  | `python esempi.py shallow_vs_deep_binding`     | Shallow vs deep binding con scoping dinamico                       |
| 8  | `python esempi.py binding_nested`              | Binding annidato: tre valori di `x` diversi a seconda del binding  |
| 9  | `python esempi.py debug_example`               | Come leggere l'output di debug                                     |
| 10 | `python esempi.py full_comparison`             | Tutte le combinazioni scoping × passaggio a confronto              |

---

## Come usare l'interprete dal codice

È possibile costruire programmi direttamente in Python e valutarli:

```python
from interprete import Interpreter, Num, Var, BinOp, Let, Fun, Call

# Programma: let x = 10 in x + 5
program = Let('x', Num(10),
              BinOp('+', Var('x'), Num(5)))

interp = Interpreter(scoping='static', passing='value', debug=True)
interp.run(program)
```

### Nodi AST disponibili

| Nodo                   | Significato                           | Esempio                                      |
|------------------------|---------------------------------------|----------------------------------------------|
| `Num(n)`               | Numero letterale                      | `Num(42)`                                    |
| `Var('x')`             | Variabile                             | `Var('x')`                                   |
| `BinOp(op, l, r)`      | Operazione binaria (`+` `-` `*` `/`)  | `BinOp('+', Var('x'), Num(1))`               |
| `Let('x', val, body)`  | Binding locale                        | `Let('x', Num(5), Var('x'))`                 |
| `Fun(params, body)`    | Funzione anonima                      | `Fun(['x'], BinOp('*', Var('x'), Num(2)))`   |
| `Call(f, args)`        | Chiamata di funzione                  | `Call(Var('f'), [Num(3)])`                   |
| `Assign('x', val)`     | Assegnamento a variabile esistente    | `Assign('x', Num(0))`                        |
| `Seq([e1, e2, ...])`   | Sequenza (restituisce l'ultima)       | `Seq([Assign('x', Num(1)), Var('x')])`       |
| `If(cond, then_, else_)` | Condizionale                        | `If(Var('x'), Num(1), Num(0))`               |

### Parametri dell'interprete

```python
Interpreter(
    scoping      = 'static'   # oppure 'dynamic'
    passing      = 'value'    # oppure 'reference' oppure 'name'
    binding      = 'shallow'  # oppure 'deep' (rilevante solo con scoping='dynamic')
    let_scope    = False      # False: Let imperativo (dichiara nel frame corrente, default)
                              # True:  Let funzionale (crea un nuovo scope figlio)
    debug        = False      # True: catena degli ambienti passo-passo
    show_ar      = False      # True: Record di Attivazione ad ogni chiamata
    show_display = False      # True: Display (depth → AR) ad ogni chiamata
)
```

---

## Opzioni di visualizzazione

I tre flag `--debug`, `--ar`, `--display` sono indipendenti e combinabili.

| Flag        | Cosa mostra                                                              |
|-------------|--------------------------------------------------------------------------|
| `--debug`   | Catena degli ambienti, lookup variabili e valori restituiti              |
| `--ar`      | Record di Attivazione: parametri, static link, dynamic link              |
| `--display` | Display: tabella `depth → AR corrente`, aggiornata ad ogni chiamata      |

```bash
python esempi.py debug_example --debug
python esempi.py classic_scoping --ar
python esempi.py binding_nested --display
python esempi.py swap_passing --ar --display
```

---

## Note importanti

- `Let` con `let_scope=False` (default) dichiara la variabile nel **frame corrente**, come nei linguaggi imperativi. Ridichiarare lo stesso nome sovrascrive il binding esistente.
- `Let` con `let_scope=True` crea un **nuovo scope figlio**, visibile solo nel `body`. È il comportamento funzionale classico (Haskell, ML, LISP).
- `Assign` **aggiorna** una variabile già esistente risalendo la catena degli scope (usarlo per gli effetti collaterali).
- Con passaggio **per riferimento**, l'argomento deve essere una variabile (`Var('x')`), non un'espressione.
- Con passaggio **per nome**, l'espressione argomento viene rivalutata ogni volta che il parametro viene letto.
