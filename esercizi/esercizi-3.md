# Esercizi avanzati — Passaggio per nome, Incremento e Binding

Ogni esercizio richiede di **prevedere** il risultato o **costruire** un programma AST.
Verifica sempre le tue previsioni eseguendo il codice.

Legenda difficoltà: ★☆☆☆ facile → ★★★★ difficile

> Tutti gli esercizi usano `let_scope=False` (default imperativo) salvo dove indicato.
> Ricorda: con `let_scope=False` i `Let` consecutivi scrivono nello stesso frame corrente.

---

## Categoria 1: Passaggio per nome con assegnamento

> Il passaggio per nome segue la semantica ALGOL 60: il parametro formale è una
> **sostituzione testuale** dell'argomento. Assegnare al parametro equivale ad
> assegnare alla variabile originale nel chiamante — **se l'argomento è un l-value
> (cioè una semplice variabile)**. Se l'argomento è un'espressione complessa (es.
> `a * 2`), il parametro non è un l-value e qualsiasi tentativo di assegnargli un
> valore solleva un errore.

---

### Esercizio 1.1 — Modifica diretta tramite nome (★★★☆)

```
x = 5
func add2(a) { a = a + 2 }
add2(x)
x
```

Prevedi il valore finale di `x` con i tre tipi di passaggio. Spiega perché nome e
riferimento producono lo stesso risultato pur agendo in modo diverso internamente.

<details>
<summary>Soluzione</summary>

- **Valore**: `a` è una copia di `x`. L'assegnamento modifica la copia locale. `x = 5`
- **Riferimento**: `a` è un alias della cella di `x`. `a = 5 + 2 = 7` aggiorna la cella condivisa. `x = 7`
- **Nome**: `a = Thunk(Var('x'))`. `a = a + 2` valuta il thunk (ottiene 5), calcola 7, poi **scrive 7 su `x` nell'env del chiamante** (sostituzione testuale: `a = a + 2` diventa `x = x + 2`). `x = 7`

Il risultato è identico per nome e riferimento perché l'argomento `x` è una semplice variabile — un l-value valido in entrambi i casi. La differenza interna:
- Riferimento usa una **cella condivisa** (`Ref`): la scrittura va nella cella.
- Nome usa un **thunk**: la scrittura individua l'l-value del thunk e aggiorna la variabile nell'env del chiamante.

```python
program = Let('x', Num(5),
           Let('add2', Fun(['a'], Assign('a', BinOp('+', Var('a'), Num(2)))),
            Seq([Call(FunName('add2'), [Var('x')]), Var('x')])))

Interpreter(passing='value').run(program)      # → 5
Interpreter(passing='reference').run(program)  # → 7
Interpreter(passing='name').run(program)       # → 7
```

| Passaggio   | Risultato |
|-------------|-----------|
| valore      | 5         |
| riferimento | 7         |
| nome        | 7         |

</details>

---

### Esercizio 1.2 — Cascata di assegnamenti per nome (★★★☆)

```
x = 3
func f(a) { a = a * 2; a = a + x }
f(x)
x
```

Prevedi il valore finale di `x` con i tre tipi di passaggio.

> **Suggerimento:** Con passaggio per nome, ogni assegnamento a `a` modifica `x`
> nell'ambiente del chiamante. Il secondo assegnamento legge la `x` già modificata
> dal primo.

<details>
<summary>Soluzione</summary>

**Valore** — `a` è una copia di `x = 3`. La variabile libera `x` è quella globale (invariata).
1. `a = a * 2` → `a = 3 * 2 = 6`  (locale)
2. `a = a + x` → `a = 6 + 3 = 9`  (locale; `x` è ancora 3)
3. `x` rimane `3`

**Riferimento** — `a` è `Ref(x)`, quindi leggere o scrivere `a` equivale a leggere o scrivere `x`.
1. `a = a * 2` → `x = x * 2 = 6`
2. `a = a + x` → `x = x + x = 6 + 6 = 12`  (`x` è già 6 dopo il primo passo)
3. `x = 12`

