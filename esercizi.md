# Esercizi

Ogni esercizio richiede di **prevedere** il risultato o **costruire** un programma AST.
Verifica sempre le tue previsioni eseguendo il codice.

Legenda difficoltà: ★☆☆☆ facile → ★★★★ difficile

---

## Categoria 1: Scoping

### Esercizio 1.1 — Previsione semplice (★☆☆☆)

Dato il programma:

```python
let x = 5;
f = fun() { x };
let x = 99;
f();
```

Che si traduce in:

```python
program = Let('x', Num(5),
           Let('f', Fun([], Var('x')),
            Let('x', Num(99),
             Call(FunName('f'), []))))
```

Qual è il risultato con scoping **statico**? E con scoping **dinamico**?
Motiva la risposta prima di eseguire il codice.

<details>
<summary>Soluzione</summary>

Il comportamento dipende sia dallo scoping che dal flag `let_scope`.

---

#### `let_scope=False` (imperativo, default)

`Let` scrive la variabile **nel frame corrente** senza creare un nuovo scope.
I tre `Let` annidati scrivono tutti nello stesso ambiente globale in sequenza:
`x=5`, poi `f=<closure>`, poi `x=99` **sovrascrive** `x=5`.

- **Statico**: la closure cattura il frame globale alla definizione. Al momento della chiamata quel frame ha già `x=99` → **99**
- **Dinamico**: `f` usa l'ambiente al momento della chiamata, dove `x=99` → **99**

Entrambi restituiscono **99**.

```python
Interpreter(scoping='static',  let_scope=False).run(program)  # → 99
Interpreter(scoping='dynamic', let_scope=False).run(program)  # → 99
```

---

#### `let_scope=True` (funzionale)

Ogni `Let` crea un **nuovo frame figlio**. Si forma la catena:

```
[global] → [let x=5] → [let f=<closure>] → [let x=99] → call
```

Il secondo `Let('x', 99)` **non sovrascrive** `x=5`; crea uno scope separato più interno.

- **Statico**: `f` è definita nel frame `[let f]`. La closure cattura `[let f]`, il cui parent è `[let x=5]`. La lookup di `x` risale: `[let f]` → `[let x=5]` (trovata!) → **5**
- **Dinamico**: `f` usa l'env al momento della chiamata. Il frame corrente è `[let x=99]` → `x=99` → **99**

```python
Interpreter(scoping='static',  let_scope=True).run(program)  # → 5
Interpreter(scoping='dynamic', let_scope=True).run(program)  # → 99
```

---

#### Tabella riassuntiva

| `let_scope` | statico | dinamico |
|-------------|---------|----------|
| `False`     | **99**  | **99**   |
| `True`      | **5**   | **99**   |

Con `let_scope=False` i due `Let x` condividono il frame globale, quindi anche la closure statica "vede" il valore aggiornato. Con `let_scope=True` i due scope sono distinti e lo scoping statico preserva il binding al momento della definizione di `f`.

</details>

---

### Esercizio 1.2 — Scrittura AST (★★☆☆)

Traduci il seguente pseudo-codice in AST e prevedi il risultato con entrambi gli scoping:

```
a = 1
g = fun() { a + 1 }
let a = 10 in g()
```

<details>
<summary>Soluzione</summary>

```python
program = Let('a', Num(1),
           Let('g', Fun([], BinOp('+', Var('a'), Num(1))),
            Let('a', Num(10),
             Call(FunName('g'), []))))
```

---

#### `let_scope=False` (imperativo, default)

I tre `Let` scrivono nello stesso frame globale: `a=1`, poi `g=<fun>`, poi `a=10` sovrascrive.

- **Statico**: `g` cattura il frame globale. Al momento della chiamata il globale ha `a=10` → `10+1` = **11**
- **Dinamico**: `g` usa l'env corrente dove `a=10` → `10+1` = **11**

```python
Interpreter(scoping='static',  let_scope=False).run(program)  # → 11
Interpreter(scoping='dynamic', let_scope=False).run(program)  # → 11
```

