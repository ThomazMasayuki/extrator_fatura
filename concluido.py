"""Tudo conferido: exportar, visualizar, enviar ao planejador ou recomeçar."""
from __future__ import annotations

import customtkinter as ctk

from .. import tema as T
from ..componentes import Card, CheckAnimado, botao, icone, rotulo
from ..estado import TEM_PLANEJADOR
from ..fmt import brl, data_br, plural
from ..tema import F


class Concluido(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 5), weight=1)

        self.check = CheckAnimado(self, 104)
        self.check.grid(row=1, column=0, pady=(0, 10))
        rotulo(self, "Tudo conferido!", ctk.CTkFont(F.serif, 40, "bold"),
               anchor="center").grid(row=2, column=0)
        self.resumo = rotulo(self, "", F.corpo, T.TEXTO_2, anchor="center")
        self.resumo.grid(row=3, column=0, pady=(4, 20))

        meio = ctk.CTkFrame(self, fg_color="transparent")
        meio.grid(row=4, column=0, padx=40)

        self.tabela = Card(meio)
        self.tabela.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 18))

        self.cards = {}
        acoes = [("excel", "↓", "Exportar para Excel", "Gera conta__AAAA-MM.xlsx com lançamentos, resumo e avisos.",
                  "Exportar", self.exportar, "primario"),
                 ("ver", "▥", "Visualizar análise", "Categorias, maiores gastos, ritmo diário e parcelas futuras.",
                  "Visualizar", lambda: app.mostrar("visualizar"), "secundario"),
                 ("pasta", "▤", "Abrir pasta", "Abre a pasta de saída no gerenciador de arquivos.",
                  "Abrir", app.abrir_pasta, "secundario"),
                 ("nova", "↺", "Nova extração", "Volta ao início para importar outras faturas.",
                  "Recomeçar", app.nova_extracao, "secundario")]
        for k, (chave, gl, tit, desc, txt_btn, cmd, estilo) in enumerate(acoes):
            c = Card(meio, destaque=chave == "excel", width=250)
            c.grid(row=1, column=k, sticky="nsew", padx=8)
            icone(c, gl, 44).pack(anchor="w", padx=20, pady=(20, 12))
            rotulo(c, tit, F.secao).pack(anchor="w", padx=20)
            rotulo(c, desc, F.pequena, T.TEXTO_2, wraplength=210).pack(anchor="w", padx=20, pady=(4, 14))
            b = botao(c, txt_btn, cmd, estilo, altura=38)
            b.pack(fill="x", padx=20, pady=(0, 20), side="bottom")
            self.cards[chave] = b

        self.resultado = rotulo(self, "", F.pequena, T.BOM, anchor="center")
        self.resultado.grid(row=5, column=0, sticky="n", pady=16)

    def on_show(self):
        s = self.app.sessao
        itens = s.confirmados
        qtd = sum(len(i.ativos) for i in itens)
        compras = sum(i.compras for i in itens)
        self.resumo.configure(text=f"{plural(len(itens), 'fatura')}  ·  {plural(qtd, 'lançamento')}  ·  "
                                   f"{brl(compras)} em compras")
        self.check.animar()
        self.resultado.configure(text="")
        txt = "Exportar e enviar ao planejador" if (TEM_PLANEJADOR and self.app.var_atualizar.get()) else "Exportar"
        self.cards["excel"].configure(text=txt)

        for w in self.tabela.winfo_children():
            w.destroy()
        cab = ["FATURA", "VENCIMENTO", "TOTAL", "EXTRAÍDO", "SITUAÇÃO"]
        for j, c in enumerate(cab):
            rotulo(self.tabela, c, F.rotulo, T.MUDO, anchor="e" if j in (2, 3) else "w").grid(
                row=0, column=j, sticky="ew", padx=18, pady=(14, 6))
        self.tabela.grid_columnconfigure(0, weight=1)
        for k, i in enumerate(itens, start=1):
            ult = k == len(itens)
            pad = (4, 14) if ult else 4
            rotulo(self.tabela, i.nome, F.corpo_b).grid(row=k, column=0, sticky="w", padx=18, pady=pad)
            rotulo(self.tabela, data_br(i.fatura.vencimento), F.corpo, T.TEXTO_2).grid(row=k, column=1, sticky="w", padx=18, pady=pad)
            rotulo(self.tabela, brl(i.total), F.corpo, anchor="e").grid(row=k, column=2, sticky="e", padx=18, pady=pad)
            rotulo(self.tabela, brl(i.extraido), F.corpo, anchor="e").grid(row=k, column=3, sticky="e", padx=18, pady=pad)
            sit, cor = ("✓ confere", T.BOM) if i.confere else ("! diferença " + brl(i.diferenca) if i.diferenca is not None
                                                             else "! sem total", T.ALERTA)
            rotulo(self.tabela, sit, F.pequena_b, cor).grid(row=k, column=4, sticky="w", padx=18, pady=pad)

    def exportar(self):
        salvos = self.app.exportar()
        if salvos:
            nomes = ", ".join(p.name for p in salvos)
            self.resultado.configure(text=f"✓  Salvo em {salvos[0].parent}:  {nomes}")