**Nome** — `a = Thunk(Var('x'))`. Ogni lettura di `a` rivaluta il thunk (legge `x` corrente); ogni scrittura a `a` scrive su `x`.
1. `a = a * 2` → legge thunk (`x = 3`), calcola 6, scrive su `x` → `x = 6`
2. `a = a + x` → legge thunk (`x = 6`!), legge `x` (= 6), calcola 12, scrive su `x` → `x = 12`
3. `x = 12`

```python
body = Seq([
    Assign('a', BinOp('*', Var('a'), Num(2))),
    Assign('a', BinOp('+', Var('a'), Var('x')))
])
program = Let('x', Num(3),
           Let('f', Fun(['a'], body),
            Seq([Call(FunName('f'), [Var('x')]), Var('x')])))

Interpreter(passing='value').run(program)      # → 3
Interpreter(passing='reference').run(program)  # → 12
Interpreter(passing='name').run(program)       # → 12
```

| Passaggio   | x dopo il 1° assign | x dopo il 2° assign | Risultato |
|-------------|---------------------|---------------------|-----------|
| valore      | 3 (copia locale)    | 3 (copia locale)    | 3         |
| riferimento | 6                   | 12                  | 12        |
| nome        | 6                   | 12                  | 12        |

La differenza fra nome e valore emerge perché con nome il parametro è un alias
della variabile originale: ogni scrittura si propaga immediatamente e ogni lettura
riflette il valore aggiornato.

</details>

---

### Esercizio 1.3 — Lo swap funziona con il passaggio per nome? (★★★☆)

```
a = 10, b = 20
swap = fun(x, y) { tmp = x; x = y; y = tmp }
swap(a, b)
a * 100 + b
```

Prevedi il risultato con i tre tipi di passaggio. Lo swap di `a` e `b` avviene con
il passaggio per nome?

<details>
<summary>Soluzione</summary>

**Valore** — `x` e `y` sono copie. Lo scambio avviene solo localmente. `a` e `b` restano invariati.
`a * 100 + b = 10 * 100 + 20 = 1020`

**Riferimento** — `x = Ref(a)`, `y = Ref(b)`.
1. `Let('tmp', Var('x'), ...)` → `tmp = Ref(a).value = 10`
2. `Assign('x', Var('y'))` → `Ref(a).value = Ref(b).value = 20` → `a = 20`
3. `Assign('y', Var('tmp'))` → `Ref(b).value = tmp = 10` → `b = 10`
`a * 100 + b = 20 * 100 + 10 = 2010`

**Nome** — `x = Thunk(Var('a'))`, `y = Thunk(Var('b'))`.
1. `Let('tmp', Var('x'), ...)` → valuta thunk `x` → `tmp = a = 10`
2. `Assign('x', Var('y'))` → valuta thunk `y` (= `b = 20`), scrive l'l-value di `x` (= `a`) → `a = 20`
3. `Assign('y', Var('tmp'))` → `tmp = 10`, scrive l'l-value di `y` (= `b`) → `b = 10`
`a * 100 + b = 20 * 100 + 10 = 2010`

Lo swap funziona sia con nome che con riferimento perché in entrambi i casi
il parametro formale è un alias dell'argomento originale.

```python
swap_body = Seq([
    Let('tmp', Var('x'),
        Seq([Assign('x', Var('y')),
             Assign('y', Var('tmp'))]))
])
program = Let('a', Num(10),
           Let('b', Num(20),
            Let('swap', Fun(['x', 'y'], swap_body),
             Seq([Call(FunName('swap'), [Var('a'), Var('b')]),
                  BinOp('+', BinOp('*', Var('a'), Num(100)), Var('b'))]))))

Interpreter(passing='value').run(program)      # → 1020
Interpreter(passing='reference').run(program)  # → 2010
Interpreter(passing='name').run(program)       # → 2010
```

| Passaggio   | Risultato | Swap avvenuto? |
|-------------|-----------|----------------|
| valore      | 1020      | No             |
| riferimento | 2010      | Sì             |
| nome        | 2010      | Sì             |

</details>

---

### Esercizio 1.4 — Il bug dell'aliasing: swap(a, a) (★★★★)

Usa la stessa funzione `swap` dell'esercizio precedente, ma chiamala passando
**la stessa variabile due volte**:

```
a = 99
swap(a, a)
a
```

Prevedi il risultato con passaggio per **riferimento** e per **nome**.

> **Attenzione:** questo è il classico *aliasing bug* degli scambi. Analizza passo
> per passo cosa succede quando i due parametri puntano alla stessa variabile.

<details>
<summary>Soluzione</summary>

**Riferimento** — `x = Ref(a)`, `y = Ref(a)`: **la stessa cella**.
1. `Let('tmp', Var('x'), ...)` → `tmp = Ref.value = 99`
2. `Assign('x', Var('y'))` → legge `Ref.value = 99`, scrive `Ref.value = 99` → nessun cambiamento
3. `Assign('y', Var('tmp'))` → `tmp = 99`, scrive `Ref.value = 99` → nessun cambiamento
`a = 99` (swap non avvenuto)

**Nome** — `x = Thunk(Var('a'))`, `y = Thunk(Var('a'))`: **lo stesso l-value**.
1. `Let('tmp', Var('x'), ...)` → valuta thunk `x` → `tmp = a = 99`
2. `Assign('x', Var('y'))` → valuta thunk `y` (= `a = 99`), scrive l'l-value di `x` (= `a`) → `a = 99` (invariato)
3. `Assign('y', Var('tmp'))` → `tmp = 99`, scrive l'l-value di `y` (= `a`) → `a = 99` (invariato)
`a = 99` (swap non avvenuto)

In entrambi i casi l'aliasing rende lo swap un no-op: `tmp` cattura il valore
iniziale, ma il passo 2 non cambia nulla perché sia sorgente che destinazione
sono la stessa variabile.

```python
swap_body = Seq([
    Let('tmp', Var('x'),
        Seq([Assign('x', Var('y')),
             Assign('y', Var('tmp'))]))
])
program = Let('a', Num(99),
           Let('swap', Fun(['x', 'y'], swap_body),
            Seq([Call(FunName('swap'), [Var('a'), Var('a')]),
                 Var('a')])))

Interpreter(passing='reference').run(program)  # → 99
Interpreter(passing='name').run(program)       # → 99
```

| Passaggio   | Risultato | Nota                         |
|-------------|-----------|------------------------------|
| riferimento | 99        | x e y alias della stessa Ref |
| nome        | 99        | x e y thunk dello stesso l-value |

> **Lezione**: lo swap corretto richiede due locazioni di memoria distinte.
> Qualunque meccanismo di aliasing (sia Ref che Thunk) fa fallire lo swap
> quando i due argomenti sono la stessa variabile.

</details>

---

## Categoria 2: Operatori PostInc e PreInc

> `PostInc('x')` corrisponde a `x++`: restituisce il valore **prima** dell'incremento.
> `PreInc('x')` corrisponde a `++x`: restituisce il valore **dopo** l'incremento.
> Entrambi rispettano la semantica di `Assign`: scrivono attraverso `Ref` e `Thunk`
> esattamente come farebbe un assegnamento esplicito.

---

### Esercizio 2.1 — Pre vs post in una sequenza (★★☆☆)

```
x = 5
a = x++
b = ++x
a * 10 + b
```

Prevedi il valore di `a`, `b` e `x` dopo ogni operazione, e il risultato finale.

<details>
<summary>Soluzione</summary>

Passo per passo:

| Operazione | Effetto su `x` | Valore restituito |
|------------|----------------|-------------------|
| `x = 5`    | `x = 5`        | —                 |
| `a = x++`  | `x → 6`        | `5` (valore PRIMA) → `a = 5` |
| `b = ++x`  | `x → 7`        | `7` (valore DOPO)  → `b = 7` |

`a * 10 + b = 5 * 10 + 7 = 57`

```python
program = Let('x', Num(5),
           Let('a', PostInc('x'),
            Let('b', PreInc('x'),
             BinOp('+', BinOp('*', Var('a'), Num(10)), Var('b')))))

Interpreter().run(program)  # → 57
```

Il punto chiave: `x++` e `++x` incrementano entrambi di 1, ma restituiscono
rispettivamente il valore vecchio e il valore nuovo. Dopo `x++` con `x=5`,
`x` è già 6 quando `++x` viene valutato.