---

#### `let_scope=True` (funzionale)

Si forma la catena:

```
[global] → [let a=1] → [let g=<fun>] → [let a=10] → call
```

- **Statico**: `g` è definita nel frame `[let g]`, il cui parent è `[let a=1]`. La closure cattura `[let g]`. La lookup di `a` risale: `[let g]` → `[let a=1]` (trovata!) → `1+1` = **2**
- **Dinamico**: `g` usa l'env al momento della chiamata, che è `[let a=10]`. Lookup `a=10` → `10+1` = **11**

```python
Interpreter(scoping='static',  let_scope=True).run(program)  # → 2
Interpreter(scoping='dynamic', let_scope=True).run(program)  # → 11
```

---

#### Tabella riassuntiva

| `let_scope` | statico | dinamico |
|-------------|---------|----------|
| `False`     | **11**  | **11**   |
| `True`      | **2**   | **11**   |

Con `let_scope=True` e scoping statico la closure cattura l'ambiente al momento della propria definizione, dove `a` vale ancora 1. Il `let a = 10` esterno non può "retroattivamente" modificare ciò che la closure ha già catturato.

</details>

---

### Esercizio 1.3 — Funzione con effetti (★★★☆)

Considera il programma:

```
x = 10
f = fun(n) { x = x + n; x }
g = fun()  { let x = 0 in f(5) }
f(1) + g()
```

Prevedi il risultato con scoping **statico** e **dinamico**.

> **Attenzione:** `f(1)` viene valutato prima di `g()`. Tieni traccia del valore di `x` durante tutta l'esecuzione.

<details>
<summary>Soluzione</summary>

```python
f_body = Seq([Assign('x', BinOp('+', Var('x'), Var('n'))), Var('x')])
g_body = Let('x', Num(0), Call(FunName('f'), [Num(5)]))

program = Let('x', Num(10),
           Let('f', Fun(['n'], f_body),
            Let('g', Fun([], g_body),
             BinOp('+', Call(FunName('f'), [Num(1)]), Call(FunName('g'), [])))))
```

---

#### `let_scope=False` (imperativo, default)

**Scoping statico** — `f` vede sempre la `x` globale:
1. `f(1)`: `x = 10 + 1 = 11`, restituisce 11. La `x` globale è ora 11.
2. `g()` → `let x = 0 in f(5)`: con `let_scope=False`, `Let('x', 0)` scrive `x=0` nel call frame di `g` (non tocca il globale). `f` cattura il globale (x=11). `x = 11 + 5 = 16`, restituisce 16.
3. Totale: **11 + 16 = 27**

**Scoping dinamico** — `f` vede la `x` dell'ambiente di chiamata:
1. `f(1)`: chiamata dal contesto globale (`x=10`). `x = 10 + 1 = 11`, restituisce 11.
2. `g()` → `let x = 0 in f(5)`: `Let('x', 0)` scrive nel call frame di `g`. `f` è chiamata con quel frame come parent; la lookup di `x` trova `x=0`. `x = 0 + 5 = 5`, restituisce 5.
3. Totale: **11 + 5 = 16**

```python
Interpreter(scoping='static',  let_scope=False).run(program)  # → 27
Interpreter(scoping='dynamic', let_scope=False).run(program)  # → 16
```

---

#### `let_scope=True` (funzionale)

**Scoping statico**: `f` cattura lo scope `[let f]`, il cui parent è `[let x=10]`. La `x` globale è la stessa di prima. Il `Let('x', 0)` in `g_body` crea uno scope isolato che non interferisce. Il risultato è identico: **27**.

**Scoping dinamico**: con `let_scope=True` il `Let('x', 0)` in `g_body` crea un frame separato con `x=0`. Quando `f` viene chiamata da quel frame, la lookup risale e trova `x=0` prima di trovare la `x` globale. Il risultato è identico: **16**.

```python
Interpreter(scoping='static',  let_scope=True).run(program)  # → 27
Interpreter(scoping='dynamic', let_scope=True).run(program)  # → 16
```

---

