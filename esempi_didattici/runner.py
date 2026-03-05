"""Catalogo e funzioni di esecuzione esempi."""

import inspect

from .scoping import classic_scoping, nested_scoping
from .passing import (
    simple_passing,
    swap_passing,
    name_passing_effects,
    name_passing_multiple_evals,
)
from .binding import shallow_vs_deep_binding, binding_nested
from .debug_compare import debug_example, full_comparison


EXAMPLES = {
    # Livello 1: concetti base
    'classic_scoping': classic_scoping,
    'simple_passing': simple_passing,
    'swap_passing': swap_passing,
    # Livello 2: casi con effetti
    'nested_scoping': nested_scoping,
    'name_passing_effects': name_passing_effects,
    'name_passing_multiple_evals': name_passing_multiple_evals,
    # Livello 3: avanzato (scoping dinamico)
    'shallow_vs_deep_binding': shallow_vs_deep_binding,
    'binding_nested': binding_nested,
    # Utility didattiche
    'debug_example': debug_example,
    'full_comparison': full_comparison,
}


ORDERED_EXAMPLES = [
    'classic_scoping',
    'simple_passing',
    'swap_passing',
    'nested_scoping',
    'name_passing_effects',
    'name_passing_multiple_evals',
    'shallow_vs_deep_binding',
    'binding_nested',
    'debug_example',
    'full_comparison',
]


def run_example(name: str, debug: bool = False, show_ar: bool = False,
                show_display: bool = False, technical_debug: bool = False):
    if name not in EXAMPLES:
        raise ValueError(f"Example '{name}' not found.")
    fn = EXAMPLES[name]
    params = inspect.signature(fn).parameters
    kwargs = {}
    if 'debug' in params:
        kwargs['debug'] = debug
    if 'show_ar' in params:
        kwargs['show_ar'] = show_ar
    if 'show_display' in params:
        kwargs['show_display'] = show_display
    if 'technical_debug' in params:
        kwargs['technical_debug'] = technical_debug
    if kwargs:
        return fn(**kwargs)
    return fn()


def run_all():
    for name in ORDERED_EXAMPLES:
        run_example(name, debug=False, show_ar=False, show_display=False)