</details>

---

### Esercizio 2.2 — PostInc nei tre tipi di passaggio (★★★☆)

```
counter = 0
bump = fun(n) { n++ }
bump(counter)
counter
```

Prevedi il valore finale di `counter` con i tre tipi di passaggio.

> **Nota:** `n++` restituisce il valore vecchio, ma ciò che importa qui è
> l'effetto collaterale sull'argomento originale, non il valore restituito da `bump`.

<details>
<summary>Soluzione</summary>

- **Valore**: `n` è una copia di `counter`. `n++` incrementa la copia locale (`n` da 0 a 1), ma `counter` non cambia. `counter = 0`

- **Riferimento**: `n = Ref(counter)`. `n++` legge `Ref.value = 0`, scrive `Ref.value = 1`. Siccome `counter` e `n` condividono la stessa cella, `counter = 1`

- **Nome**: `n = Thunk(Var('counter'))`. `n++` legge il thunk (ottiene 0), scrive 1 sull'l-value `counter`. `counter = 1`

```python
program = Let('counter', Num(0),
           Let('bump', Fun(['n'], PostInc('n')),
            Seq([Call(FunName('bump'), [Var('counter')]), Var('counter')])))

Interpreter(passing='value').run(program)      # → 0
Interpreter(passing='reference').run(program)  # → 1
Interpreter(passing='name').run(program)       # → 1
```

| Passaggio   | Risultato |
|-------------|-----------|
| valore      | 0         |
| riferimento | 1         |
| nome        | 1         |

</details>

---

### Esercizio 2.3 — Aliasing con PostInc e PreInc (★★★★)

```
a = 5
f = fun(x, y) { x++; ++y; x + y }
f(a, a)
```

Prevedi il risultato con i tre tipi di passaggio. Tieni traccia di `a` dopo ogni operazione.

> **Attenzione:** con nome e riferimento, `x` e `y` puntano entrambi ad `a`.
> Considera come le due operazioni di incremento si influenzano a vicenda.

<details>
<summary>Soluzione</summary>

**Valore** — `x = 5`, `y = 5` (copie indipendenti).
1. `x++` → `x` locale: 5 → 6 (restituisce 5, scartato da `Seq`)
2. `++y` → `y` locale: 5 → 6 (restituisce 6, scartato da `Seq`)
3. `x + y = 6 + 6 = 12`

**Riferimento** — `x = Ref(a)`, `y = Ref(a)`: **la stessa cella**.
1. `x++` → legge `Ref = 5`, scrive `Ref = 6` → `a = 6`
2. `++y` → legge `Ref = 6`, scrive `Ref = 7` → `a = 7`
3. `x + y` → `Ref + Ref = 7 + 7 = 14`

**Nome** — `x = Thunk(Var('a'))`, `y = Thunk(Var('a'))`: **lo stesso l-value**.
1. `x++` → legge thunk (`a = 5`), scrive 6 su `a` → `a = 6`
2. `++y` → legge thunk (`a = 6`!), scrive 7 su `a` → `a = 7`
3. `x + y` → valuta thunk `x` (`a = 7`) + thunk `y` (`a = 7`) = **14**

Con nome e riferimento l'aliasing fa sì che il secondo incremento parta da 6
(non da 5): le due operazioni non sono indipendenti.

```python
body = Seq([PostInc('x'), PreInc('y'), BinOp('+', Var('x'), Var('y'))])
program = Let('a', Num(5),
           Let('f', Fun(['x', 'y'], body),
            Call(FunName('f'), [Var('a'), Var('a')])))

Interpreter(passing='value').run(program)      # → 12
Interpreter(passing='reference').run(program)  # → 14
Interpreter(passing='name').run(program)       # → 14
```

| Passaggio   | Dopo `x++` | Dopo `++y` | `x + y` | Risultato |
|-------------|------------|------------|---------|-----------|
| valore      | x=6, y=5   | x=6, y=6   | 6+6     | 12        |
| riferimento | a=6        | a=7        | 7+7     | 14        |
| nome        | a=6        | a=7        | 7+7     | 14        |

