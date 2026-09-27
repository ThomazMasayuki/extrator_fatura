"""Tela de processamento: progresso por arquivo enquanto a extração roda em segundo plano."""
from __future__ import annotations

import customtkinter as ctk

from .. import tema as T
from ..componentes import Card, botao, rotulo
from ..tema import F

GIRO = "◐◓◑◒"


class Processando(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.app = app
        self.grid_rowconfigure((0, 2), weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.card = Card(self, width=620)
        self.card.grid(row=1, column=0, padx=40)
        self.card.grid_columnconfigure(0, weight=1)
        rotulo(self.card, "LENDO SUAS FATURAS", F.rotulo, T.OURO).grid(row=0, column=0, sticky="w", padx=30, pady=(28, 4))
        self.titulo = rotulo(self.card, "Extraindo lançamentos…", F.subtitulo)
        self.titulo.grid(row=1, column=0, sticky="w", padx=30)
        self.sub = rotulo(self.card, "Isso leva poucos segundos por arquivo.", F.corpo, T.TEXTO_2)
        self.sub.grid(row=2, column=0, sticky="w", padx=30, pady=(2, 16))
        self.barra = ctk.CTkProgressBar(self.card, height=8, corner_radius=4, fg_color=T.SURFACE_3,
                                        progress_color=T.OURO, width=560)
        self.barra.grid(row=3, column=0, sticky="ew", padx=30)
        self.linhas = ctk.CTkFrame(self.card, fg_color="transparent")
        self.linhas.grid(row=4, column=0, sticky="ew", padx=30, pady=(16, 8))
        self.linhas.grid_columnconfigure(1, weight=1)
        self.btn_voltar = botao(self.card, "←  Voltar ao início", lambda: app.mostrar("inicio"), "secundario")
        self.status: list[tuple[ctk.CTkLabel, ctk.CTkLabel]] = []
        self.giro = 0
        self.rodando = False

    def on_show(self):
        pass

    def preparar(self, pdfs):
        for w in self.linhas.winfo_children():
            w.destroy()
        self.btn_voltar.grid_forget()
        self.titulo.configure(text="Extraindo lançamentos…")
        self.sub.configure(text="Isso leva poucos segundos por arquivo.")
        self.barra.set(0)
        self.status = []
        for k, pdf in enumerate(pdfs):
            ic = ctk.CTkLabel(self.linhas, text="○", text_color=T.MUDO, font=F.secao, width=24)
            ic.grid(row=k, column=0, sticky="w", pady=5)
            rotulo(self.linhas, pdf.name, F.corpo).grid(row=k, column=1, sticky="w", padx=8)
            st = rotulo(self.linhas, "na fila", F.pequena, T.MUDO, anchor="e")
            st.grid(row=k, column=2, sticky="e")
            self.status.append((ic, st))
        self.rodando = True
        self._girar()

    def _girar(self):
        if not self.rodando:
            return
        self.giro = (self.giro + 1) % len(GIRO)
        for ic, st in self.status:
            if st.cget("text") == "lendo…":
                ic.configure(text=GIRO[self.giro], text_color=T.OURO)
        self.after(120, self._girar)

    def iniciou(self, i: int):
        ic, st = self.status[i]
        st.configure(text="lendo…", text_color=T.OURO)

    def concluiu(self, i: int, total: int, ok: bool, detalhe: str):
        ic, st = self.status[i]
        ic.configure(text="✓" if ok else "✕", text_color=T.BOM if ok else T.RUIM)
        st.configure(text=detalhe, text_color=T.TEXTO_2 if ok else T.RUIM)
        self.barra.set((i + 1) / total)

    def falhou_tudo(self):
        self.rodando = False
        self.titulo.configure(text="Não foi possível ler as faturas")
        self.sub.configure(text="Verifique se o PDF tem texto (não escaneado) e a senha.")
        self.btn_voltar.grid(row=5, column=0, sticky="w", padx=30, pady=(4, 26))

    def terminar(self):
        self.rodando = False
