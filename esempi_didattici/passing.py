"""Esempi su passaggio per valore, riferimento e nome."""

from interprete import (
    Interpreter,
    Num, Var, BinOp, Let, Fun, FunName, Call, Assign, Seq,
)

from .utils import header, section


def simple_passing(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """double(x): cambia x oppure no?"""
    header(
        "PASSAGGIO: valore vs riferimento vs nome",
        "double(x) modifica x?"
    )

    program = Let('x', Num(5),
               Let('double', Fun(['n'],
                       Assign('n', BinOp('*', Var('n'), Num(2)))),
                Seq([
                    Call(FunName('double'), [Var('x')]),
                    Var('x')
                ])))

    print("\n  Pseudo-codice:")
    print("    x = 5")
    print("    double = fun(n) { n = n * 2 }")
    print("    double(x)")
    print("    x")

    section("Passaggio per VALORE")
    print("  → x rimane 5")
    Interpreter(passing='value', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Passaggio per RIFERIMENTO")
    print("  → x diventa 10")
    Interpreter(passing='reference', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Passaggio per NOME")
    print("  → x rimane 5")
    Interpreter(passing='name', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)


def swap_passing(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """swap(a, b): funziona solo con passaggio per riferimento."""
    header(
        "PASSAGGIO: swap",
        "Lo swap modifica davvero le variabili del chiamante?"
    )

    swap_body = Seq([
        Let('tmp', Var('x'),
            Seq([
                Assign('x', Var('y')),
                Assign('y', Var('tmp'))
            ]))
    ])

    program = Let('a', Num(10),
               Let('b', Num(20),
                Let('swap', Fun(['x', 'y'], swap_body),
                 Seq([
                     Call(FunName('swap'), [Var('a'), Var('b')]),
                     BinOp('+',
                         BinOp('*', Var('a'), Num(100)),
                         Var('b'))
                 ]))))

    print("\n  Pseudo-codice:")
    print("    a = 10, b = 20")
    print("    swap = fun(x, y) { tmp=x; x=y; y=tmp }")
    print("    swap(a, b)")
    print("    a*100 + b")

    section("Passaggio per VALORE")
    print("  → 1020 (nessuno scambio reale)")
    Interpreter(passing='value', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Passaggio per RIFERIMENTO")
    print("  → 2010 (scambio riuscito)")
    Interpreter(passing='reference', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)


def name_passing_effects(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """Effetto Jensen: il lato effetto cambia l'argomento sotto passaggio per nome."""
    header(
        "PASSAGGIO PER NOME: effetto collaterale",
        "f(n * 10) cambia risultato tra value e name"
    )

    program = Let('n', Num(1),
               Let('f', Fun(['x'],
                       Seq([
                           Assign('n', Num(0)),
                           Var('x')
                       ])),
                Call(FunName('f'), [BinOp('*', Var('n'), Num(10))])))

    print("\n  Pseudo-codice:")
    print("    n = 1")
    print("    f = fun(x) { n = 0; return x }")
    print("    f(n * 10)")

    section("Passaggio per VALORE")
    print("  → Risultato atteso: 10")
    Interpreter(passing='value', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Passaggio per NOME")
    print("  → Risultato atteso: 0")
    Interpreter(passing='name', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)


def name_passing_multiple_evals(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """Con passaggio per nome l'argomento può essere valutato più volte."""
    header(
        "PASSAGGIO PER NOME: valutazioni multiple",
        "f(x)=x+x su f(inc())"
    )

    inc_body = Seq([
        Assign('count', BinOp('+', Var('count'), Num(1))),
        Var('count')
    ])

    f_body = BinOp('+', Var('x'), Var('x'))

    program = Let('count', Num(0),
               Let('inc', Fun([], inc_body),
                Let('f', Fun(['x'], f_body),
                 Call(FunName('f'), [Call(FunName('inc'), [])]))))

    print("\n  Pseudo-codice:")
    print("    count = 0")
    print("    inc = fun() { count = count + 1; return count }")
    print("    f   = fun(x) { x + x }")
    print("    f(inc())")

    section("Passaggio per VALORE")
    print("  → Risultato atteso: 2")
    Interpreter(passing='value', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Passaggio per NOME")
    print("  → Risultato atteso: 3")
    Interpreter(passing='name', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)
