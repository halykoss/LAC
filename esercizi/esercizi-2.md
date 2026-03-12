# Esercizi avanzati — Scoping e Passaggio Parametri

Ogni esercizio richiede di **prevedere** il risultato o **costruire** un programma AST.
Verifica sempre le tue previsioni eseguendo il codice.

Legenda difficoltà: ★☆☆☆ facile → ★★★★ difficile

> Tutti gli esercizi usano `let_scope=False` (default imperativo): i `Let` consecutivi
> scrivono nello stesso frame corrente invece di creare scope annidati.

---

## Categoria 1: Scoping avanzato

### Esercizio 1.1 — Funzione annidata con x locale (★★★☆)

```
x = 1
func inner(n) { x + n }
func outer(m) { x = 10; inner(m) }
outer(5)
```

`outer` introduce una `x` locale pari a 10 e poi chiama `inner`.

Prevedi il risultato con scoping **statico** e **dinamico**.

> **Suggerimento:** con scoping statico, `inner` vede la `x` del contesto in cui è **definita**. Con scoping dinamico, vede la `x` del contesto da cui viene **chiamata**.

<details>
<summary>Soluzione</summary>

- **Statico** → **6**: `inner` è una closure che cattura il frame globale (`x=1`). Il `x=10` introdotto dentro `outer` è locale al frame di `outer`. La lookup di `x` in `inner` risale al globale → `1+5=6`.
- **Dinamico** → **15**: `inner` è chiamata dall'interno di `outer`, dove l'ambiente corrente ha `x=10`. La lookup trova `x=10` → `10+5=15`.

```python
program = Let('x', Num(1),
           Let('inner', Fun(['n'], BinOp('+', Var('x'), Var('n'))),
            Let('outer', Fun(['m'],
                    Let('x', Num(10),
                        Call(FunName('inner'), [Var('m')]))),
             Call(FunName('outer'), [Num(5)]))))

Interpreter(scoping='static').run(program)   # → 6
Interpreter(scoping='dynamic').run(program)  # → 15
```

| Scoping  | x visto da inner       | Risultato |
|----------|------------------------|:---------:|
| statico  | `x=1` (globale)        | 6         |
| dinamico | `x=10` (frame di outer)| 15        |

</details>

---

### Esercizio 1.2 — Catena di tre funzioni annidate (★★★☆)

```
x = 1
func f()  { x * 2 }
func g()  { x = 5; f() }
func h()  { x = 10; g() }
h()
```

La catena di chiamate è `h() → g() → f()`. Ogni funzione introduce una `x` locale diversa.

Prevedi il risultato con scoping **statico** e **dinamico**.

> **Suggerimento:** con scoping statico, `f` ignora le `x` locali di `g` e `h`. Con scoping dinamico, quale `x` vede `f`?

<details>
<summary>Soluzione</summary>

- **Statico** → **2**: `f` cattura il frame globale (`x=1`). Le `x` locali introdotte da `g` (`x=5`) e `h` (`x=10`) non interferiscono. `f` restituisce sempre `1*2=2`.
- **Dinamico** → **10**: `f` è chiamata da `g`, che è chiamata da `h`. L'ambiente dinamico al momento della chiamata di `f` è il frame di `g` (dove `x=5`). `f` restituisce `5*2=10`.

```python
program = Let('x', Num(1),
           Let('f', Fun([], BinOp('*', Var('x'), Num(2))),
            Let('g', Fun([], Let('x', Num(5), Call(FunName('f'), []))),
             Let('h', Fun([], Let('x', Num(10), Call(FunName('g'), []))),
              Call(FunName('h'), [])))))

Interpreter(scoping='static').run(program)   # → 2
Interpreter(scoping='dynamic').run(program)  # → 10
```

| Scoping  | x visto da f           | Risultato |
|----------|------------------------|:---------:|
| statico  | `x=1` (globale)        | 2         |
| dinamico | `x=5` (frame di g)     | 10        |

**Nota:** con scoping dinamico la `x=10` di `h` è oscurata dalla `x=5` di `g`, che è più vicina nella catena di chiamata.

</details>

---

### Esercizio 1.3 — Funzione chiamata due volte da un contesto con x locale (★★★☆)

```
x = 10
func f() { x }
func g() { x = 0; f() + f() }
g()
```

`g` introduce una `x` locale pari a 0 e poi chiama `f` due volte.

Prevedi il risultato con scoping **statico** e **dinamico**. Le due chiamate a `f()` restituiscono lo stesso valore?

<details>
<summary>Soluzione</summary>