#### Tabella riassuntiva

| `let_scope` | statico | dinamico |
|-------------|---------|----------|
| `False`     | **27**  | **16**   |
| `True`      | **27**  | **16**   |

In questo esercizio `let_scope` non cambia i risultati perché il comportamento chiave dipende da `Assign` (che aggiorna una variabile esistente nella catena), non da come `Let` crea i frame. Con scoping statico `f` punta sempre alla `x` globale; con scoping dinamico `f` punta sempre alla `x` del proprio chiamante.

</details>

---

### Esercizio 1.4 — Tre livelli di annidamento (★★★★)

Analizza questo programma:

```
x = 1
f = fun() { x }
g = fun() { let x = 2 in f() }
h = fun() { let x = 3 in g() }
h()
```

Prevedi il risultato con scoping **statico** e **dinamico**, e spiega passo per passo la catena di chiamate.

<details>
<summary>Soluzione</summary>

```python
program = Let('x', Num(1),
           Let('f', Fun([], Var('x')),
            Let('g', Fun([], Let('x', Num(2), Call(FunName('f'), []))),
             Let('h', Fun([], Let('x', Num(3), Call(FunName('g'), []))),
              Call(FunName('h'), [])))))
```

---

#### `let_scope=False` (imperativo, default)

**Scoping statico** → **1**

`f` cattura il frame globale (dove `x=1`). I `Let('x', ...)` dentro i body di `g` e `h` scrivono nei rispettivi call frame, non nel globale. La lookup di `x` in `f` risale direttamente al globale → **1**.

**Scoping dinamico** → **2**

La catena di chiamata è `h() → g() → f()`. Il `Let('x', 2)` nel body di `g` scrive `x=2` nel call frame di `g`. Quando `f` esegue, il suo parent dinamico è il call frame di `g`, dove trova `x=2`. Il `let x = 3` di `h` è più in alto nella catena e viene oscurato → **2**.

```python
Interpreter(scoping='static',  let_scope=False).run(program)  # → 1
Interpreter(scoping='dynamic', let_scope=False).run(program)  # → 2
```

---

#### `let_scope=True` (funzionale)

**Scoping statico** → **1**

Con `let_scope=True` i `Let('x', ...)` creano frame separati, ma ciò non cambia il risultato: `f` cattura alla definizione lo scope dove `x=1` è il primo antenato con una variabile `x`. Indipendentemente da chi chiama `f`, essa vedrà sempre `x=1` → **1**.

**Scoping dinamico** → **2**

Con `let_scope=True`, `Let('x', 2)` in `g_body` crea un frame `[let x=2]` figlio del call frame di `g`. Quando `f` viene chiamata da quel frame, la lookup risale e trova `x=2` prima di trovare `x=1` o `x=3` → **2**.

```python
Interpreter(scoping='static',  let_scope=True).run(program)  # → 1
Interpreter(scoping='dynamic', let_scope=True).run(program)  # → 2
```

---

#### Tabella riassuntiva

| `let_scope` | statico | dinamico |
|-------------|---------|----------|
| `False`     | **1**   | **2**    |
| `True`      | **1**   | **2**    |

In questo esercizio `let_scope` non cambia i risultati perché le variabili `x` introdotte sono già **dentro i body delle funzioni** (non a livello top-level). La struttura delle catene di scope differisce internamente, ma il binding di `x` che `f` raggiunge è lo stesso in entrambi i casi.

</details>

---

## Categoria 2: Record di Attivazione e Display

> Usa i flag `show_ar=True` e `show_display=True` per visualizzare queste strutture durante l'esecuzione.
> Ricorda: i frame di `Let` non creano un nuovo AR — solo le **chiamate di funzione** lo fanno.
>
> Gli esercizi di questa categoria assumono `let_scope=False` (il default), dove tutti i `Let` top-level scrivono nello stesso frame globale. Con `let_scope=True` verrebbero creati frame intermedi che altererebbero la struttura del Display e i link degli AR.

### Esercizio 2.1 — Leggere un AR (★☆☆☆)

