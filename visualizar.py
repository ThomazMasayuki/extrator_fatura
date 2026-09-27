"""Análise visual das faturas confirmadas."""
from __future__ import annotations

import pandas as pd
import customtkinter as ctk

from .. import tema as T
from ..componentes import BarrasH, Card, Colunas, botao, rotulo
from ..fmt import brl, plural
from ..tema import F

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


class Visualizar(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=32, pady=(20, 10))
        topo.grid_columnconfigure(1, weight=1)
        botao(topo, "←  Voltar", lambda: app.mostrar("concluido"), "secundario", altura=36, width=110).grid(row=0, column=0, rowspan=2, padx=(0, 16))
        rotulo(topo, "Análise da fatura", F.titulo).grid(row=0, column=1, sticky="w")
        self.sub = rotulo(topo, "", F.corpo, T.TEXTO_2)
        self.sub.grid(row=1, column=1, sticky="w")
        self.seletor = ctk.CTkSegmentedButton(topo, command=lambda _v: self._render(), font=F.pequena_b, height=34,
                                              fg_color=T.SURFACE_2, selected_color=T.SELECIONADO,
                                              selected_hover_color=T.SELECIONADO_HOVER, unselected_color=T.SURFACE_2,
                                              unselected_hover_color=T.SURFACE_3, text_color=T.TEXTO)
        self.seletor.grid(row=0, column=2, rowspan=2, sticky="e")

        corpo = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=T.SURFACE_3,
                                       scrollbar_button_hover_color=T.BORDA)
        corpo.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.corpo = corpo
        corpo.grid_columnconfigure((0, 1), weight=1, uniform="v")

        kpis = ctk.CTkFrame(corpo, fg_color="transparent")
        kpis.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 12))
        self.kpis = {}
        for k, (chave, nome) in enumerate([("compras", "Total em compras"), ("creditos", "Créditos e estornos"),
                                            ("qtd", "Lançamentos"), ("ticket", "Ticket médio"),
                                            ("maior", "Maior compra")]):
            kpis.grid_columnconfigure(k, weight=1, uniform="k")
            c = Card(kpis, destaque=k == 0)
            c.grid(row=0, column=k, sticky="ew", padx=6)
            rotulo(c, nome.upper(), F.rotulo, T.MUDO).pack(anchor="w", padx=18, pady=(16, 2))
            v = rotulo(c, "—", F.numero)
            v.pack(anchor="w", padx=18)
            s = rotulo(c, "", F.pequena, T.TEXTO_2)
            s.pack(anchor="w", padx=18, pady=(0, 16))
            self.kpis[chave] = (v, s)

        self.g_cat = self._grafico(corpo, 1, 0, "Gastos por categoria", "Categoria informada pelo banco", BarrasH, 300)
        self.g_est = self._grafico(corpo, 1, 1, "Maiores estabelecimentos", "Top 8 por valor total", BarrasH, 300)
        self.g_dia = self._grafico(corpo, 2, 0, "Ritmo de gastos", "Compras por dia", Colunas, 240)
        self.lbl_dia = self._ultimo_sub
        self.g_parc, self.lbl_parc = self._grafico(corpo, 2, 1, "Parcelas já comprometidas",
                                                   "Quanto das próximas faturas já está comprometido", Colunas, 240,
                                                   com_extra=True)

    def _grafico(self, master, r, c, titulo, sub, cls, altura, com_extra=False):
        card = Card(master)
        card.grid(row=r, column=c, sticky="nsew", padx=12, pady=12)
        card.grid_columnconfigure(0, weight=1)
        rotulo(card, titulo, F.secao).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 0))
        self._ultimo_sub = rotulo(card, sub, F.pequena, T.TEXTO_2)
        self._ultimo_sub.grid(row=1, column=0, sticky="w", padx=20)
        extra = None
        if com_extra:
            extra = rotulo(card, "", F.corpo_b, T.OURO, anchor="e")
            extra.grid(row=0, column=1, rowspan=2, sticky="e", padx=20)
        g = cls(card, altura)
        g.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(12, 18))
        return (g, extra) if com_extra else g

    # --------------------------------------------------------------- dados
    def on_show(self):
        itens = self.app.sessao.confirmados
        nomes = ["Todas"] + [i.nome[:22] for i in itens] if len(itens) > 1 else [itens[0].nome[:22]] if itens else []
        self.seletor.configure(values=nomes)
        if nomes:
            self.seletor.set(nomes[0])
        self._render()

    def _df(self) -> pd.DataFrame:
        itens = self.app.sessao.confirmados
        if not itens:
            return pd.DataFrame(columns=["Data", "Descricao", "Valor", "Parcela", "Categoria_banco", "Tipo"])
        escolha = self.seletor.get()
        if escolha != "Todas":
            itens = [i for i in itens if i.nome[:22] == escolha] or itens
        return pd.concat([i.ativos for i in itens], ignore_index=True)

    def _render(self):
        df = self._df()
        compras = df[df["Valor"] > 0]
        creditos = df[df["Valor"] < 0]
        self.sub.configure(text=f"{plural(len(df), 'lançamento')} confirmados")

        tot = compras["Valor"].sum()
        self.kpis["compras"][0].configure(text=brl(tot))
        self.kpis["compras"][1].configure(text=f"{plural(len(compras), 'compra')}")
        self.kpis["creditos"][0].configure(text=brl(creditos["Valor"].sum()), text_color=T.BOM if len(creditos) else T.TEXTO)
        self.kpis["creditos"][1].configure(text=plural(len(creditos), "lançamento"))
        self.kpis["qtd"][0].configure(text=str(len(df)))
        intl = int((df["Tipo"] == "Internacional").sum()) if len(df) else 0
        self.kpis["qtd"][1].configure(text=f"{intl} internacional(is)")
        self.kpis["ticket"][0].configure(text=brl(compras["Valor"].mean()) if len(compras) else "—")
        self.kpis["ticket"][1].configure(text="por compra")
        if len(compras):
            m = compras.loc[compras["Valor"].idxmax()]
            self.kpis["maior"][0].configure(text=brl(m["Valor"]))
            self.kpis["maior"][1].configure(text=str(m["Descricao"])[:28])
        else:
            self.kpis["maior"][0].configure(text="—")
            self.kpis["maior"][1].configure(text="")

        cat = (compras.assign(c=compras["Categoria_banco"].replace("", "Sem categoria").fillna("Sem categoria"))
               .groupby("c")["Valor"].sum().sort_values(ascending=False))
        if len(cat) > 8:  # nunca mais de 8 barras: o resto vira "Outros"
            cat = pd.concat([cat.iloc[:7], pd.Series({"Outros": cat.iloc[7:].sum()})])
        self.g_cat.definir(list(cat.items()))

        est = compras.groupby("Descricao")["Valor"].sum().sort_values(ascending=False).head(8)
        self.g_est.definir(list(est.items()))

        if len(compras):
            dia = compras.groupby(compras["Data"].dt.normalize())["Valor"].sum()
            dia = dia.reindex(pd.date_range(dia.index.min(), dia.index.max()), fill_value=0)
            if len(dia) > 62:  # período longo: agrupa por semana para não virar um pente de barras finas
                dia = dia.resample("W-MON", label="left", closed="left").sum()
                self.lbl_dia.configure(text="Compras por semana")
            else:
                self.lbl_dia.configure(text="Compras por dia")
            self.g_dia.definir([(d.strftime("%d/%m"), float(v)) for d, v in dia.items()],
                               rotulo_cada=max(1, len(dia) // 8))
        else:
            self.g_dia.definir([])

        # parcelas futuras: parcela n/t ainda tem (t - n) cobranças pela frente
        futuro: dict[pd.Timestamp, float] = {}
        for r in df[df["Parcela"].astype(str).str.contains("/")].itertuples():
            n, t = map(int, str(r.Parcela).split("/"))
            base = pd.Timestamp(r.Data).to_period("M")
            for k in range(1, t - n + 1):
                mes = (base + k).to_timestamp()
                futuro[mes] = futuro.get(mes, 0.0) + float(r.Valor)
        if futuro:  # eixo contínuo: meses sem parcela aparecem com zero
            meses = pd.date_range(min(futuro), max(futuro), freq="MS")[:12]
        else:
            meses = []
        self.g_parc.definir([(f"{MESES[m.month - 1]}/{str(m.year)[2:]}", futuro.get(m, 0.0)) for m in meses])
        self.lbl_parc.configure(text=f"{brl(sum(futuro.values()))}\nem parcelas a vencer" if futuro else "")
