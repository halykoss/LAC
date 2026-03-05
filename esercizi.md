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

- **Statico**: `f` cattura `x=5` nell'ambiente di definizione → **5**
- **Dinamico**: `f` usa l'ambiente al momento della chiamata, dove `x=99` → **99**

```python
Interpreter(scoping='static').run(program)   # → 5
Interpreter(scoping='dynamic').run(program)  # → 99
```

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

- **Statico**: `g` cattura `a=1` alla definizione → `1 + 1 = 2`
- **Dinamico**: `g` vede `a=10` al momento della chiamata → `10 + 1 = 11`

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

**Scoping statico** — `f` vede sempre la `x` globale:
1. `f(1)`: `x = 10 + 1 = 11`, restituisce 11. La `x` globale è ora 11.
2. `g()` → `let x = 0 in f(5)`: `f` vede la `x` globale (11). `x = 11 + 5 = 16`, restituisce 16.
3. Totale: **11 + 16 = 27**

**Scoping dinamico** — `f` vede la `x` dell'ambiente di chiamata:
1. `f(1)`: chiamata dal contesto globale (`x=10`). `x = 10 + 1 = 11`, restituisce 11.
2. `g()` → `let x = 0 in f(5)`: `f` è chiamata con `x=0` nel contesto. `x = 0 + 5 = 5`, restituisce 5.
3. Totale: **11 + 5 = 16**

```python
f_body = Seq([Assign('x', BinOp('+', Var('x'), Var('n'))), Var('x')])
g_body = Let('x', Num(0), Call(FunName('f'), [Num(5)]))

program = Let('x', Num(10),
           Let('f', Fun(['n'], f_body),
            Let('g', Fun([], g_body),
             BinOp('+', Call(FunName('f'), [Num(1)]), Call(FunName('g'), [])))))
```

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

**Statico** → **1**

`f` cattura `x=1` al momento della sua definizione. Indipendentemente da chi la chiama e da quanti livelli di `let x = ...` ci sono sopra, `f` vedrà sempre `x=1`.

**Dinamico** → **2**

La catena di chiamata è `h() → g() → f()`. Al momento in cui `f` è eseguita, l'ambiente dinamico più vicino con `x` è quello di `g` (il `let x = 2`). Il `let x = 3` di `h` è più lontano nella catena.

```python
program = Let('x', Num(1),
           Let('f', Fun([], Var('x')),
            Let('g', Fun([], Let('x', Num(2), Call(FunName('f'), []))),
             Let('h', Fun([], Let('x', Num(3), Call(FunName('g'), []))),
              Call(FunName('h'), [])))))
```

```python
Interpreter(scoping='static').run(program)   # → 1
Interpreter(scoping='dynamic').run(program)  # → 2
```

</details>

---

## Categoria 2: Record di Attivazione e Display

> Usa i flag `--ar` e `--display` per visualizzare queste strutture durante l'esecuzione.
> Ricorda: i frame di `Let` non creano un nuovo AR — solo le **chiamate di funzione** lo fanno.

### Esercizio 2.1 — Leggere un AR (★☆☆☆)

Esegui il seguente programma con `--ar`:

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
║  static link  → [let x]  depth=0  {x=10}               ║
║  dynamic link → [let f]  depth=0  (chiamante)          ║
╚════════════════════════════════════════════════════════╝
```

1. **1 AR** — una sola chiamata
2. **`a = 5`** — il parametro formale
3. **Static link** → l'ambiente catturato dalla closure al momento della definizione di `f`, ovvero il frame `[let x]` che contiene `x=10`. **Non** punta a `[let f]`: la closure viene creata quando `Fun` viene valutato, cioè *dentro* il `Let x` ma *prima* che esista il frame `let f`.

**Static link ≠ dynamic link**: il dynamic link punta a `[let f]` (il frame da cui viene fatta la chiamata `f(5)`), mentre lo static link punta a `[let x]` (l'env catturato alla definizione).

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

Eseguilo con `--display`. Prevedi cosa conterrà il Display **al momento della chiamata di `f`**:

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
|   0   | Ambiente globale        | `{vuoto}`            |
|   1   | call frame `f (a)`      | `a=10`               |

> **Nota:** quando `f` viene chiamata, il suo AR **sostituisce** quello di `g` a depth 1 nel Display. L'Ambiente globale è vuoto perché `x`, `f`, `g` vivono nei rispettivi frame `let x`, `let f`, `let g` (non nel frame globale).
>
> Il frame `let y = 2` creato dentro `f` non compare nel Display — non è un call frame.

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

Eseguilo con `--ar` sia in modalità **statica** sia **dinamica**.

Confronta gli AR prodotti e rispondi:
1. Il **static link** di `f` cambia tra i due scoping? Perché?
2. Il **dynamic link** cambia? Perché?
3. Quale scoping produce il risultato 1? Quale produce 99?

<details>
<summary>Soluzione</summary>

Il **dynamic link** di `f` è lo stesso in entrambi gli scoping: punta al frame `[let x=99]` (il `Let` creato dentro il corpo di `g`, da cui `f` viene chiamata). **Non** punta all'AR di `g` stesso — un frame `Let` non è un AR.

Il **static link** cambia:
- **Scoping statico**: static link → `[let x]` (depth=0), l'env catturato dalla closure alla definizione. `f` vede `x=1` → **1**
- **Scoping dinamico**: static link **assente** — `f` usa la catena dinamica al momento della chiamata, che ha `x=99` in cima. `f` vede `x=99` → **99**

Cambia anche la **profondità lessicale** dell'AR di `f`:
- **Statico**: `lex_depth = 1` (parent statico = `[let x]` depth=0)
- **Dinamico**: `lex_depth = 2` (parent dinamico = `[let x=99]` depth=1, dentro l'AR di `g`)

| Campo        | Scoping statico                       | Scoping dinamico (shallow)              |
|--------------|---------------------------------------|-----------------------------------------|
| static link  | → `[let x]` depth=0 {x=1}            | **assente** (nessuna closure catturata) |
| dynamic link | → `[let x=99]` depth=1 (dentro `g`)  | → `[let x=99]` depth=1 (dentro `g`)    |
| lex_depth f  | **1**                                 | **2**                                   |
| risultato    | **1**                                 | **99**                                  |

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

Verifica le previsioni con `--display --ar`.

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
|   0   | Ambiente globale| `{vuoto}` ¹                  |
|   1   | call frame `f`  | `n=10`                       |

> ¹ `x`, `f`, `g`, `h` vivono nei frame `let x`, `let f`, `let g`, `let h` — non nel frame globale.
>
> Al momento della chiamata di `f`, il suo AR ha sostituito quelli di `h` e `g` a depth 1.

**4. Risultato:** `f(10)` = `10 + x` = `10 + 0` = **10**

```python
Interpreter(scoping='static', show_ar=True, show_display=True).run(program)
# → 10
```

</details>