Esegui il seguente programma con `show_ar=True`:

```python
program = Let('x', Num(10),
           Let('f', Fun(['a'], BinOp('+', Var('a'), Var('x'))),
            Call(FunName('f'), [Num(5)])))

Interpreter(scoping='static', passing='value', show_ar=True).run(program)
```

Senza eseguire il codice, rispondi:
1. Quanti AR vengono stampati?
2. Qual è la variabile locale nell'AR?
3. Verso quale ambiente punta lo **static link**?

<details>
<summary>Soluzione</summary>

Viene stampato **1** AR (una sola chiamata di funzione: `f(5)`).

```
╔═ Record di Attivazione ════════════════════════════════╗
║  call frame (a)   [profondità lessicale: 1]            ║
╠════════════════════════════════════════════════════════╣
║  variabili locali:                                     ║
║    a = 5                                               ║
╠════════════════════════════════════════════════════════╣
║  static link  → [Ambiente globale]  depth=0  {x=10, f=<fun(a)>}  ║
║  dynamic link → [Ambiente globale]  depth=0  (chiamante)          ║
╚════════════════════════════════════════════════════════╝
```

1. **1 AR** — una sola chiamata
2. **`a = 5`** — il parametro formale
3. **Static link** → il frame globale, catturato dalla closure alla definizione di `f`. Con `let_scope=False`, tutti i `Let` scrivono nello stesso frame globale, quindi `x` e `f` convivono nell'Ambiente globale.

**Static link = dynamic link** in questo caso: entrambi puntano all'Ambiente globale, perché anche la chiamata `f(5)` avviene dall'Ambiente globale (nessun frame `[let f]` separato).

</details>

---

### Esercizio 2.2 — Prevedere il Display (★★☆☆)

Considera il programma:

```python
program = Let('x', Num(1),
           Let('f', Fun(['a'],
                   Let('y', Num(2),
                       BinOp('+', Var('a'), Var('y')))),
            Let('g', Fun([],
                    Call(FunName('f'), [Num(10)])),
             Call(FunName('g'), []))))
```

Eseguilo con `show_display=True`. Prevedi cosa conterrà il Display **al momento della chiamata di `f`**:

| depth | AR corrente | contenuto |
|-------|-------------|-----------|
|   0   |      ?      |     ?     |
|   1   |      ?      |     ?     |

<details>
<summary>Soluzione</summary>

La catena di chiamate è: `g()` → `f(10)`.

Con scoping **statico**, la `lex_depth` di un call frame dipende dall'ambiente catturato dalla closure (il parent statico), non dalla profondità dinamica della chiamata:

- `g`'s closure cattura l'env `[let f]` (depth 0) → g ha `lex_depth = 1`
- `f`'s closure cattura l'env `[let x]` (depth 0) → f ha `lex_depth = 1`

Entrambe le funzioni hanno `lex_depth = 1`, quindi **condividono la stessa cella del Display**. Al momento della chiamata di `f`, il Display mostra:

| depth | AR corrente             | contenuto principale |
|-------|-------------------------|----------------------|
|   0   | Ambiente globale        | `{x=1, f=<fun>, g=<fun>}` |
|   1   | call frame `f (a)`      | `a=10`               |

> **Nota:** quando `f` viene chiamata, il suo AR **sostituisce** quello di `g` a depth 1 nel Display. L'Ambiente globale contiene tutte le variabili dichiarate al top-level (`x`, `f`, `g`) perché con `let_scope=False` ogni `Let` scrive nello stesso frame.
>
> Il `Let('y', 2, ...)` dentro `f` aggiunge `y` direttamente al call frame di `f` (non crea un frame separato). Al momento della chiamata, prima che il body esegua, `y` non è ancora presente.

</details>

---

### Esercizio 2.3 — Static link vs Dynamic link (★★★☆)

Dato il programma:

```python
program = Let('x', Num(1),
           Let('f', Fun([], Var('x')),
            Let('g', Fun([],
                    Let('x', Num(99),
                        Call(FunName('f'), []))),
             Call(FunName('g'), []))))
```