- **Statico** → **20**: `f` è una closure che cattura il frame globale dove `x=10`. Il `Let('x', 0, ...)` dentro `g` scrive `x=0` nel frame di `g`, non nel globale. Entrambe le chiamate a `f()` risalgono al globale e trovano `x=10` → `10+10=20`.
- **Dinamico** → **0**: `f` è una `DynFunction`. Chiamata dall'interno del body di `g`, l'ambiente dinamico ha `x=0` nel frame corrente di `g`. Entrambe le chiamate restituiscono 0 → `0+0=0`.

```python
g_body = Let('x', Num(0),
             BinOp('+', Call(FunName('f'), []), Call(FunName('f'), [])))

program = Let('x', Num(10),
           Let('f', Fun([], Var('x')),
            Let('g', Fun([], g_body),
             Call(FunName('g'), []))))

Interpreter(scoping='static').run(program)   # → 20
Interpreter(scoping='dynamic').run(program)  # → 0
```

| Scoping  | x visto da f        | f()+f() | Risultato |
|----------|---------------------|:-------:|:---------:|
| statico  | `x=10` (globale)    | 10+10   | 20        |
| dinamico | `x=0` (frame di g)  | 0+0     | 0         |

</details>

---

### Esercizio 1.4 — Effetto del contesto locale su f() + h() + f() (★★★★)

```
x = 1
func f() { x }
func h() { x = 100; f() }
f() + h() + f()
```

`h` introduce una `x` locale pari a 100 e poi chiama `f`. L'espressione finale chiama `f` tre volte: prima, dentro `h`, e dopo.

Prevedi il risultato con scoping **statico** e **dinamico**.

> **Attenzione:** `x = 100` dentro `h` è una variabile locale al frame di `h`, non un'assegnazione alla `x` globale. Non altera il risultato delle chiamate a `f()` fuori da `h`.

<details>
<summary>Soluzione</summary>

**Statico** → **3**

`f` cattura il frame globale (`x=1`). Il `Let('x', 100, ...)` dentro `h` scrive nel frame di `h`, non nel globale. Tutte e tre le chiamate a `f()` leggono `x=1`.

- `f()` = 1
- `h()` → frame di h con `x=100` → chiama `f()` → closure vede globale `x=1` → restituisce 1
- `f()` = 1
- Totale: `1 + 1 + 1` = **3**

**Dinamico** → **102**

`f` è una `DynFunction`. Il suo risultato dipende dall'ambiente al momento della chiamata.

- `f()` chiamata dal globale: `x=1` → 1
- `h()` → frame di h con `x=100` → chiama `f()` → lookup `x` nel frame corrente: `x=100` → 100
- `f()` chiamata dal globale: `x=1` → 1
- Totale: `1 + 100 + 1` = **102**

```python
h_body = Let('x', Num(100), Call(FunName('f'), []))

program = Let('x', Num(1),
           Let('f', Fun([], Var('x')),
            Let('h', Fun([], h_body),
             BinOp('+',
                 BinOp('+', Call(FunName('f'), []), Call(FunName('h'), [])),
                 Call(FunName('f'), [])))))

Interpreter(scoping='static').run(program)   # → 3
Interpreter(scoping='dynamic').run(program)  # → 102
```

| Scoping  | f() | h() → f() | f() | Totale |
|----------|:---:|:----------:|:---:|:------:|
| statico  |  1  |     1      |  1  |   3    |
| dinamico |  1  |    100     |  1  | 102    |

</details>

---

## Categoria 2: Passaggio parametri

### Esercizio 2.1 — Previsione semplice (★☆☆☆)

```
x = 3
func inc(n) { n = n + 1 }
inc(x)
x
```

Prevedi il valore finale di `x` con passaggio per **valore**, per **riferimento** e per **nome**.

<details>
<summary>Soluzione</summary>

- **Valore**: `n` è una copia di `x`. La modifica non si propaga al chiamante. `x = 3`
- **Riferimento**: `n` è un alias della cella di `x`. `x = 4`
- **Nome**: `n` contiene il thunk `Var('x')`. L'assegnamento `n = n+1` rivaluta il thunk (ottiene 3), calcola 4, poi sostituisce il thunk con 4 **solo nel frame locale** — non tocca `x`. `x = 3`

```python
program = Let('x', Num(3),
           Let('inc', Fun(['n'], Assign('n', BinOp('+', Var('n'), Num(1)))),
            Seq([Call(FunName('inc'), [Var('x')]), Var('x')])))

Interpreter(passing='value').run(program)      # → 3
Interpreter(passing='reference').run(program)  # → 4
Interpreter(passing='name').run(program)       # → 3
```

