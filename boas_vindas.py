"""Tela de entrada: cartão animado e o botão 'Clique aqui para iniciar'."""
from __future__ import annotations

import math
import random
import tkinter as tk

import customtkinter as ctk

from .. import tema as T
from ..componentes import ret_arred
from ..tema import F


class BoasVindas(ctk.CTkFrame):
    FPS_MS = 40  # ~25 fps: suave e leve

    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.app = app
        self.cv = tk.Canvas(self, bg=T.BG, highlightthickness=0, bd=0)
        self.cv.pack(fill="both", expand=True)
        self.particulas: list[list[float]] = []
        self.t = 0.0
        self.ativo = False
        self._redesenho = None
        self.cv.bind("<Configure>", self._agendar)

    # --------------------------------------------------------------- ciclo
    def on_show(self):
        self.ativo = True
        self.app.bind("<Return>", lambda _e: self.app.iniciar())
        self._animar()

    def on_hide(self):
        self.ativo = False
        self.app.unbind("<Return>")

    def _agendar(self, _e=None):
        if self._redesenho:
            self.after_cancel(self._redesenho)
        self._redesenho = self.after(60, self._desenhar)

    # --------------------------------------------------------------- desenho
    def _desenhar(self):
        cv = self.cv
        cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 100:
            return
        card_w = min(430, w * 0.34)
        card_h = card_w / 1.586
        bloco = card_h + 300
        topo = max(30, (h - bloco) / 2)
        cx = w / 2
        self.card_box = (cx - card_w / 2, topo, cx + card_w / 2, topo + card_h)

        # brilho radial atrás do cartão (círculos concêntricos, sem transparência)
        gy = topo + card_h / 2
        for k in range(22, 0, -1):
            r = card_w * 0.45 + k * card_w * 0.045
            cor = T.misturar(T.BG, "#1C1A17", (22 - k) / 22 * 0.9)
            cv.create_oval(cx - r * 1.35, gy - r * 0.8, cx + r * 1.35, gy + r * 0.8, fill=cor, outline="")

        # partículas douradas
        random.seed(7)
        self.particulas = []
        for _ in range(46):
            x, y = random.uniform(0, w), random.uniform(0, h)
            r = random.choice((1, 1, 1.5, 2))
            vel = random.uniform(0.15, 0.55)
            cor = T.misturar(T.BG, T.OURO, random.uniform(0.25, 0.7))
            item = cv.create_oval(x - r, y - r, x + r, y + r, fill=cor, outline="", tags="particula")
            self.particulas.append([item, vel, random.uniform(0, 6.28), h])

        self._desenhar_cartao(*self.card_box)

        y = topo + card_h + 58
        cv.create_text(cx, y, text="Extrator de Faturas", fill=T.TEXTO, font=F.tk(46, "bold", F.serif))
        y += 50
        cv.create_text(cx, y, text="Transforme o PDF da sua fatura em lançamentos conferidos — em segundos.",
                       fill=T.TEXTO_2, font=F.tk(16))
        y += 34
        cv.create_line(cx - 40, y, cx + 40, y, fill=T.OURO_ESCURO, width=1)
        y += 52
        self._botao(cx, y)
        y += 64
        cv.create_text(cx, y, text="◈  Processamento 100% local  ·  seus dados não saem do computador",
                       fill=T.MUDO, font=F.tk(12))

    def _botao(self, cx, cy):
        cv, bw, bh = self.cv, 330, 60
        halo = ret_arred(cv, cx - bw / 2 - 6, cy - bh / 2 - 6, cx + bw / 2 + 6, cy + bh / 2 + 6, 36,
                         fill=T.misturar(T.BG, T.OURO, 0.12), outline="", tags=("btn", "btn_halo"))
        corpo = ret_arred(cv, cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, 30,
                          fill=T.OURO, outline="", tags=("btn", "btn_corpo"))
        cv.create_text(cx, cy, text="Clique aqui para iniciar   →", fill=T.SOBRE_OURO,
                       font=F.tk(18, "bold"), tags="btn")
        cv.tag_bind("btn", "<Enter>", lambda _e: (cv.itemconfigure("btn_corpo", fill=T.OURO_HOVER),
                                                  cv.configure(cursor="hand2")))
        cv.tag_bind("btn", "<Leave>", lambda _e: (cv.itemconfigure("btn_corpo", fill=T.OURO),
                                                  cv.configure(cursor="")))
        cv.tag_bind("btn", "<Button-1>", lambda _e: self.app.iniciar())

    def _desenhar_cartao(self, x1, y1, x2, y2):
        cv = self.cv
        w, h = x2 - x1, y2 - y1
        tag = "cartao"
        ret_arred(cv, x1 + 6, y1 + 10, x2 + 6, y2 + 14, 22, fill="#07090E", outline="", tags=tag)   # sombra
        ret_arred(cv, x1, y1, x2, y2, 22, fill="#141B29", outline=T.OURO_ESCURO, width=2, tags=(tag, "borda"))
        # linhas de guilhoché
        for k in range(9):
            pts = []
            for i in range(0, 41):
                px = x1 + 12 + (w - 24) * i / 40
                py = y1 + h * 0.62 + math.sin(i / 40 * math.pi * 2 + k * 0.35) * h * (0.07 + k * 0.012) - k * 4
                pts += [px, py]
            cv.create_line(*pts, smooth=True, fill=T.misturar("#141B29", T.OURO, 0.07 + k * 0.012), tags=tag)
        # chip
        cx, cy = x1 + w * 0.12, y1 + h * 0.34
        ret_arred(cv, cx, cy, cx + w * 0.13, cy + h * 0.17, 6, fill=T.OURO, outline="", tags=tag)
        for f in (0.33, 0.66):
            cv.create_line(cx, cy + h * 0.17 * f, cx + w * 0.13, cy + h * 0.17 * f, fill=T.OURO_ESCURO, tags=tag)
        cv.create_line(cx + w * 0.065, cy, cx + w * 0.065, cy + h * 0.17, fill=T.OURO_ESCURO, tags=tag)
        # aproximação
        ax, ay = cx + w * 0.19, cy + h * 0.085
        for k in range(3):
            r = 7 + k * 6
            cv.create_arc(ax - r, ay - r, ax + r, ay + r, start=-45, extent=90, style="arc",
                          outline=T.OURO_ESCURO, width=2, tags=tag)
        # textos
        cv.create_text(x1 + w * 0.08, y1 + h * 0.16, text="◆  EXTRATOR", anchor="w", fill=T.OURO,
                       font=F.tk(max(11, int(h * 0.065)), "bold"), tags=tag)
        cv.create_text(x2 - w * 0.08, y1 + h * 0.16, text="PLATINUM", anchor="e", fill=T.OURO_ESCURO,
                       font=F.tk(max(9, int(h * 0.05)), "bold"), tags=tag)
        cv.create_text(x1 + w * 0.08, y1 + h * 0.66, text="••••   ••••   ••••   2026", anchor="w",
                       fill=T.TEXTO, font=F.tk(max(12, int(h * 0.085)), "bold", F.mono), tags=tag)
        cv.create_text(x1 + w * 0.08, y1 + h * 0.82, text="SUAS FINANÇAS, CONFERIDAS", anchor="w",
                       fill=T.TEXTO_2, font=F.tk(max(9, int(h * 0.05)), "bold"), tags=tag)
        r = h * 0.085
        bx, by = x2 - w * 0.1, y1 + h * 0.8
        cv.create_oval(bx - 2.6 * r, by - r, bx - 0.6 * r, by + r, outline=T.OURO, width=2, tags=tag)
        cv.create_oval(bx - 1.4 * r, by - r, bx + 0.6 * r, by + r, outline=T.OURO_ESCURO, width=2, tags=tag)

    # --------------------------------------------------------------- animação
    def _animar(self):
        if not self.ativo:
            return
        self.t += 0.05
        cv = self.cv
        for p in self.particulas:
            item, vel, fase, h = p
            dx = math.sin(self.t + fase) * 0.25
            cv.move(item, dx, -vel)
            c = cv.coords(item)
            if c and c[3] < 0:
                cv.move(item, 0, h + 6)
        # cartão flutuando e borda "respirando"
        cv.move("cartao", 0, math.cos(self.t * 0.9) * 0.18)
        brilho = (math.sin(self.t * 1.3) + 1) / 2
        cv.itemconfigure("borda", outline=T.misturar(T.OURO_ESCURO, T.OURO_HOVER, brilho * 0.8))
        cv.itemconfigure("btn_halo", fill=T.misturar(T.BG, T.OURO, 0.08 + brilho * 0.14))
        self.after(self.FPS_MS, self._animar)
