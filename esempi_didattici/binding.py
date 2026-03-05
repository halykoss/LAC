"""Esempi su shallow/deep binding con scoping dinamico."""

from interprete import (
    Interpreter,
    Num, Var, Let, Fun, FunName, Call,
)

from .utils import header, section


def shallow_vs_deep_binding(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """
    x = 1
    f = fun() { x }
    apply = fun(g) { let x = 2 in g() }
    apply(f)
    """
    header(
        "BINDING: shallow vs deep",
        "Con scoping dinamico, quale ambiente usa la funzione passata?"
    )

    program = Let('x', Num(1),
               Let('f', Fun([], Var('x')),
                Let('apply', Fun(['g'],
                        Let('x', Num(2),
                            Call(FunName('g'), []))),
                 Call(FunName('apply'), [FunName('f')]))))

    print("\n  Pseudo-codice:")
    print("    x = 1")
    print("    f = fun() { return x }")
    print("    apply = fun(g) { let x = 2 in g() }")
    print("    apply(f)")

    section("Scoping STATICO")
    print("  → Risultato atteso: 1")
    Interpreter(scoping='static', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Scoping DINAMICO + Shallow Binding")
    print("  → Risultato atteso: 2")
    Interpreter(scoping='dynamic', binding='shallow', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Scoping DINAMICO + Deep Binding")
    print("  → Risultato atteso: 1")
    Interpreter(scoping='dynamic', binding='deep', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)


def binding_nested(debug: bool = False, show_ar: bool = False, show_display: bool = False):
    """
    x = 0
    f = fun() { x }
    wrapper = fun(g) { let x = 10 in g() }
    let x = 99 in wrapper(f)
    """
    header(
        "BINDING: esempio annidato",
        "x alla definizione=0, nel wrapper=10, al passaggio=99"
    )

    program = Let('x', Num(0),
               Let('f', Fun([], Var('x')),
                Let('wrapper', Fun(['g'],
                        Let('x', Num(10),
                            Call(FunName('g'), []))),
                 Let('x', Num(99),
                  Call(FunName('wrapper'), [FunName('f')])))))

    print("\n  Pseudo-codice:")
    print("    x = 0")
    print("    f = fun() { return x }")
    print("    wrapper = fun(g) { let x = 10 in g() }")
    print("    let x = 99 in wrapper(f)")

    section("Scoping STATICO")
    print("  → Risultato atteso: 0")
    Interpreter(scoping='static', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Scoping DINAMICO + Shallow Binding")
    print("  → Risultato atteso: 10")
    Interpreter(scoping='dynamic', binding='shallow', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)

    section("Scoping DINAMICO + Deep Binding")
    print("  → Risultato atteso: 99")
    Interpreter(scoping='dynamic', binding='deep', debug=debug,
                show_ar=show_ar, show_display=show_display).run(program)