| Passaggio    | Risultato |
|--------------|-----------|
| valore       | 3         |
| riferimento  | 4         |
| nome         | 3         |

</details>

---

### Esercizio 2.2 — Quale variabile cambia? (★★☆☆)

```
a = 10
b = 20
func f(x) { x = x + b }
f(a)
a
```

Prevedi il valore finale di `a` con i tre tipi di passaggio. Per ognuno, spiega perché.

<details>
<summary>Soluzione</summary>

- **Valore**: `x` è una copia di `a`. L'assegnamento modifica la copia locale. `a = 10`
- **Riferimento**: `x` è un alias di `a`. `x = 10 + 20 = 30` scrive nella cella condivisa. `a = 30`
- **Nome**: `x = Thunk(Var('a'))`. L'assegnamento rivaluta il thunk (`a=10`), calcola `10+20=30`, poi scrive 30 nel binding locale di `x` (sostituisce il thunk). La variabile `a` non viene toccata. `a = 10`

```python
program = Let('a', Num(10),
           Let('b', Num(20),
            Let('f', Fun(['x'], Assign('x', BinOp('+', Var('x'), Var('b')))),
             Seq([Call(FunName('f'), [Var('a')]), Var('a')]))))

Interpreter(passing='value').run(program)      # → 10
Interpreter(passing='reference').run(program)  # → 30
Interpreter(passing='name').run(program)       # → 10
```

| Passaggio    | Risultato |
|--------------|-----------|
| valore       | 10        |
| riferimento  | 30        |
| nome         | 10        |

</details>

---

### Esercizio 2.3 — Jensen's device (★★★☆)

Costruisci un programma in cui una funzione `f(x)` legge `x` **dopo** aver azzerato una variabile `n` da cui `x` dipende. Il risultato deve essere diverso tra passaggio per valore e per nome.

```
n = 5
func f(x) { n = 0; x }
f(n * 10)
```

> **Suggerimento:** con passaggio per nome, `n * 10` non viene calcolato subito — viene rivalutato quando `x` viene letto, cioè dopo che `n` è stato azzerato.

<details>
<summary>Soluzione</summary>

- **Valore**: `n * 10 = 50` è calcolato **prima** della chiamata. Dentro `f`: `n = 0`, poi restituisce `x = 50` → **50**
- **Nome**: il thunk `n * 10` è valutato **quando `x` viene letto**, cioè dopo `n = 0`. `0 * 10 = 0` → **0**

Questo è il cosiddetto **Jensen's device** (ALGOL 60): l'effetto collaterale della funzione cambia il risultato dell'argomento.

```python
program = Let('n', Num(5),
           Let('f', Fun(['x'],
                   Seq([Assign('n', Num(0)),
                        Var('x')])),
            Call(FunName('f'), [BinOp('*', Var('n'), Num(10))])))

Interpreter(scoping='static', passing='value').run(program)  # → 50
Interpreter(scoping='static', passing='name').run(program)   # → 0
```

| Passaggio | Risultato |
|-----------|-----------|
| valore    | 50        |
| nome      | 0         |

</details>

---

### Esercizio 2.4 — Conta le valutazioni (★★★★)

```
count = 0
func tick()  { count = count + 1; count }
func g(x)    { x + x + x }
g(tick())
```

Prevedi il risultato con passaggio per **valore** e per **nome**.
Quante volte viene chiamata `tick()` in ciascun caso?

<details>
<summary>Soluzione</summary>

**Valore** — `tick()` è chiamata **una volta** prima di passare l'argomento:
- `tick()` → `count = 1`, restituisce 1
- `g(1)` = `1 + 1 + 1` = **3**

**Nome** — il thunk `Call(tick, [])` è rivalutato **ogni volta** che `x` viene letto (3 volte):
- prima `x` : `tick()` → `count = 1`, restituisce 1
- seconda `x`: `tick()` → `count = 2`, restituisce 2
- terza `x` : `tick()` → `count = 3`, restituisce 3
- `(1 + 2) + 3` = **6**

```python
tick_body = Seq([
    Assign('count', BinOp('+', Var('count'), Num(1))),
    Var('count')
])
program = Let('count', Num(0),
           Let('tick', Fun([], tick_body),
            Let('g', Fun(['x'],
                    BinOp('+', BinOp('+', Var('x'), Var('x')), Var('x'))),
             Call(FunName('g'), [Call(FunName('tick'), [])]))))

Interpreter(passing='value').run(program)  # → 3
Interpreter(passing='name').run(program)   # → 6
```

