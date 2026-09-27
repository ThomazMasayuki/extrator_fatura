"""Formatação no padrão brasileiro."""
from __future__ import annotations

import re
from datetime import date


def brl(v: float | None, sinal: bool = False) -> str:
    if v is None:
        return "—"
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    pref = "−" if v < 0 else ("+" if sinal and v > 0 else "")
    return f"{pref}R$ {s}"


def brl_curto(v: float) -> str:
    a = abs(v)
    if a >= 1_000_000:
        return f"R$ {v / 1_000_000:.1f} mi".replace(".", ",")
    if a >= 10_000:
        return f"R$ {v / 1_000:.0f} mil"
    if a >= 1_000:
        return f"R$ {v / 1_000:.1f} mil".replace(".", ",")
    return f"R$ {v:.0f}"


def data_br(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "—"


def cartao(numero: str | None) -> str:
    dig = re.sub(r"\D", "", numero or "")
    return f"•••• {dig[-4:]}" if len(dig) >= 4 else (numero or "—")


def ler_brl(txt: str) -> float:
    t = txt.strip().replace("R$", "").replace(" ", "")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    return float(t)


def plural(n: int, singular: str, plural_: str | None = None) -> str:
    return f"{n} {singular if n == 1 else (plural_ or singular + 's')}"
