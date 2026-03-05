"""Esempi base di scoping statico vs dinamico."""

from interprete import (
    Interpreter,
    Num, Var, BinOp, Let, Fun, FunName, Call, Assign, Seq,
)

from .utils import header, section


def classic_scoping(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """
    Esempio classico:
      x = 10
      f = fun() { x }
      g = fun() { let x = 20 in f() }
      g()
    """
    header(
        "SCOPING: statico vs dinamico",
        "Quale 'x' vede la funzione f() quando è chiamata da g()?"
    )

    program = Let('x', Num(10),
               Let('f', Fun([], Var('x')),
                Let('g', Fun([],
                        Let('x', Num(20),
                            Call(FunName('f'), []))),
                 Call(FunName('g'), []))))

    print("\n  Pseudo-codice:")
    print("    x = 10")
    print("    f = fun() { return x }")
    print("    g = fun() { x = 20; return f() }")
    print("    g()")

    if debug:
        section("Come leggere il debug (guida rapida)")
        print("  1) Cerca 'CALL #2': e' la chiamata a f().")
        print("  2) Guarda la catena dei frame subito sotto.")
        print("  3) Se compare prima 'let x = 20', allora f vede 20 (dinamico).")
        print("  4) Se la catena parte da 'let x = 10', allora f vede 10 (statico).")

    section("Scoping STATICO (lessicale)")
    print("  → f cattura x=10 alla definizione.")
    print("  → Risultato atteso: 10")
    static_result = Interpreter(scoping='static', debug=debug,
                                show_ar=show_ar, show_display=show_display).run(program)
    print(f"  [Conferma] statico: ottenuto {static_result}, atteso 10")

    section("Scoping DINAMICO")
    print("  → f usa l'ambiente della chiamata.")
    print("  → Risultato atteso: 20")
    dynamic_result = Interpreter(scoping='dynamic', debug=debug,
                                 show_ar=show_ar, show_display=show_display).run(program)
    print(f"  [Conferma] dinamico: ottenuto {dynamic_result}, atteso 20")


def nested_scoping(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """
    Esempio annidato:
      x = 1
      f(y) = { x = x + y; x }
      g()  = { let x=100 in f(5) }
      f(10) + g()
    """
    header(
        "SCOPING: funzioni annidate",
        "f modifica x: cambia tra statico e dinamico"
    )

    f_body = Seq([
        Assign('x', BinOp('+', Var('x'), Var('y'))),
        Var('x')
    ])

    g_body = Let('x', Num(100),
                 Call(FunName('f'), [Num(5)]))

    program = Let('x', Num(1),
               Let('f', Fun(['y'], f_body),
                Let('g', Fun([], g_body),
                 BinOp('+',
                     Call(FunName('f'), [Num(10)]),
                     Call(FunName('g'), [])))))

    print("\n  Pseudo-codice:")
    print("    x = 1")
    print("    f = fun(y) { x = x + y; return x }")
    print("    g = fun()  { let x = 100; return f(5) }")
    print("    f(10) + g()")

    section("Scoping STATICO")
    print("  → f vede sempre la x globale.")
    print("  → Risultato atteso: 27")
    Interpreter(scoping='static', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Scoping DINAMICO")
    print("  → in g(), f vede la x locale (100).")
    print("  → Risultato atteso: 116")
    Interpreter(scoping='dynamic', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)