</details>

---

### Esercizio 2.4 — Incrementi come argomenti (★★★☆)

```
a = 5
func f(x, y) { x + x + 2 * y }
f(a++, ++a)
```

Prevedi il valore restituito da `f(a++, ++a)` con passaggio per **valore** e per **nome**.
Il passaggio per **riferimento** è applicabile qui? Perché?

> **Nota C:** `f(a++, ++a)` in C è **undefined behaviour** (due modifiche ad `a` senza sequence point tra gli argomenti). L'interprete invece garantisce valutazione da sinistra a destra, rendendo il comportamento deterministico.
>
> **Suggerimento:** ricorda che `a++` (post-incremento) restituisce il valore **prima** dell'incremento, mentre `++a` (pre-incremento) restituisce il valore **dopo**. Con passaggio per nome, `x` appare **due volte** nel corpo: ogni lettura rivaluta il thunk su un `a` diverso.

<details>
<summary>Soluzione</summary>

**Riferimento — non applicabile**

Il passaggio per riferimento richiede che l'argomento sia una variabile (un l-value). `a++` e `++a` sono espressioni che restituiscono un valore temporaneo: non c'è una "variabile" a cui legare l'alias. L'interprete solleva un `TypeError`.

---

**Valore** → **24**

Gli argomenti sono valutati **prima** della chiamata, da sinistra a destra:
- `a++`: legge `a=5`, incrementa `a` a 6, restituisce **5** → `x = 5`
- `++a`: incrementa `a` a 7, restituisce **7** → `y = 7`

`x + x + 2*y` = `5 + 5 + 2*7` = **24**

---

**Nome** → **27**

Gli argomenti diventano thunk rivalutati ad ogni lettura nel corpo. Il corpo `x + x + 2*y` si valuta come `(x + x) + (2 * y)`:

- Prima lettura di `x`: rivaluta `PostInc('a')` con `a=5` → restituisce **5**, `a` diventa **6**
- Seconda lettura di `x`: rivaluta `PostInc('a')` con `a=6` → restituisce **6**, `a` diventa **7**
- Lettura di `y`: rivaluta `PreInc('a')` con `a=7` → `a` diventa **8**, restituisce **8**
- `(5 + 6) + 2*8` = `11 + 16` = **27**

Con passaggio per nome il risultato è diverso perché `x` viene rivalutato due volte: la seconda lettura opera su un `a` già incrementato dalla prima.

```python
body = BinOp('+', BinOp('+', Var('x'), Var('x')), BinOp('*', Num(2), Var('y')))
program = Let('a', Num(5),
           Let('f', Fun(['x', 'y'], body),
            Call(FunName('f'), [PostInc('a'), PreInc('a')])))

Interpreter(passing='value').run(program)      # → 24
Interpreter(passing='name').run(program)       # → 27
# Interpreter(passing='reference').run(program) # → TypeError: richiede l-value
```

| Passaggio    | x (1°) | x (2°) | y  | Risultato |
|--------------|:------:|:------:|:--:|:---------:|
| valore       | 5      | 5      | 7  | 24        |
| nome         | 5      | 6      | 8  | 27        |
| riferimento  | —      | —      | —  | TypeError |

</details>

---

## Categoria 3: Deep binding vs Shallow binding

> Questi esercizi usano **scoping dinamico** (`scoping='dynamic'`) e confrontano
> i due tipi di binding per le funzioni passate come argomento:
>
> - **Shallow binding**: la funzione passata come argomento viene chiamata
>   nell'ambiente **del momento della chiamata** (nessuna cattura).
> - **Deep binding**: la funzione passata come argomento cattura l'ambiente
>   **del momento del passaggio** (wrappata in `DynClosure`).
>
> Con **scoping statico** le funzioni sono sempre `Closure` e catturano l'ambiente
> alla **definizione**, indipendentemente da chi le passa o le chiama.

---

### Esercizio 3.1 — apply(f): quale x vede g? (★★★☆)

```
x = 1
f    = fun()    { x }
apply = fun(g)  { let x = 100 in g() }
apply(f)
```

Prevedi il risultato con scoping **statico**, **dinamico shallow** e **dinamico deep**.

