"""Tela inicial: o que o extrator identifica, seleção de faturas e preferências."""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from .. import tema as T
from ..componentes import Card, ZonaArquivo, botao, icone, rotulo
from ..estado import TEM_PLANEJADOR, ler_config, salvar_config
from ..tema import F

RECURSOS = [
    ("≡", "Lançamentos", "Data, descrição e valor de cada compra, em qualquer layout de banco."),
    ("½", "Parcelas", "Reconhece 04/10, PARC 04/10 e 4 DE 10 e data a parcela no mês em que cai."),
    ("↺", "Créditos e estornos", "Entende −R$, R$ 40,00- (Banco do Brasil) e o sufixo C."),
    ("◎", "Internacionais", "Marca compras em outro país ou moeda estrangeira."),
    ("▤", "Resumo da fatura", "Vencimento, total, pagamento mínimo e limites — até em caixas separadas."),
    ("⇄", "Conciliação", "Confronta a soma extraída com o total e aponta a diferença."),
    ("◈", "PDFs protegidos", "Pede a senha uma vez e reaproveita nas outras faturas da sessão."),
    ("→", "Pronto para o planejador", "Exporta conta__AAAA-MM.xlsx no formato que o painel lê."),
]


class Inicio(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=3, uniform="c")
        self.grid_columnconfigure(1, weight=2, uniform="c")
        self.grid_rowconfigure(0, weight=1)

        # ---------------- coluna esquerda
        esq = ctk.CTkFrame(self, fg_color="transparent")
        esq.grid(row=0, column=0, sticky="nsew", padx=(32, 14), pady=26)
        esq.grid_columnconfigure(0, weight=1)

        rotulo(esq, "Importe sua fatura", F.titulo).grid(row=0, column=0, sticky="w")
        rotulo(esq, "Selecione o PDF, ajuste as preferências e deixe o resto com o extrator.",
               F.corpo, T.TEXTO_2).grid(row=1, column=0, sticky="w", pady=(2, 16))

        self.zona = ZonaArquivo(esq, self.selecionar, altura=200)
        self.zona.grid(row=2, column=0, sticky="ew")

        self.lista = ctk.CTkFrame(esq, fg_color="transparent")
        self.lista.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.lista.grid_columnconfigure(0, weight=1)

        pref = Card(esq)
        pref.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        pref.grid_columnconfigure((0, 1), weight=1)
        rotulo(pref, "PREFERÊNCIAS", F.rotulo, T.MUDO).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 8))

        rotulo(pref, "Conta (prefixo do arquivo)", F.pequena, T.TEXTO_2).grid(row=1, column=0, sticky="w", padx=(20, 8))
        rotulo(pref, "Pasta de saída", F.pequena, T.TEXTO_2).grid(row=1, column=1, sticky="w", padx=(8, 20))
        self.ent_conta = self._entrada(pref, app.var_conta)
        self.ent_conta.grid(row=2, column=0, sticky="ew", padx=(20, 8), pady=(4, 12))
        pasta = ctk.CTkFrame(pref, fg_color="transparent")
        pasta.grid(row=2, column=1, sticky="ew", padx=(8, 20), pady=(4, 12))
        pasta.grid_columnconfigure(0, weight=1)
        self._entrada(pasta, app.var_pasta).grid(row=0, column=0, sticky="ew")
        botao(pasta, "Procurar", self.escolher_pasta, "secundario", altura=38, width=96).grid(row=0, column=1, padx=(8, 0))

        self._switch(pref, "Ignorar linhas repetidas idênticas", app.var_dup).grid(
            row=3, column=0, sticky="w", padx=20, pady=(0, 16))
        if TEM_PLANEJADOR:
            self._switch(pref, "Enviar ao planejador ao exportar", app.var_atualizar).grid(
                row=3, column=1, sticky="w", padx=(8, 20), pady=(0, 16))

        self.btn_extrair = botao(esq, "Extrair lançamentos   →", self.extrair, "primario", altura=54,
                                 grande=True, state="disabled")
        self.btn_extrair.grid(row=5, column=0, sticky="ew", pady=(18, 0))

        # ---------------- coluna direita
        dir_ = Card(self)
        dir_.grid(row=0, column=1, sticky="nsew", padx=(14, 32), pady=26)
        dir_.grid_columnconfigure(1, weight=1)
        rotulo(dir_, "O QUE O EXTRATOR IDENTIFICA", F.rotulo, T.OURO).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=22, pady=(20, 10))
        for k, (gl, tit, desc) in enumerate(RECURSOS, start=1):
            icone(dir_, gl, 38).grid(row=k, column=0, sticky="n", padx=(22, 12), pady=8)
            bloco = ctk.CTkFrame(dir_, fg_color="transparent")
            bloco.grid(row=k, column=1, sticky="ew", padx=(0, 20), pady=6)
            rotulo(bloco, tit, F.corpo_b).pack(fill="x")
            lbl = rotulo(bloco, desc, F.pequena, T.TEXTO_2, wraplength=320)
            lbl.pack(fill="x")

    # --------------------------------------------------------------- helpers
    @staticmethod
    def _entrada(master, var):
        return ctk.CTkEntry(master, textvariable=var, height=38, corner_radius=10, fg_color=T.SURFACE_2,
                            border_color=T.BORDA, text_color=T.TEXTO, font=F.corpo)

    @staticmethod
    def _switch(master, texto, var):
        return ctk.CTkSwitch(master, text=texto, variable=var, font=F.pequena, text_color=T.TEXTO_2,
                             progress_color=T.OURO, button_color=T.TEXTO, button_hover_color=T.OURO_HOVER,
                             fg_color=T.SURFACE_3)

    # --------------------------------------------------------------- ciclo
    def on_show(self):
        self.app.bind("<Control-o>", lambda _e: self.selecionar())
        self._atualizar_lista()

    def on_hide(self):
        self.app.unbind("<Control-o>")

    # --------------------------------------------------------------- ações
    def selecionar(self):
        arqs = filedialog.askopenfilenames(
            parent=self.app, title="Selecione a(s) fatura(s)",
            filetypes=[("Faturas em PDF", "*.pdf *.PDF"), ("Todos os arquivos", "*")],
            initialdir=ler_config().get("ultima_pasta_pdf", str(Path.home())))
        if not arqs:
            return
        self.app.sessao.pdfs = [Path(a) for a in arqs]
        salvar_config(ultima_pasta_pdf=str(Path(arqs[0]).parent))
        self._atualizar_lista()

    def remover(self, pdf: Path):
        self.app.sessao.pdfs.remove(pdf)
        self._atualizar_lista()

    def escolher_pasta(self):
        p = filedialog.askdirectory(parent=self.app, initialdir=self.app.var_pasta.get() or str(Path.home()))
        if p:
            self.app.var_pasta.set(p)

    def extrair(self):
        if self.app.sessao.pdfs:
            self.app.iniciar_extracao()

    def _atualizar_lista(self):
        for w in self.lista.winfo_children():
            w.destroy()
        pdfs = self.app.sessao.pdfs
        self.zona.definir_qtd(len(pdfs))
        self.btn_extrair.configure(state="normal" if pdfs else "disabled")
        for k, pdf in enumerate(pdfs[:4]):
            linha = ctk.CTkFrame(self.lista, fg_color=T.SURFACE, corner_radius=10, border_width=1, border_color=T.BORDA)
            linha.grid(row=k, column=0, sticky="ew", pady=3)
            linha.grid_columnconfigure(1, weight=1)
            icone(linha, "▤", 28, bg=T.SURFACE).grid(row=0, column=0, padx=(12, 10), pady=7)
            rotulo(linha, pdf.name, F.corpo_b).grid(row=0, column=1, sticky="w")
            try:
                kb = pdf.stat().st_size / 1024
                tam = f"{kb:.0f} KB" if kb < 1024 else f"{kb / 1024:.1f} MB".replace(".", ",")
            except OSError:
                tam = ""
            rotulo(linha, tam, F.pequena, T.MUDO).grid(row=0, column=2, padx=10)
            botao(linha, "✕", lambda p=pdf: self.remover(p), "fantasma", altura=28, width=32).grid(row=0, column=3, padx=(0, 8))
        if len(pdfs) > 4:
            rotulo(self.lista, f"+ {len(pdfs) - 4} arquivo(s)", F.pequena, T.MUDO).grid(row=5, column=0, sticky="w", pady=(2, 0))