Eseguilo con `show_ar=True` sia in modalità **statica** sia **dinamica**.

Confronta gli AR prodotti e rispondi:
1. Il **static link** di `f` cambia tra i due scoping? Perché?
2. Il **dynamic link** cambia? Perché?
3. Quale scoping produce il risultato 1? Quale produce 99?

<details>
<summary>Soluzione</summary>

Il **dynamic link** di `f` è lo stesso in entrambi gli scoping: punta al call frame di `g`. Con `let_scope=False`, `Let('x', 99)` scrive `x=99` direttamente nel call frame di `g` (non crea un frame separato), quindi il dynamic link di `f` punta al call frame di `g` che contiene `x=99`.

Il **static link** cambia:
- **Scoping statico**: static link → `[Ambiente globale]` (depth=0), catturato alla definizione. Il globale ha `x=1` → **1**
- **Scoping dinamico**: static link **assente** — `f` risale la catena dinamica, trova `x=99` nel call frame di `g` → **99**

Cambia anche la **profondità lessicale** dell'AR di `f`:
- **Statico**: `lex_depth = 1` (parent statico = Ambiente globale, depth=0)
- **Dinamico**: `lex_depth = 2` (parent dinamico = call frame di `g`, depth=1)

| Campo        | Scoping statico                              | Scoping dinamico (shallow)              |
|--------------|----------------------------------------------|-----------------------------------------|
| static link  | → `[Ambiente globale]` depth=0 {x=1, f, g}  | **assente** (nessuna closure catturata) |
| dynamic link | → `[call frame (∅)]` depth=1, g {x=99}      | → `[call frame (∅)]` depth=1, g {x=99} |
| lex_depth f  | **1**                                        | **2**                                   |
| risultato    | **1**                                        | **99**                                  |

</details>

---

### Esercizio 2.4 — Display con tre livelli (★★★★)

Analizza il seguente programma:

```python
program = Let('x', Num(0),
           Let('f', Fun(['n'],
                   BinOp('+', Var('n'), Var('x'))),
            Let('g', Fun(['m'],
                    Call(FunName('f'), [BinOp('*', Var('m'), Num(2))])),
             Let('h', Fun([],
                     Call(FunName('g'), [Num(5)])),
              Call(FunName('h'), [])))))
```

Senza eseguire il codice:
1. Quante chiamate di funzione avvengono in totale?
2. Qual è la profondità massima nel Display?
3. Disegna il Display al momento della chiamata a `f`.
4. Qual è il risultato finale?

Verifica le previsioni con `show_display=True, show_ar=True`.

<details>
<summary>Soluzione</summary>

**1. Chiamate di funzione:** 3 — `h()`, poi `g(5)`, poi `f(10)`

**2. Profondità massima:** **1**

Con scoping statico, la `lex_depth` dipende dall'env catturato dalla closure:
- `h`'s closure cattura `[let g]` (depth 0) → `lex_depth = 1`
- `g`'s closure cattura `[let f]` (depth 0) → `lex_depth = 1`
- `f`'s closure cattura `[let x]` (depth 0) → `lex_depth = 1`

Tutte e tre le funzioni hanno `lex_depth = 1`: ogni chiamata **sostituisce** la precedente nel Display.

**3. Display al momento della chiamata di `f`:**

| depth | AR              | contenuto                    |
|-------|-----------------|------------------------------|
|   0   | Ambiente globale| `{x=0, f=<fun>, g=<fun>, h=<fun>}` |
|   1   | call frame `f`  | `n=10`                       |

> Con `let_scope=False`, tutte le dichiarazioni top-level (`x`, `f`, `g`, `h`) finiscono nell'Ambiente globale.
>
> Al momento della chiamata di `f`, il suo AR ha sostituito quelli di `h` e `g` a depth 1.

**4. Risultato:** `f(10)` = `10 + x` = `10 + 0` = **10**

```python
Interpreter(scoping='static', show_ar=True, show_display=True).run(program)
# → 10
```

</details>