<details>
<summary>Soluzione</summary>

```python
program = Let('x', Num(1),
           Let('f', Fun([], Var('x')),
            Let('apply', Fun(['g'],
                    Let('x', Num(100),
                        Call(FunName('g'), []))),
             Call(FunName('apply'), [FunName('f')]))))
```

**Scoping statico** → **1**

`f` è una `Closure` che cattura l'env globale al momento della definizione (dove `x = 1`). `apply` introduce `x = 100` nel proprio call frame, ma non tocca il globale. Quando `g()` viene chiamata, `f` usa il proprio env catturato → `x = 1`.

**Dinamico shallow** → **100**

`f` è una `DynFunction` (nessuna cattura). Quando `g()` è chiamata dall'interno di `apply`, il call frame di `apply` è l'env corrente e contiene `x = 100`. La lookup di `x` trova 100.

**Dinamico deep** → **1**

`f` è una `DynFunction`. Al momento del passaggio come argomento (call_env = env globale con `x = 1`), viene wrappata in una `DynClosure` che cattura quell'env. Quando `g()` viene chiamata dentro `apply`, `g` usa l'env catturato (globale, `x = 1`).

```python
Interpreter(scoping='static').run(program)                   # → 1
Interpreter(scoping='dynamic', binding='shallow').run(program)  # → 100
Interpreter(scoping='dynamic', binding='deep').run(program)     # → 1
```

| Scoping         | `x` visto da `g` | Risultato |
|-----------------|------------------|-----------|
| statico         | 1 (env di definizione) | 1   |
| dinamico shallow| 100 (env di chiamata)  | 100 |
| dinamico deep   | 1 (env di passaggio)   | 1   |

Con static e deep il risultato coincide: in entrambi i casi `f` è indipendente
dall'ambiente di chi la chiama. La differenza è **quando** l'env viene catturato
(definizione vs passaggio come argomento).

</details>

---

### Esercizio 3.2 — Due callback, una x che cambia nel mezzo (★★★★)

```
x = 5
f    = fun() { x }
g    = fun() { x }
apply2 = fun(f, g) { f() + (let x = 100 in g()) }
apply2(f, g)
```

`apply2` chiama `f()` prima di introdurre `x = 100` localmente, poi chiama `g()`
all'interno di quello scope.

Prevedi il risultato con scoping **statico**, **dinamico shallow** e **dinamico deep**.

> **Suggerimento:** con shallow binding, il momento della chiamata è diverso per
> `f()` e `g()`. Con deep binding, entrambe le funzioni catturano l'env al momento
> del **passaggio**, non della chiamata.

<details>
<summary>Soluzione</summary>

```python
apply2_body = BinOp('+',
    Call(FunName('f'), []),
    Let('x', Num(100), Call(FunName('g'), [])))

program = Let('x', Num(5),
           Let('f', Fun([], Var('x')),
            Let('g', Fun([], Var('x')),
             Let('apply2', Fun(['f', 'g'], apply2_body),
              Call(FunName('apply2'), [FunName('f'), FunName('g')])))))
```

**Scoping statico** → **10**

`f` e `g` sono `Closure` che catturano il frame globale (dove `x = 5`). `apply2` introduce `x = 100` nel proprio call frame, ma il globale resta `x = 5`. Entrambe le chiamate restituiscono 5. `5 + 5 = 10`.

**Dinamico shallow** → **105**

`f` e `g` sono `DynFunction`.
- `f()` è chiamata quando il call frame di `apply2` non ha ancora `x` → risale al globale `x = 5` → **5**
- `Let('x', 100, ...)` aggiunge `x = 100` al call frame di `apply2`
- `g()` è chiamata con il call frame di `apply2` aggiornato → trova `x = 100` → **100**
`5 + 100 = 105`

**Dinamico deep** → **10**

`f` e `g` sono wrappate in `DynClosure` al momento del passaggio (call_env = env globale con `x = 5`). Entrambe usano quell'env catturato, indipendentemente da cosa `apply2` fa al proprio frame. Entrambe restituiscono 5. `5 + 5 = 10`.

