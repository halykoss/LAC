"""
Esempi Didattici (versione modulare)
====================================

Obiettivo: fornire agli studenti un percorso graduale su:
  1) scoping
  2) passaggio parametri
  3) shallow/deep binding (solo dinamico)

Uso:
  python esempi.py                          # mostra catalogo ed esegue tutto
  python esempi.py list                     # solo catalogo
  python esempi.py classic_scoping          # singolo esempio
  python esempi.py classic_scoping --debug  # con debug
  python esempi.py classic_scoping --ar     # con record di attivazione
  python esempi.py classic_scoping --display  # con display
  python esempi.py classic_scoping --ar --display --debug  # tutto insieme
"""

import argparse

from esempi_didattici import (
    classic_scoping,
    nested_scoping,
    simple_passing,
    swap_passing,
    name_passing_effects,
    name_passing_multiple_evals,
    shallow_vs_deep_binding,
    binding_nested,
    debug_example,
    full_comparison,
    EXAMPLES,
    run_all,
    run_example,
)


def print_catalog():
    print("\nCatalogo esempi (ordine consigliato):")
    print("  1. classic_scoping")
    print("  2. simple_passing")
    print("  3. swap_passing")
    print("  4. nested_scoping")
    print("  5. name_passing_effects")
    print("  6. name_passing_multiple_evals")
    print("  7. shallow_vs_deep_binding")
    print("  8. binding_nested")
    print("  9. debug_example")
    print(" 10. full_comparison")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Interprete Didattico LAC — esegui gli esempi',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
esempi:
  python esempi.py
  python esempi.py list
  python esempi.py classic_scoping
  python esempi.py classic_scoping --debug
  python esempi.py classic_scoping --ar
  python esempi.py classic_scoping --display
  python esempi.py classic_scoping --ar --display --debug
        """
    )
    parser.add_argument('name', nargs='?', default=None,
                        help='nome dell\'esempio (ometti per eseguire tutti)')
    parser.add_argument('--debug',   action='store_true',
                        help='mostra la catena degli ambienti passo-passo')
    parser.add_argument('--ar',      action='store_true',
                        help='mostra i Record di Attivazione ad ogni chiamata')
    parser.add_argument('--display', action='store_true',
                        help='mostra il Display (depth → AR) ad ogni chiamata')

    args = parser.parse_args()

    if args.name is None:
        print_catalog()
        print("\nEseguo tutti gli esempi...\n")
        run_all()
    elif args.name == 'list':
        print_catalog()
    elif args.name in EXAMPLES:
        run_example(args.name, debug=args.debug,
                    show_ar=args.ar, show_display=args.display)
    else:
        print(f"Esempio '{args.name}' non trovato.")
        print("Usa 'python esempi.py list' per il catalogo.")
