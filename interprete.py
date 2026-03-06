"""
Interprete Didattico per Linguaggi di Programmazione
=====================================================

Permette di esplorare tre concetti fondamentali:

  1. SCOPING:  static (lexical)  vs  dynamic
  2. PASSING:  by value          vs  by reference  vs  by name
  3. DEBUG:    visualizzazione passo per passo dell'esecuzione

I programmi non vengono parsati da testo: si costruiscono direttamente
come alberi di oggetti Python (AST manuali). Questo permette di
concentrarsi sulla semantica, non sulla sintassi.

Uso tipico:
    from interprete import *

    program = Let('x', Num(5),
                  BinOp('+', Var('x'), Num(1)))

    interp = Interpreter(scoping='static', passing='value', debug=True)
    interp.run(program)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional


# ════════════════════════════════════════════════════════════════
# PARTE 1 — NODI DELL'AST
#
# Ogni nodo rappresenta un costrutto del linguaggio.
# I programmi si costruiscono annidando questi oggetti.
# ════════════════════════════════════════════════════════════════

@dataclass
class Num:
    """Numero letterale.  Es: Num(42)  →  42"""
    value: float


@dataclass
class Var:
    """Riferimento a una variabile.  Es: Var('x')  →  il valore di x"""
    name: str


class FunName(Var):
    """Riferimento a una funzione per nome.  Es: FunName('f')  →  la funzione f
    Sottoclasse di Var: stessa semantica, ma rende esplicito che si sta
    referenziando una funzione, non un valore generico.
    """
    pass


@dataclass
class BinOp:
    """Operazione binaria.
    Es: BinOp('+', Var('x'), Num(1))  →  x + 1
    Operatori supportati: '+', '-', '*', '/'
    """
    op: str
    left: Any
    right: Any


@dataclass
class Let:
    """Binding locale: lega 'name' a 'value' nel 'body'.
    Es: Let('x', Num(5), BinOp('*', Var('x'), Num(2)))
    Equivale a:  let x = 5 in x * 2
    """
    name: str
    value: Any
    body: Any


@dataclass
class Fun:
    """Definizione di funzione anonima.
    Es: Fun(['x', 'y'], BinOp('+', Var('x'), Var('y')))
    Equivale a:  fun(x, y) { x + y }
    """
    params: List[str]
    body: Any


@dataclass
class Call:
    """Chiamata di funzione.
    Es: Call(Var('f'), [Num(3), Num(4)])
    Equivale a:  f(3, 4)
    """
    func: Any
    args: List[Any]


@dataclass
class If:
    """Condizionale.
    Es: If(Var('x'), Num(1), Num(0))
    Equivale a:  if x then 1 else 0
    (qualunque valore non-zero è considerato vero)
    """
    cond: Any
    then_: Any
    else_: Any


@dataclass
class Assign:
    """Assegnamento a una variabile esistente.
    Es: Assign('x', Num(42))
    Equivale a:  x = 42
    Importante per il passaggio per riferimento.
    """
    name: str
    value: Any


@dataclass
class Seq:
    """Sequenza di espressioni (valuta tutte, restituisce l'ultima).
    Es: Seq([Assign('x', Num(1)), Var('x')])
    """
    exprs: List[Any]


# ════════════════════════════════════════════════════════════════
# PARTE 2 — VALORI A RUNTIME
#
# Questi oggetti esistono durante l'esecuzione, non nell'AST.
# ════════════════════════════════════════════════════════════════

class Closure:
    """
    [Scoping STATICO] Funzione + ambiente catturato alla definizione.

    Quando una funzione viene definita con scoping statico, l'interprete
    salva una copia dell'ambiente corrente. Quando viene chiamata, il
    corpo "vede" quell'ambiente — non quello di chi la chiama.

    Questo è il comportamento di Python, Java, Haskell, ...
    """
    def __init__(self, params: List[str], body, env: 'Env'):
        self.params = params
        self.body = body
        self.env = env  # ambiente catturato alla DEFINIZIONE

    def __repr__(self):
        return f"<fun({', '.join(self.params)})>"


class DynFunction:
    """
    [Scoping DINAMICO] Funzione senza ambiente catturato.

    Quando viene chiamata, il corpo "vede" l'ambiente del chiamante.
    Il comportamento dipende da chi chiama la funzione.

    Questo è il comportamento di Bash, alcuni dialetti Lisp, ...
    """
    def __init__(self, params: List[str], body):
        self.params = params
        self.body = body

    def __repr__(self):
        return f"<dyn-fun({', '.join(self.params)})>"


class DynClosure:
    """
    [Scoping DINAMICO + Deep Binding] Funzione con ambiente catturato
    al momento del PASSAGGIO come argomento.

    Differisce da Closure (scoping statico, cattura alla definizione)
    e da DynFunction (shallow binding, usa l'env al momento della chiamata).

    Viene creata automaticamente dall'interprete quando:
      - scoping = 'dynamic'
      - binding = 'deep'
      - si passa una funzione come argomento a un'altra funzione

    Esempio storico: implementazioni di LISP con funarg profondo.
    """
    def __init__(self, params: List[str], body, env: 'Env'):
        self.params = params
        self.body = body
        self.env = env  # ambiente catturato al PASSAGGIO

    def __repr__(self):
        return f"<dyn-closure({', '.join(self.params)})>"


class Ref:
    """
    [Passaggio per RIFERIMENTO] Cella mutabile condivisa.

    Chiamante e chiamato condividono la stessa cella.
    Modificare il parametro dentro la funzione modifica la variabile
    originale fuori dalla funzione.

    Equivale ai puntatori in C o ai parametri 'ref' in Pascal.
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Ref({self.value!r})"


class Thunk:
    """
    [Passaggio per NOME] Espressione sospesa (non ancora valutata).

    L'espressione viene valutata ogni volta che il parametro viene usato,
    nell'ambiente del chiamante (non del chiamato).

    Effetto: gli effetti collaterali dentro la funzione (es. modificare
    una variabile) possono cambiare il risultato dell'argomento.

    Era il comportamento di ALGOL 60.
    """
    def __init__(self, expr, env: 'Env'):
        self.expr = expr
        self.env = env  # ambiente del CHIAMANTE

    def __repr__(self):
        return f"<thunk: {self.expr}>"


# ════════════════════════════════════════════════════════════════
# PARTE 3 — ENVIRONMENT (CATENA DI SCOPE)
#
# Un environment è un dizionario di binding (name → value)
# collegato a un environment padre. Forma una lista concatenata:
#
#   [local scope] → [function scope] → [global scope] → None
# ════════════════════════════════════════════════════════════════

class Env:
    """
    Catena di scope per la gestione delle variabili.

    Ogni frame contiene i binding del livello corrente e un puntatore
    al frame padre. La ricerca risale la catena finché non trova la
    variabile o raggiunge la fine (errore).
    """

    def __init__(self, parent: Optional[Env] = None, label: str = "",
                 is_call_frame: bool = False):
        self.bindings: dict = {}      # variabili definite in questo scope
        self.parent: Optional[Env] = parent
        self.label: str = label
        self.is_call_frame: bool = is_call_frame
        # Profondità lessicale: conta solo i frame di chiamata di funzione
        if parent is None:
            self.lex_depth: int = 0
        elif is_call_frame:
            self.lex_depth = parent.lex_depth + 1
        else:
            self.lex_depth = parent.lex_depth
        # Link per i record di attivazione (popolati da Interpreter._apply)
        self.dynamic_link: Optional[Env] = None   # ambiente del chiamante
        self.static_link:  Optional[Env] = None   # ambiente lessicale catturato

    # -- Operazioni principali --

    def lookup(self, name: str):
        """Cerca una variabile risalendo la catena di scope."""
        value, _, _ = self.lookup_with_origin(name)
        return value

    def lookup_with_origin(self, name: str):
        """
        Cerca una variabile risalendo la catena di scope e restituisce:
        (value, frame_label, depth)
        depth=0 significa frame corrente.
        """
        depth = 0
        current = self
        while current is not None:
            if name in current.bindings:
                label = current.label or "scope"
                return current.bindings[name], label, depth
            current = current.parent
            depth += 1
        raise NameError(f"Variable '{name}' not found")

    def update(self, name: str, value):
        """Aggiorna una variabile esistente (la cerca nella catena)."""
        if name in self.bindings:
            self.bindings[name] = value
        elif self.parent is not None:
            self.parent.update(name, value)
        else:
            raise NameError(f"Variable '{name}' not found for update")

    def define(self, name: str, value):
        """Definisce una nuova variabile nel frame corrente."""
        self.bindings[name] = value

    # -- Visualizzazione --

    def show(self, level: int = 0) -> str:
        """Rappresentazione visuale della catena di scope (per il debug)."""
        pad = "    " * level
        lines = [f"{pad}┌─ [{self.label or 'scope'}]"]
        for k, v in self.bindings.items():
            lines.append(f"{pad}│  {k} = {v!r}")
        if not self.bindings:
            lines.append(f"{pad}│  (empty)")
        lines.append(f"{pad}└{'─' * 14}")
        if self.parent is not None:
            lines.append(self.parent.show(level + 1))
        return "\n".join(lines)

    def frame_summary(self) -> str:
        """Riepilogo breve del frame corrente."""
        if not self.bindings:
            return f"{self.label or 'scope'}{{}}"
        pairs = ", ".join(f"{k}={v!r}" for k, v in self.bindings.items())
        return f"{self.label or 'scope'}{{{pairs}}}"

    def chain_summary(self, max_frames: int = 6) -> str:
        """Riepilogo compatto della catena di scope."""
        frames = []
        cur = self
        while cur is not None and len(frames) < max_frames:
            frames.append(cur.frame_summary())
            cur = cur.parent
        if cur is not None:
            frames.append("...")
        return " -> ".join(frames)

    def __repr__(self):
        return f"Env({list(self.bindings.keys())})"


# ════════════════════════════════════════════════════════════════
# PARTE 4 — INTERPRETER
#
# Visita l'AST in modo ricorsivo (pattern "visitor").
# La configurazione (scoping, passing) cambia il comportamento
# senza modificare il codice dei nodi.
# ════════════════════════════════════════════════════════════════

class Interpreter:
    """
    Interprete didattico configurabile.

    Parametri
    ---------
    scoping : 'static'    → scoping lessicale (Python, Java, ...)
              'dynamic'   → scoping dinamico  (Bash, EMACS Lisp, ...)

    passing : 'value'     → copia del valore  (default in quasi tutti i linguaggi)
              'reference' → alias alla variabile originale (C++, Pascal ref)
              'name'      → espressione rivalutata ad ogni uso  (ALGOL 60)

    binding : 'shallow'   → (solo con dynamic) la funzione passata come argomento
                            viene chiamata nell'env dinamico del momento della chiamata
              'deep'      → (solo con dynamic) la funzione passata come argomento
                            cattura l'env del momento del passaggio (funarg problem)
              Nota: con scoping='static' il binding è sempre deep per definizione
                    (le funzioni sono già Closure che catturano alla definizione).

    let_scope    : True  → Let crea un nuovo scope (stile funzionale / lessicale)
                   False → Let dichiara la variabile nel frame corrente, senza creare
                           un nuovo ambiente (stile imperativo: C, Java, Python, ...)

    debug        : False → solo risultato finale
                   True  → mostra ogni chiamata di funzione e i relativi ambienti

    show_ar      : True  → visualizza il Record di Attivazione ad ogni chiamata
    show_display : True  → visualizza il Display (depth → AR corrente) ad ogni chiamata
    """

    def __init__(
        self,
        scoping: str = 'static',
        passing: str = 'value',
        binding: str = 'shallow',
        let_scope: bool = False,
        debug: bool = False,
        show_ar: bool = False,
        show_display: bool = False,
    ):
        if scoping not in ('static', 'dynamic'):
            raise ValueError("scoping must be 'static' or 'dynamic'")
        if passing not in ('value', 'reference', 'name'):
            raise ValueError("passing must be 'value', 'reference', or 'name'")
        if binding not in ('shallow', 'deep'):
            raise ValueError("binding must be 'shallow' or 'deep'")

        self.scoping = scoping
        self.passing = passing
        self.binding = binding
        self.let_scope = let_scope
        self.debug = debug
        self.show_ar = show_ar
        self.show_display = show_display
        self._step = 0
        self._call_depth = 0
        self._call_id = 0
        self._display: dict = {}     # depth → Env (AR più recente a quella profondità)
        self._ar_stack: list = []    # stack degli AR attivi

    # ── Metodo principale ─────────────────────────────────────────

    def eval(self, expr, env: Env):
        """
        Valuta un'espressione nell'environment dato e restituisce il valore.
        È il cuore dell'interprete: dispatch sul tipo di nodo.
        """
        self._step += 1

        if isinstance(expr, Num):
            return expr.value

        elif isinstance(expr, Var):
            return self._eval_var(expr, env)

        elif isinstance(expr, BinOp):
            return self._eval_binop(expr, env)

        elif isinstance(expr, Let):
            return self._eval_let(expr, env)

        elif isinstance(expr, Fun):
            return self._eval_fun(expr, env)

        elif isinstance(expr, Call):
            return self._eval_call(expr, env)

        elif isinstance(expr, If):
            return self._eval_if(expr, env)

        elif isinstance(expr, Assign):
            return self._eval_assign(expr, env)

        elif isinstance(expr, Seq):
            return self._eval_seq(expr, env)

        else:
            raise TypeError(f"Unknown AST node: {type(expr).__name__}")

    # ── Valutazione dei singoli nodi ──────────────────────────────

    def _eval_var(self, expr: Var, env: Env):
        val, frame_label, depth = env.lookup_with_origin(expr.name)
        indent = "  " * self._call_depth

        if isinstance(val, Ref):
            # Passaggio per riferimento: la variabile è una cella mutabile,
            # la dereferenziamo in modo trasparente.
            if self.debug:
                print(f"{indent}  lookup  {expr.name} = {val.value!r}"
                      f"  [ref condiviso, da '{frame_label}']")
            return val.value

        elif isinstance(val, Thunk):
            # Passaggio per nome: valutiamo l'espressione sospesa ORA,
            # nell'ambiente del chiamante (catturato nel thunk).
            if self.debug:
                print(f"{indent}  lookup  {expr.name} → thunk  [per nome, da '{frame_label}']")
                print(f"{indent}         rivaluto: {val.expr}")
            result = self.eval(val.expr, val.env)
            if self.debug:
                print(f"{indent}         risultato: {result!r}")
            return result

        if self.debug:
            if isinstance(expr, FunName):
                print(f"\n{indent}→ {expr.name}()  [da '{frame_label}']")
            else:
                print(f"{indent}  lookup  {expr.name} = {val!r}  [da '{frame_label}']")

        return val

    def _eval_binop(self, expr: BinOp, env: Env):
        left = self.eval(expr.left, env)
        right = self.eval(expr.right, env)
        if expr.op == '+': return left + right
        if expr.op == '-': return left - right
        if expr.op == '*': return left * right
        if expr.op == '/':
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
        raise ValueError(f"Unknown operator: '{expr.op}'")

    def _eval_let(self, expr: Let, env: Env):
        # Valuta il valore nell'ambiente corrente
        val = self.eval(expr.value, env)
        if self.let_scope:
            # Stile FUNZIONALE: crea un nuovo scope visibile solo nel body.
            # La variabile non esiste fuori dall'espressione let.
            new_env = Env(parent=env, label=f"let {expr.name}")
            new_env.define(expr.name, val)
            return self.eval(expr.body, new_env)
        else:
            # Stile IMPERATIVO: dichiara la variabile nel frame corrente.
            # La variabile resta accessibile anche dopo il body (come in C/Java/Python).
            env.define(expr.name, val)
            return self.eval(expr.body, env)

    def _eval_fun(self, expr: Fun, env: Env):
        if self.scoping == 'static':
            # SCOPING STATICO: cattura l'ambiente corrente nella closure.
            # Il body della funzione "ricorderà" questo ambiente.
            return Closure(expr.params, expr.body, env)
        else:
            # SCOPING DINAMICO: non cattura nulla.
            # L'ambiente sarà quello di chi chiamerà la funzione.
            return DynFunction(expr.params, expr.body)

    def _eval_call(self, expr: Call, env: Env):
        func = self.eval(expr.func, env)
        if not isinstance(func, (Closure, DynFunction, DynClosure)):
            raise TypeError(f"'{func!r}' is not a function")
        return self._apply(func, expr.args, env)

    def _debug_show_env_chain(self, env: Env, indent: str, origin: str = "") -> None:
        """Mostra la catena degli ambienti come albero annidato con | (per il debug)."""
        SEP = "─" * 28
        visible: dict = {}  # nome → (valore, frame) — prima occorrenza vince

        cur = env
        pipe = ""   # prefisso che cresce: "", "|  ", "|  |  ", ...
        is_first = True

        while cur is not None:
            label = cur.label or "scope"
            p = indent + "  " + pipe  # prefisso completo per questo livello

            if is_first:
                suffix = f"  ({origin})" if origin else ""
                print(f"{p}{label}{suffix}")
                is_first = False
            else:
                print(f"{p}{label}")

            print(f"{p}{SEP}")

            if cur.bindings:
                for k, v in cur.bindings.items():
                    print(f"{p}  {k} = {v!r}")
                    if k not in visible:
                        visible[k] = (v, label)
            else:
                print(f"{p}  (vuoto)")

            cur = cur.parent
            if cur is not None:
                pipe += "|  "
                print(f"{indent}  {pipe.rstrip()}")  # riga con solo i | come connettore

        # Riepilogo piatto: mostra solo le variabili effettivamente accessibili
        if visible:
            print(f"{indent}  {'┈' * 17}")
            print(f"{indent}  visibile da qui:")
            for k, (v, src) in visible.items():
                print(f"{indent}    {k} = {v!r}  [da '{src}']")
        print()

    def _print_ar(self, frame: Env, indent: str = "") -> None:
        """Visualizza un Record di Attivazione come box ╔═╗."""
        W = 56
        label = frame.label or "frame"
        depth = frame.lex_depth

        print(f"\n{indent}  ╔═ Record di Attivazione {'═' * (W - 24)}╗")
        title = f"  {label}   [profondità lessicale: {depth}]"
        print(f"{indent}  ║{title:<{W}}║")
        print(f"{indent}  ╠{'═' * W}╣")

        # Variabili locali (parametri)
        print(f"{indent}  ║{'  variabili locali:':<{W}}║")
        if frame.bindings:
            for k, v in frame.bindings.items():
                if isinstance(v, Ref):
                    vstr = f"→ {v.value!r}  (ref condiviso)"
                elif isinstance(v, Thunk):
                    vstr = f"⟨thunk: {v.expr}⟩  (per nome)"
                else:
                    vstr = repr(v)
                line = f"    {k} = {vstr}"
                if len(line) > W:
                    line = line[:W - 3] + "..."
                print(f"{indent}  ║{line:<{W}}║")
        else:
            print(f"{indent}  ║{'    (nessuna)':<{W}}║")

        print(f"{indent}  ╠{'═' * W}╣")

        # Static link
        if frame.static_link is not None:
            sl = frame.static_link
            sl_label = sl.label or "scope"
            summary = ", ".join(f"{k}={v!r}" for k, v in sl.bindings.items()) or "vuoto"
            line = f"  static link  → [{sl_label}]  depth={sl.lex_depth}  {{{summary}}}"
            if len(line) > W:
                line = line[:W - 3] + "..."
            print(f"{indent}  ║{line:<{W}}║")
        else:
            print(f"{indent}  ║{'  static link  → assente  (scoping dinamico shallow)':<{W}}║")

        # Dynamic link
        if frame.dynamic_link is not None:
            dl = frame.dynamic_link
            dl_label = dl.label or "scope"
            line = f"  dynamic link → [{dl_label}]  depth={dl.lex_depth}  (chiamante)"
            if len(line) > W:
                line = line[:W - 3] + "..."
            print(f"{indent}  ║{line:<{W}}║")
        else:
            print(f"{indent}  ║{'  dynamic link → (chiamata dal livello globale)':<{W}}║")

        print(f"{indent}  ╚{'═' * W}╝")

    def _print_display(self, indent: str = "") -> None:
        """Visualizza il Display corrente come tabella ╔═╗."""
        if not self._display:
            return
        W = 56
        max_depth = max(self._display.keys())
        print(f"\n{indent}  ╔═ Display {'═' * (W - 9)}╗")
        for d in range(max_depth + 1):
            if d in self._display:
                frame = self._display[d]
                label = frame.label or "scope"
                bindings = ", ".join(f"{k}={v!r}" for k, v in frame.bindings.items()) or "vuoto"
                cell = f"  [{d}]  {label:<28}  {{{bindings}}}"
                if len(cell) > W:
                    cell = cell[:W - 3] + "..."
                print(f"{indent}  ║{cell:<{W}}║")
            else:
                print(f"{indent}  ║{'  [' + str(d) + ']  (nessun AR attivo)':<{W}}║")
        print(f"{indent}  ╚{'═' * W}╝")

    def _apply(self, func, args: list, call_env: Env):
        """
        Applica una funzione agli argomenti.

        Qui si decidono tre cose fondamentali:
          1. Quale ambiente "eredita" il frame della funzione?
             → Dipende da SCOPING e BINDING
          2. Come vengono passati gli argomenti?
             → Dipende da PASSING
          3. Le funzioni passate come argomenti catturano l'env ora?
             → Dipende da BINDING (shallow vs deep)
        """
        params = func.params

        if len(params) != len(args):
            raise TypeError(
                f"Function expects {len(params)} argument(s), "
                f"got {len(args)}"
            )

        # ── 1. Scelta dell'ambiente padre del frame locale ──────────
        if isinstance(func, Closure):
            # STATIC: il body vede l'ambiente catturato alla DEFINIZIONE
            parent_env = func.env
            origin = "definition (static)"
        elif isinstance(func, DynClosure):
            # DYNAMIC + DEEP: il body vede l'ambiente catturato al PASSAGGIO
            parent_env = func.env
            origin = "passing time (dynamic deep)"
        else:
            # DYNAMIC + SHALLOW: il body vede l'ambiente di CHIAMATA
            parent_env = call_env
            origin = "call site (dynamic shallow)"

        param_str = ", ".join(params) if params else "∅"
        local_env = Env(parent=parent_env, label=f"call frame ({param_str})",
                        is_call_frame=True)

        # ── 2. Passaggio dei parametri ──────────────────────────────
        for param, arg_expr in zip(params, args):

            if self.passing == 'value':
                # Valuta l'argomento e passa una COPIA del valore.
                # Modifiche al parametro non influenzano il chiamante.
                val = self.eval(arg_expr, call_env)

                # ── 3. Deep binding: se stiamo passando una funzione
                #       dinamica come argomento, catturiamo l'env ora.
                if (self.scoping == 'dynamic'
                        and self.binding == 'deep'
                        and isinstance(val, DynFunction)):
                    val = DynClosure(val.params, val.body, call_env)
                    if self.debug:
                        indent = "  " * self._call_depth
                        print(f"{indent}  [DEEP] parametro '{param}' cattura env di passaggio")

                local_env.define(param, val)

            elif self.passing == 'reference':
                # Passa una CELLA CONDIVISA con il chiamante.
                # Modifiche al parametro si riflettono sulla variabile originale.
                ref = self._make_ref(arg_expr, call_env)
                local_env.define(param, ref)

            elif self.passing == 'name':
                # Passa un THUNK: l'espressione viene rivalutata ad ogni uso.
                # La valutazione avviene nell'ambiente del chiamante.
                thunk = Thunk(arg_expr, call_env)
                local_env.define(param, thunk)

        # ── 3. Metadati AR: link dinamico e statico ─────────────────
        local_env.dynamic_link = call_env
        if isinstance(func, (Closure, DynClosure)):
            local_env.static_link = func.env

        # ── 4. Aggiorna display e stack AR ───────────────────────────
        depth = local_env.lex_depth
        old_display_entry = self._display.get(depth)
        self._display[depth] = local_env
        self._ar_stack.append(local_env)

        # ── 5. Output (debug / AR / display) ────────────────────────
        call_id = None
        indent = "  " * self._call_depth
        if self.debug:
            self._call_id += 1
            call_id = self._call_id
            config = f"scoping={self.scoping}, passing={self.passing}"
            if self.scoping == 'dynamic':
                config += f", binding={self.binding}"
            print(f"\n{indent}▶ Call #{call_id}  [{config}]")
            self._debug_show_env_chain(local_env, indent, origin=origin)

        if self.show_ar:
            self._print_ar(local_env, indent)
        if self.show_display:
            self._print_display(indent)

        # ── 6. Esecuzione del corpo ──────────────────────────────────
        self._call_depth += 1
        try:
            result = self.eval(func.body, local_env)
        finally:
            self._call_depth -= 1
            self._ar_stack.pop()
            # Ripristina il display al valore precedente
            if old_display_entry is not None:
                self._display[depth] = old_display_entry
            else:
                self._display.pop(depth, None)

        if self.debug:
            indent = "  " * self._call_depth
            print(f"{indent}◀ Return #{call_id} → {result!r}")

        return result

    def _make_ref(self, arg_expr, env: Env) -> Ref:
        """
        Per il passaggio per riferimento:
        - Se l'argomento è una variabile, condivide la sua cella con il chiamato.
        - Se la variabile non è ancora una cella mutabile, la converte.
        - Solo variabili possono essere passate per riferimento (non espressioni).
        """
        if not isinstance(arg_expr, Var):
            raise TypeError(
                f"Pass-by-reference requires a variable, not '{arg_expr}'"
            )

        current = env.lookup(arg_expr.name)

        if isinstance(current, Ref):
            # La variabile è già una cella mutabile: condividiamo la stessa
            return current
        else:
            # Creiamo una nuova cella e aggiorniamo il binding del chiamante
            # in modo che punti alla stessa cella del chiamato
            ref = Ref(current)
            env.update(arg_expr.name, ref)
            return ref

    def _eval_if(self, expr: If, env: Env):
        cond = self.eval(expr.cond, env)
        if cond:
            return self.eval(expr.then_, env)
        else:
            return self.eval(expr.else_, env)

    def _eval_assign(self, expr: Assign, env: Env):
        """
        Assegnamento a una variabile esistente.

        Comportamento speciale:
        - Se la variabile contiene un Ref (pass-by-ref),
          modifica il valore DENTRO la cella → visibile anche al chiamante.
        - Altrimenti, aggiorna il binding normalmente.
        """
        new_val = self.eval(expr.value, env)
        current = env.lookup(expr.name)

        if isinstance(current, Ref):
            # Aggiorna la cella condivisa (effetto visibile al chiamante!)
            if self.debug:
                indent = "  " * self._call_depth
                print(f"{indent}  [REF] {expr.name}: {current.value!r} -> {new_val!r}")
            current.value = new_val
        else:
            env.update(expr.name, new_val)

        return new_val

    def _eval_seq(self, expr: Seq, env: Env):
        result = None
        for e in expr.exprs:
            result = self.eval(e, env)
        return result

    # ── Configurazione a runtime ──────────────────────────────────

    def set_scoping(self, mode: str):
        """Cambia la modalità di scoping durante l'esecuzione."""
        if mode not in ('static', 'dynamic'):
            raise ValueError("Valid values: 'static', 'dynamic'")
        self.scoping = mode
        print(f"[CONFIG] Scoping → {mode}")

    def set_passing(self, mode: str):
        """Cambia la modalità di passaggio parametri durante l'esecuzione."""
        if mode not in ('value', 'reference', 'name'):
            raise ValueError("Valid values: 'value', 'reference', 'name'")
        self.passing = mode
        print(f"[CONFIG] Passing → {mode}")

    def set_binding(self, mode: str):
        """Cambia la modalità di binding (solo rilevante con scoping='dynamic')."""
        if mode not in ('shallow', 'deep'):
            raise ValueError("Valid values: 'shallow', 'deep'")
        self.binding = mode
        print(f"[CONFIG] Binding → {mode}")

    def set_debug(self, enabled: bool = True):
        """Abilita o disabilita la modalità debug."""
        self.debug = enabled

    # ── Punto di ingresso ─────────────────────────────────────────

    def run(self, program, global_env: Optional[Env] = None):
        """
        Esegue un programma a partire da un environment globale vuoto.
        Stampa la configurazione e il risultato finale.
        """
        self._step = 0
        self._call_depth = 0
        self._call_id = 0
        self._display = {}
        self._ar_stack = []
        if global_env is None:
            global_env = Env(label="Ambiente globale")
        self._display[0] = global_env   # depth 0 = scope globale

        binding_info = self.binding if self.scoping == 'dynamic' else 'n/a (static)'
        let_info = 'funzionale (nuovo scope)' if self.let_scope else 'imperativo (frame corrente)'
        print("┌" + "─" * 48 + "┐")
        print("│  INTERPRETE DIDATTICO                          │")
        print(f"│  Scoping: {self.scoping:<39}│")
        print(f"│  Passing: {self.passing:<39}│")
        print(f"│  Binding: {binding_info:<39}│")
        print(f"│  Let:     {let_info:<39}│")
        print(f"│  Debug:   {'on' if self.debug else 'off':<39}│")
        if self.show_ar:
            print(f"│  AR:      on                                     │")
        if self.show_display:
            print(f"│  Display: on                                     │")
        print("└" + "─" * 48 + "┘")

        result = self.eval(program, global_env)

        print(f"\n  ➜  Result: {result!r}")
        print("─" * 50)
        return result
