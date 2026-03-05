"""Esempi di debug e confronto completo delle combinazioni."""

from interprete import (
    Interpreter,
    Num, Var, BinOp, Let, Fun, FunName, Call,
)

from .utils import header, section


def debug_example(show_ar: bool = False, show_display: bool = False):
    """Esempio minimo per mostrare debug=True."""
    header(
        "MODALITÀ DEBUG",
        "Visualizzazione degli ambienti durante l'esecuzione"
    )

    program = Let('x', Num(10),
               Let('f', Fun(['a'],
                       BinOp('+', Var('a'), Var('x'))),
                Call(FunName('f'), [Num(5)])))

    print("\n  Programma:")
    print("    x = 10")
    print("    f = fun(a) { a + x }")
    print("    f(5)")

    section("Esecuzione con debug=True")
    Interpreter(scoping='static', passing='value', debug=True,
                show_ar=show_ar, show_display=show_display).run(program)


def full_comparison(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """Confronta tutte le combinazioni scoping x passing su un unico programma."""
    header(
        "CONFRONTO COMPLETO",
        "Stesso programma, tutte le combinazioni scoping x passing"
    )

    f_body = BinOp('+', Var('arg'), Var('x'))
    g_body = Let('x', Num(100), Call(FunName('f'), [Var('n')]))

    program = Let('x', Num(1),
               Let('n', Num(10),
                Let('f', Fun(['arg'], f_body),
                 Let('g', Fun([], g_body),
                  Call(FunName('g'), [])))))

    print("\n  Pseudo-codice:")
    print("    x = 1")
    print("    n = 10")
    print("    f = fun(arg) { arg + x }")
    print("    g = fun() { let x = 100 in f(n) }")
    print("    g()")

    results = {}
    for scoping in ('static', 'dynamic'):
        for passing in ('value', 'reference', 'name'):
            interp = Interpreter(scoping=scoping, passing=passing, debug=debug,
                                 show_ar=show_ar, show_display=show_display)
            print(f"\n  [{scoping.upper()} + {passing.upper()}]")
            results[(scoping, passing)] = interp.run(program)

    print("\n  Risultati:")
    for (sc, pa), result in results.items():
        print(f"  - {sc:>7} + {pa:>9} => {result}")