| Passaggio | Chiamate a `tick` | Risultato |
|-----------|-------------------|-----------|
| valore    | 1                 | 3         |
| nome      | 3                 | 6         |

</details>

---

### Esercizio 2.5 — Aliasing (★★★☆)

```
a = 5
func f(x, y) { x = x + 1; y = y + 1; x + y }
f(a, a)
```

Prevedi il valore restituito da `f(a, a)` con passaggio per **valore**, per **riferimento** e per **nome**.
Attenzione: `a` viene passata **due volte** come argomento.

<details>
<summary>Soluzione</summary>

- **Valore**: `x` e `y` ricevono copie indipendenti di `a=5`. `x=6`, `y=6`. Risultato: **12**.
- **Riferimento**: `x` e `y` sono entrambi alias della **stessa cella** di `a`. `x=x+1` aggiorna la cella a 6. `y=y+1` legge 6 dalla stessa cella e la aggiorna a 7. `x+y` = 7+7 = **14**.
- **Nome**: `x` e `y` sono thunk indipendenti di `Var('a')`. `x=x+1` rivaluta il thunk (ottiene 5), calcola 6, e sostituisce il thunk con 6 **solo nel frame locale** — `a` non cambia. Stesso per `y`. `x+y` = 6+6 = **12**.

Il passaggio per riferimento è l'unico che produce aliasing: modificare `x` cambia anche `y`.

```python
program = Let('a', Num(5),
           Let('f', Fun(['x', 'y'],
                   Seq([Assign('x', BinOp('+', Var('x'), Num(1))),
                        Assign('y', BinOp('+', Var('y'), Num(1))),
                        BinOp('+', Var('x'), Var('y'))])),
            Call(FunName('f'), [Var('a'), Var('a')])))

Interpreter(scoping='static', passing='value').run(program)      # → 12
Interpreter(scoping='static', passing='reference').run(program)  # → 14
Interpreter(scoping='static', passing='name').run(program)       # → 12
```

| Passaggio    | Risultato | Nota                           |
|--------------|-----------|--------------------------------|
| valore       | 12        | x e y indipendenti             |
| riferimento  | 14        | x e y alias della stessa cella |
| nome         | 12        | thunk sostituiti localmente    |

</details>

---

### Esercizio 2.6 — Due argomenti per nome (★★★★)

```
count = 0
func step()    { count = count + 1; count }
func h(a, b)   { a * b + a }
h(step(), step())
```

Prevedi il risultato con passaggio per **valore** e per **nome**.
Quante volte viene chiamata `step()` in ciascun caso? In quale ordine?

<details>
<summary>Soluzione</summary>

**Valore** — gli argomenti sono valutati **prima** della chiamata, da sinistra a destra:
- 1° arg: `step()` → `count = 1`, restituisce 1 → `a = 1`
- 2° arg: `step()` → `count = 2`, restituisce 2 → `b = 2`
- `h(1, 2)` = `1 * 2 + 1` = **3**

**Nome** — i thunk `Call(step,[])` sono rivalutati ogni volta che `a` o `b` vengono letti.
L'espressione `a * b + a` si valuta come `(a * b) + a`:
- `a` (primo nel prodotto): `step()` → `count = 1`, restituisce 1
- `b`: `step()` → `count = 2`, restituisce 2
- `1 * 2 = 2`
- `a` (nella somma): `step()` → `count = 3`, restituisce 3
- `2 + 3` = **5**

`step()` è chiamata **3 volte** con nome, anche se `a` appare due volte e `b` una.

```python
step_body = Seq([Assign('count', BinOp('+', Var('count'), Num(1))), Var('count')])
program = Let('count', Num(0),
           Let('step', Fun([], step_body),
            Let('h', Fun(['a', 'b'],
                    BinOp('+', BinOp('*', Var('a'), Var('b')), Var('a'))),
             Call(FunName('h'), [Call(FunName('step'), []),
                                 Call(FunName('step'), [])]))))

Interpreter(scoping='static', passing='value').run(program)  # → 3
Interpreter(scoping='static', passing='name').run(program)   # → 5
```

| Passaggio | Chiamate a `step` | `a`, `b`, `a` | Risultato |
|-----------|-------------------|---------------|-----------|
| valore    | 2 (prima della chiamata) | 1, 2, 1  | 3 |
| nome      | 3 (una per ogni lettura) | 1, 2, 3  | 5 |

</details>