```python
Interpreter(scoping='static').run(program)                   # → 10
Interpreter(scoping='dynamic', binding='shallow').run(program)  # → 105
Interpreter(scoping='dynamic', binding='deep').run(program)     # → 10
```

| Scoping          | `f()` | `g()` | Risultato |
|------------------|:-----:|:-----:|:---------:|
| statico          | 5     | 5     | 10        |
| dinamico shallow | 5     | 100   | 105       |
| dinamico deep    | 5     | 5     | 10        |

Con shallow binding, `f` e `g` vedono ambienti diversi pur essendo funzioni
identiche: il risultato dipende da **quando** vengono chiamate. Con deep e static,
l'env è determinato prima della chiamata e non può essere alterato da `apply2`.

</details>

---

### Esercizio 3.3 — Tre momenti diversi, tre valori di x (★★★★)

> Questo esercizio richiede `let_scope=True` (stile funzionale) per creare
> scope annidati distinti.

```
let x = 1 in          -- (A) x al momento della definizione di f
  let f = fun() { x } in
    let x = 50 in     -- (B) x al momento del passaggio di f
      let apply = fun(g) { let x = 99 in g() } in
        apply(f)      -- f passata qui, con x = 50 nello scope
```

I tre tipi di scoping/binding catturano `x` in tre momenti distinti:
- Statico: momento **(A)** — definizione di `f`
- Deep: momento **(B)** — passaggio di `f` come argomento
- Shallow: momento **(C)** — chiamata di `g()` dentro `apply`, dove `x = 99`

Prevedi il risultato per ognuno.

<details>
<summary>Soluzione</summary>

```python
program = Let('x', Num(1),
           Let('f', Fun([], Var('x')),
            Let('x', Num(50),
             Let('apply', Fun(['g'],
                     Let('x', Num(99),
                         Call(FunName('g'), []))),
              Call(FunName('apply'), [FunName('f')])))))
```

Con `let_scope=True`, ogni `Let` crea un nuovo scope figlio. Al momento della
chiamata `apply(f)`, la catena di scope è:

```
[global] → [x=1] → [f=<fun>] → [x=50] → [apply=<fun>]  ← call site
```

**Scoping statico** → **1**

`f` è una `Closure` che cattura `[f=<fun>]` (il frame creato dal `Let('f', ...)`),
il cui parent è `[x=1]`. La lookup di `x` risale: `[f]` → `[x=1]` (trovata) → **1**.
`apply` non può influenzare l'env catturato da `f`.

**Dinamico shallow** → **99**

`f` è una `DynFunction`. Viene chiamata come `g()` dall'interno del body di `apply`,
dopo che `Let('x', 99, ...)` ha creato `[x=99]`. Il call frame di `g` ha come
parent l'env corrente inside `apply` (che ha `[x=99]` in catena) → **99**.

**Dinamico deep** → **50**

`f` è una `DynFunction`. Al momento del passaggio come argomento, `call_env` è
il frame `[apply=<fun>]`, il cui parent è `[x=50]`. `f` viene wrappata in
`DynClosure(env=[apply=<fun>])`. Quando `g()` è chiamata, il call frame di `g`
ha come parent `[apply=<fun>]` → lookup `x`: non nel frame di `g` → non in
`[apply]` → `[x=50]` → **50**.

```python
Interpreter(scoping='static',  let_scope=True).run(program)              # → 1
Interpreter(scoping='dynamic', let_scope=True, binding='shallow').run(program)  # → 99
Interpreter(scoping='dynamic', let_scope=True, binding='deep').run(program)     # → 50
```

| Scoping          | `x` catturato da           | Valore | Risultato |
|------------------|----------------------------|:------:|:---------:|
| statico          | definizione di `f`  (A)    | 1      | 1         |
| dinamico shallow | chiamata di `g()` in apply (C) | 99 | 99        |
| dinamico deep    | passaggio di `f` (B)       | 50     | 50        |

Questo esercizio è la sintesi del problema del binding: i tre modi di scoping
rappresentano tre domande diverse — *dove è stata definita la funzione?*,
*dove viene chiamata?*, *dove è stata passata come argomento?* — e ciascuno
risponde con un valore diverso.

</details>
