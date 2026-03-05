"""Pacchetto di esempi didattici organizzati per argomento."""

from .scoping import classic_scoping, nested_scoping
from .passing import (
    simple_passing,
    swap_passing,
    name_passing_effects,
    name_passing_multiple_evals,
)
from .binding import shallow_vs_deep_binding, binding_nested
from .debug_compare import debug_example, full_comparison
from .runner import EXAMPLES, run_all, run_example

__all__ = [
    'classic_scoping',
    'nested_scoping',
    'simple_passing',
    'swap_passing',
    'name_passing_effects',
    'name_passing_multiple_evals',
    'shallow_vs_deep_binding',
    'binding_nested',
    'debug_example',
    'full_comparison',
    'EXAMPLES',
    'run_all',
    'run_example',
]
