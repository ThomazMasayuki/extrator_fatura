"""Estado da sessão: faturas extraídas, ajustes do usuário e confirmação."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

import pandas as pd

from fatura_extractor import Fatura

from .fmt import brl

CONFIG = Path.home() / ".config" / "extrator-fatura.json"
RAIZ_PLANEJADOR = Path(__file__).resolve().parents[2]
TEM_PLANEJADOR = (RAIZ_PLANEJADOR / "atualizar.py").exists()
PASTA_PADRAO = RAIZ_PLANEJADOR / "dados" / "faturas" if TEM_PLANEJADOR else Path.home() / "Faturas"


def ler_config() -> dict:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def salvar_config(**kv) -> None:
    cfg = ler_config() | kv
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class ItemFatura:
    fatura: Fatura
    excluidos: set[int] = field(default_factory=set)   # índices do DataFrame
    total_manual: float | None = None
    confirmada: bool = False
    exportado: Path | None = None

    @property
    def nome(self) -> str:
        return self.fatura.arquivo.name

    @property
    def df(self) -> pd.DataFrame:
        return self.fatura.lancamentos

    @property
    def ativos(self) -> pd.DataFrame:
        return self.df.drop(index=list(self.excluidos), errors="ignore")

    @property
    def total(self) -> float | None:
        return self.total_manual if self.total_manual is not None else self.fatura.valor_total

    @property
    def compras(self) -> float:
        a = self.ativos
        return round(float(a.loc[a["Valor"] > 0, "Valor"].sum()), 2) if not a.empty else 0.0

    @property
    def creditos(self) -> float:
        a = self.ativos
        return round(float(a.loc[a["Valor"] < 0, "Valor"].sum()), 2) if not a.empty else 0.0

    @property
    def extraido(self) -> float:
        return round(self.compras + self.creditos, 2)

    @property
    def diferenca(self) -> float | None:
        return None if self.total is None else round(self.total - self.extraido, 2)

    @property
    def confere(self) -> bool:
        d = self.diferenca
        return d is not None and abs(d) <= 0.01

    @property
    def aderencia(self) -> float | None:
        """Soma extraída / total da fatura (1.0 = bate)."""
        if not self.total:
            return None
        return self.extraido / self.total

    def alternar(self, idx: int) -> None:
        self.excluidos.symmetric_difference_update({idx})
        self.confirmada = False

    def para_exportar(self) -> Fatura:
        avisos = [a for a in self.fatura.avisos if not a.startswith("Soma extraída difere")]
        if self.excluidos:
            avisos.append(f"{len(self.excluidos)} lançamento(s) excluído(s) manualmente na conferência.")
        if self.total_manual is not None:
            avisos.append("Total da fatura informado manualmente na conferência.")
        if self.diferenca is not None and not self.confere:
            avisos.append(f"Soma extraída difere do total em {brl(self.diferenca)} "
                          "— confirmado pelo usuário.")
        return replace(self.fatura, lancamentos=self.ativos.reset_index(drop=True),
                       valor_total=self.total, avisos=avisos)


@dataclass
class Sessao:
    pdfs: list[Path] = field(default_factory=list)
    senhas_pdf: dict[Path, str] = field(default_factory=dict)
    senhas_sessao: list[str] = field(default_factory=list)   # só em memória
    itens: list[ItemFatura] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)
    atual: int = 0

    def nova(self) -> None:
        self.pdfs.clear()
        self.senhas_pdf.clear()
        self.itens.clear()
        self.erros.clear()
        self.atual = 0

    @property
    def item(self) -> ItemFatura | None:
        return self.itens[self.atual] if self.itens else None

    @property
    def confirmados(self) -> list[ItemFatura]:
        return [i for i in self.itens if i.confirmada]

    @property
    def proximo_pendente(self) -> int | None:
        return next((k for k, i in enumerate(self.itens) if not i.confirmada), None)
