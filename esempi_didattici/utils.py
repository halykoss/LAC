"""Utility di stampa usate da tutti gli esempi."""


def header(title: str, subtitle: str = ""):
    print("\n" + "═" * 60)
    print(f"  {title}")
    if subtitle:
        print(f"  {subtitle}")
    print("═" * 60)


def section(label: str = ""):
    print(f"\n{'─' * 60}")
    if label:
        print(f"  {label}")
    print("─" * 60)
