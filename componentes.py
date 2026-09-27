"""Componentes visuais reutilizáveis (CustomTkinter + Canvas)."""
from __future__ import annotations

import math
import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk

from . import tema as T
from .fmt import brl, brl_curto
from .tema import F


# ----------------------------------------------------------------- básicos
def ret_arred(cv: tk.Canvas, x1, y1, x2, y2, r, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    p = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
         x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return cv.create_polygon(p, smooth=True, **kw)


class Card(ctk.CTkFrame):
    def __init__(self, master, destaque: bool = False, **kw):
        kw.setdefault("fg_color", T.SURFACE)
        kw.setdefault("corner_radius", 16)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", T.OURO_ESCURO if destaque else T.BORDA)
        super().__init__(master, **kw)


_ESTILOS = {
    "primario": dict(fg_color=T.OURO, hover_color=T.OURO_HOVER, text_color=T.SOBRE_OURO,
                     text_color_disabled="#6E5B35"),
    "sucesso": dict(fg_color=T.BOM, hover_color="#63E3A6", text_color="#06200F"),
    "secundario": dict(fg_color=T.SURFACE_3, hover_color="#2B3752", text_color=T.TEXTO,
                       border_width=1, border_color=T.BORDA, text_color_disabled=T.MUDO),
    "fantasma": dict(fg_color="transparent", hover_color=T.SURFACE_2, text_color=T.TEXTO_2),
}


def botao(master, texto: str, comando, estilo: str = "primario", altura: int = 40,
          grande: bool = False, **kw) -> ctk.CTkButton:
    cfg = dict(_ESTILOS[estilo])
    cfg.setdefault("font", F.botao_g if grande else F.botao)
    cfg.setdefault("corner_radius", altura // 2)
    cfg.update(kw)
    return ctk.CTkButton(master, text=texto, command=comando, height=altura, **cfg)


def badge(master, texto: str, tipo: str = "neutro") -> ctk.CTkLabel:
    cores = {"bom": (T.BOM_FUNDO, T.BOM), "alerta": (T.ALERTA_FUNDO, T.ALERTA),
             "ruim": (T.RUIM_FUNDO, T.RUIM), "ouro": (T.OURO_FUNDO, T.OURO),
             "neutro": (T.SURFACE_3, T.TEXTO_2)}
    bg, fg = cores[tipo]
    return ctk.CTkLabel(master, text=texto, fg_color=bg, text_color=fg, corner_radius=12,
                        font=F.pequena_b, height=26, padx=12)


def definir_badge(lbl: ctk.CTkLabel, texto: str, tipo: str) -> None:
    cores = {"bom": (T.BOM_FUNDO, T.BOM), "alerta": (T.ALERTA_FUNDO, T.ALERTA),
             "ruim": (T.RUIM_FUNDO, T.RUIM), "ouro": (T.OURO_FUNDO, T.OURO),
             "neutro": (T.SURFACE_3, T.TEXTO_2)}
    bg, fg = cores[tipo]
    lbl.configure(text=texto, fg_color=bg, text_color=fg)


def rotulo(master, texto: str, fonte=None, cor: str = T.TEXTO, **kw) -> ctk.CTkLabel:
    kw.setdefault("anchor", "w")
    kw.setdefault("justify", "left")
    return ctk.CTkLabel(master, text=texto, font=fonte or F.corpo, text_color=cor, **kw)


def divisoria(master) -> ctk.CTkFrame:
    return ctk.CTkFrame(master, height=1, fg_color=T.LINHA, corner_radius=0)


def icone(master, glifo: str, tam: int = 38, bg: str = T.SURFACE, cor: str = T.OURO,
          fundo: str = T.OURO_FUNDO) -> tk.Canvas:
    cv = tk.Canvas(master, width=tam, height=tam, bg=bg, highlightthickness=0, bd=0)
    ret_arred(cv, 1, 1, tam - 1, tam - 1, tam * 0.32, fill=fundo, outline="")
    cv.create_text(tam / 2, tam / 2, text=glifo, fill=cor, font=F.tk(int(tam * 0.45), "bold"))
    return cv


# ----------------------------------------------------------------- toast
class Toaster:
    def __init__(self, root):
        self.root = root
        self.atual = None

    def __call__(self, msg: str, tipo: str = "bom", ms: int = 3200) -> None:
        if self.atual is not None:
            self.atual.destroy()
        cor = {"bom": T.BOM, "alerta": T.ALERTA, "ruim": T.RUIM, "ouro": T.OURO}[tipo]
        glifo = {"bom": "✓", "alerta": "!", "ruim": "✕", "ouro": "◆"}[tipo]
        f = ctk.CTkFrame(self.root, fg_color=T.SURFACE_3, corner_radius=14, border_width=1, border_color=cor)
        ctk.CTkLabel(f, text=glifo, text_color=cor, font=F.secao, width=20).pack(side="left", padx=(16, 6), pady=12)
        ctk.CTkLabel(f, text=msg, text_color=T.TEXTO, font=F.corpo).pack(side="left", padx=(0, 18), pady=12)
        f.place(relx=1.0, rely=0.0, x=-28, y=84, anchor="ne")
        f.lift()
        self.atual = f
        self.root.after(ms, lambda: (f.destroy(), setattr(self, "atual", None) if self.atual is f else None))


# ----------------------------------------------------------------- diálogo
class Dialogo(ctk.CTkToplevel):
    """Diálogo modal no tema do app. `campo` = 'senha' | 'texto' | None."""

    def __init__(self, master, titulo: str, mensagem: str, botoes: list[tuple[str, object, str]],
                 campo: str | None = None, dica: str = "", glifo: str = "◆", tipo: str = "ouro"):
        super().__init__(master, fg_color=T.SURFACE)
        self.resultado = None
        self.title(titulo)
        self.resizable(False, False)
        self.transient(master)
        cor = {"ouro": T.OURO, "alerta": T.ALERTA, "ruim": T.RUIM, "bom": T.BOM}[tipo]
        fundo = {"ouro": T.OURO_FUNDO, "alerta": T.ALERTA_FUNDO, "ruim": T.RUIM_FUNDO, "bom": T.BOM_FUNDO}[tipo]

        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(padx=28, pady=(26, 22), fill="both")
        topo = ctk.CTkFrame(corpo, fg_color="transparent")
        topo.pack(fill="x")
        icone(topo, glifo, 44, bg=T.SURFACE, cor=cor, fundo=fundo).pack(side="left")
        ctk.CTkLabel(topo, text=titulo, font=F.subtitulo, text_color=T.TEXTO).pack(side="left", padx=14)
        ctk.CTkLabel(corpo, text=mensagem, font=F.corpo, text_color=T.TEXTO_2, justify="left",
                     anchor="w", wraplength=400).pack(fill="x", pady=(16, 4))

        self.entrada = None
        if campo:
            self.entrada = ctk.CTkEntry(corpo, show="•" if campo == "senha" else "", height=42,
                                        corner_radius=10, fg_color=T.SURFACE_2, border_color=T.BORDA,
                                        text_color=T.TEXTO, font=F.corpo, width=400)
            self.entrada.pack(fill="x", pady=(10, 0))
            self.entrada.bind("<Return>", lambda _e: self._fechar(True))
        if dica:
            ctk.CTkLabel(corpo, text=dica, font=F.pequena, text_color=T.MUDO, anchor="w",
                         justify="left", wraplength=400).pack(fill="x", pady=(8, 0))

        linha = ctk.CTkFrame(corpo, fg_color="transparent")
        linha.pack(fill="x", pady=(22, 0))
        for texto, valor, estilo in reversed(botoes):
            botao(linha, texto, lambda v=valor: self._fechar(v), estilo, altura=38).pack(side="right", padx=(8, 0))
        self.bind("<Escape>", lambda _e: self._fechar(None))
        self.protocol("WM_DELETE_WINDOW", lambda: self._fechar(None))

        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = master.winfo_rootx() + (master.winfo_width() - w) // 2
        y = master.winfo_rooty() + (master.winfo_height() - h) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.after(30, self._modal)

    def _modal(self):
        try:
            self.grab_set()
        except tk.TclError:
            self.after(50, self._modal)
            return
        (self.entrada or self).focus_force()

    def _fechar(self, valor):
        if valor is not None and self.entrada is not None:
            self.resultado = self.entrada.get() if valor is True else valor
        else:
            self.resultado = valor
        self.grab_release()
        self.destroy()

    def mostrar(self):
        self.master.wait_window(self)
        return self.resultado


# ----------------------------------------------------------------- stepper
class Stepper(tk.Canvas):
    def __init__(self, master, passos: list[str], bg: str = T.SURFACE):
        super().__init__(master, height=40, bg=bg, highlightthickness=0, bd=0)
        self.passos = passos
        self.atual = 0
        self.bind("<Configure>", lambda _e: self._desenhar())

    def definir(self, i: int) -> None:
        self.atual = i
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        fonte = F.tk(13, "bold")
        f = tkfont.Font(font=fonte)
        larguras = [f.measure(p) for p in self.passos]
        gap, r = 44, 13
        total = sum(2 * r + 10 + w for w in larguras) + gap * (len(self.passos) - 1)
        x = max(0, (self.winfo_width() - total) / 2)
        y = 20
        for i, (nome, w) in enumerate(zip(self.passos, larguras)):
            feito, atual = i < self.atual, i == self.atual
            if feito:
                self.create_oval(x, y - r, x + 2 * r, y + r, fill=T.OURO, outline="")
                self.create_text(x + r, y, text="✓", fill=T.SOBRE_OURO, font=F.tk(13, "bold"))
            elif atual:
                self.create_oval(x - 3, y - r - 3, x + 2 * r + 3, y + r + 3, fill=T.OURO_FUNDO, outline="")
                self.create_oval(x, y - r, x + 2 * r, y + r, fill=T.SURFACE, outline=T.OURO, width=2)
                self.create_text(x + r, y, text=str(i + 1), fill=T.OURO, font=F.tk(12, "bold"))
            else:
                self.create_oval(x, y - r, x + 2 * r, y + r, fill=T.SURFACE, outline=T.BORDA, width=2)
                self.create_text(x + r, y, text=str(i + 1), fill=T.MUDO, font=F.tk(12, "bold"))
            cor_txt = T.TEXTO if (feito or atual) else T.MUDO
            self.create_text(x + 2 * r + 10, y, text=nome, anchor="w", fill=cor_txt, font=fonte)
            x += 2 * r + 10 + w
            if i < len(self.passos) - 1:
                self.create_line(x + 12, y, x + gap - 12, y, fill=T.OURO if feito else T.BORDA, width=2)
                x += gap


# ----------------------------------------------------------------- zona de arquivo
class ZonaArquivo(tk.Canvas):
    """Área clicável com borda tracejada para escolher PDFs."""

    def __init__(self, master, comando, altura: int = 210):
        super().__init__(master, height=altura, bg=T.BG, highlightthickness=0, bd=0, cursor="hand2")
        self.comando = comando
        self.hover = False
        self.qtd = 0
        self.bind("<Configure>", lambda _e: self._desenhar())
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<Button-1>", lambda _e: self.comando())

    def definir_qtd(self, n: int) -> None:
        self.qtd = n
        self._desenhar()

    def _set_hover(self, v: bool) -> None:
        self.hover = v
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10:
            return
        ativo = self.hover or self.qtd
        ret_arred(self, 2, 2, w - 2, h - 2, 22, fill=T.SURFACE_2 if self.hover else T.SURFACE,
                  outline=T.OURO if ativo else T.BORDA, width=2, dash=(8, 6))
        cx, cy = w / 2, h / 2 - 26
        for k, cor in enumerate((T.misturar(T.OURO_FUNDO, T.SURFACE, 0.5), T.OURO_FUNDO)):
            rr = 36 - k * 8
            self.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, fill=cor, outline="")
        self.create_text(cx, cy, text="✓" if self.qtd else "↑", fill=T.OURO, font=F.tk(28, "bold"))
        titulo = (f"{self.qtd} fatura(s) selecionada(s) — clique para trocar" if self.qtd
                  else "Clique para selecionar a fatura em PDF")
        self.create_text(cx, cy + 58, text=titulo, fill=T.TEXTO, font=F.tk(16, "bold"))
        self.create_text(cx, cy + 84, text="Aceita vários arquivos  ·  PDFs com senha  ·  atalho Ctrl+O",
                         fill=T.MUDO, font=F.tk(12))


# ----------------------------------------------------------------- medidor de conciliação
class Medidor(tk.Canvas):
    """Barra que confronta a soma extraída com o total da fatura (marca de 100%)."""

    def __init__(self, master, bg: str = T.SURFACE):
        super().__init__(master, height=74, bg=bg, highlightthickness=0, bd=0)
        self.dados = (None, 0.0, False)
        self.bind("<Configure>", lambda _e: self._desenhar())

    def definir(self, total: float | None, extraido: float, confere: bool) -> None:
        self.dados = (total, extraido, confere)
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        w = self.winfo_width()
        if w < 20:
            return
        total, extraido, confere = self.dados
        y0, y1 = 30, 44
        ret_arred(self, 0, y0, w, y1, 7, fill=T.SURFACE_3, outline="")
        if not total:
            self.create_text(0, 12, text="Total da fatura não identificado", anchor="w",
                             fill=T.ALERTA, font=F.tk(12, "bold"))
            self.create_text(0, 62, text="Informe o total para conciliar", anchor="w",
                             fill=T.MUDO, font=F.tk(11))
            return
        escala = 1.15
        alvo = w / escala
        prop = max(0.0, extraido / total)
        cor = T.BOM if confere else T.ALERTA
        fim = max(10, min(w, alvo * prop))
        ret_arred(self, 0, y0, fim, y1, 7, fill=cor, outline="")
        self.create_line(alvo, y0 - 8, alvo, y1 + 8, fill=T.TEXTO, width=2)
        self.create_text(alvo, y1 + 18, text="total da fatura", fill=T.MUDO, font=F.tk(10))
        pct = f"{prop * 100:.1f}%".replace(".", ",")
        self.create_text(0, 12, text=f"{pct} do total conciliado", anchor="w", fill=cor, font=F.tk(13, "bold"))


# ----------------------------------------------------------------- check animado
class CheckAnimado(tk.Canvas):
    def __init__(self, master, tam: int = 104, bg: str = T.BG):
        super().__init__(master, width=tam, height=tam, bg=bg, highlightthickness=0, bd=0)
        self.tam = tam

    def animar(self, passo: int = 0) -> None:
        t = self.tam
        self.delete("all")
        p = min(1.0, passo / 18)
        self.create_oval(6, 6, t - 6, t - 6, fill=T.misturar(T.BG, T.BOM_FUNDO, p), outline="")
        self.create_arc(6, 6, t - 6, t - 6, start=90, extent=-359.9 * p, style="arc", outline=T.BOM, width=4)
        if passo > 12:
            q = min(1.0, (passo - 12) / 12)
            pts = [(t * 0.30, t * 0.52), (t * 0.44, t * 0.66), (t * 0.72, t * 0.38)]
            seg1 = min(1.0, q * 2)
            x = pts[0][0] + (pts[1][0] - pts[0][0]) * seg1
            y = pts[0][1] + (pts[1][1] - pts[0][1]) * seg1
            self.create_line(pts[0][0], pts[0][1], x, y, fill=T.BOM, width=6, capstyle="round")
            if q > 0.5:
                s2 = (q - 0.5) * 2
                x2 = pts[1][0] + (pts[2][0] - pts[1][0]) * s2
                y2 = pts[1][1] + (pts[2][1] - pts[1][1]) * s2
                self.create_line(pts[1][0], pts[1][1], x2, y2, fill=T.BOM, width=6, capstyle="round")
        if passo < 26:
            self.after(22, self.animar, passo + 1)


# ----------------------------------------------------------------- gráficos
class _GraficoBase(tk.Canvas):
    def __init__(self, master, altura: int, bg: str = T.SURFACE):
        super().__init__(master, height=altura, bg=bg, highlightthickness=0, bd=0)
        self.dados: list[tuple[str, float]] = []
        self.dicas: dict[int, str] = {}
        self.bind("<Configure>", lambda _e: self._desenhar())
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", lambda _e: self._sem_dica())

    def definir(self, dados: list[tuple[str, float]]) -> None:
        self.dados = dados
        self._desenhar()

    def _vazio(self, w, h) -> bool:
        if not self.dados or max((v for _, v in self.dados), default=0) <= 0:
            self.create_text(w / 2, h / 2, text="Sem dados para exibir", fill=T.MUDO, font=F.tk(12))
            return True
        return False

    def _sem_dica(self):
        self.delete("dica")
        self.itemconfigure("barra", fill=T.SERIE)

    def _mover(self, ev):
        self._sem_dica()
        itens = self.find_overlapping(ev.x - 1, ev.y - 1, ev.x + 1, ev.y + 1)
        alvo = next((i for i in reversed(itens) if i in self.dicas), None)
        if alvo is None:
            return
        barra = self.dicas_barra.get(alvo)
        if barra:
            self.itemconfigure(barra, fill=T.SERIE_HOVER)
        texto = self.dicas[alvo]
        t = self.create_text(0, 0, text=texto, fill=T.TEXTO, font=F.tk(12, "bold"), anchor="nw", tags="dica")
        x1, y1, x2, y2 = self.bbox(t)
        tw, th = x2 - x1 + 20, y2 - y1 + 14
        x = min(ev.x + 14, self.winfo_width() - tw - 4)
        y = max(4, ev.y - th - 10)
        fundo = ret_arred(self, x, y, x + tw, y + th, 8, fill=T.SURFACE_3, outline=T.BORDA, tags="dica")
        self.coords(t, x + 10, y + 7)
        self.tag_raise(fundo)
        self.tag_raise(t)


class BarrasH(_GraficoBase):
    """Barras horizontais ordenadas (magnitude, uma série = um tom)."""

    def _desenhar(self) -> None:
        self.delete("all")
        self.dicas, self.dicas_barra = {}, {}
        w, h = self.winfo_width(), self.winfo_height()
        if w < 50 or self._vazio(w, h):
            return
        fr = tkfont.Font(font=F.tk(12))
        n = len(self.dados)
        passo = min(34, (h - 8) / n)
        esp = min(14, passo * 0.45)
        rot_w = min(w * 0.42, max(fr.measure(r) for r, _ in self.dados) + 12)
        val_w = 92
        area = max(40, w - rot_w - val_w)
        vmax = max(v for _, v in self.dados)
        total = sum(v for _, v in self.dados) or 1
        for k, (rot, v) in enumerate(self.dados):
            yc = 4 + passo * k + passo / 2
            txt = rot if fr.measure(rot) <= rot_w - 12 else rot[: max(4, int(len(rot) * (rot_w - 20) / fr.measure(rot)))] + "…"
            self.create_text(0, yc, text=txt, anchor="w", fill=T.TEXTO_2, font=F.tk(12))
            comp = max(4, area * v / vmax)
            x0 = rot_w
            b = ret_arred(self, x0, yc - esp / 2, x0 + comp, yc + esp / 2, 4, fill=T.SERIE, outline="", tags="barra")
            self.create_text(x0 + comp + 8, yc, text=brl_curto(v), anchor="w", fill=T.TEXTO, font=F.tk(12, "bold"))
            alvo = self.create_rectangle(0, yc - passo / 2, w, yc + passo / 2, outline="", fill="")
            pct = f"{v / total * 100:.1f}".replace(".", ",")
            self.dicas[alvo] = f"{rot}\n{brl(v)}  ·  {pct}% do total"
            self.dicas_barra[alvo] = b
            self.tag_lower(alvo)


class Colunas(_GraficoBase):
    """Colunas verticais (série temporal curta)."""

    def __init__(self, master, altura: int, bg: str = T.SURFACE, rotulo_cada: int = 1):
        super().__init__(master, altura, bg)
        self.rotulo_cada = rotulo_cada

    def definir(self, dados, rotulo_cada: int | None = None) -> None:
        if rotulo_cada:
            self.rotulo_cada = rotulo_cada
        super().definir(dados)

    def _desenhar(self) -> None:
        self.delete("all")
        self.dicas, self.dicas_barra = {}, {}
        w, h = self.winfo_width(), self.winfo_height()
        if w < 50 or self._vazio(w, h):
            return
        esq, base, topo = 58, h - 26, 12
        vmax = max(v for _, v in self.dados)
        mag = 10 ** math.floor(math.log10(vmax)) if vmax > 0 else 1
        teto = math.ceil(vmax / mag) * mag
        for k in range(4):
            yv = teto * k / 3
            y = base - (base - topo) * yv / teto
            self.create_line(esq, y, w, y, fill=T.LINHA)
            self.create_text(esq - 8, y, text=brl_curto(yv), anchor="e", fill=T.MUDO, font=F.tk(10))
        n = len(self.dados)
        slot = (w - esq) / n
        larg = max(3, min(28, slot * 0.62))
        for k, (rot, v) in enumerate(self.dados):
            xc = esq + slot * k + slot / 2
            y = base - (base - topo) * v / teto
            b = None
            if v > 0:
                b = ret_arred(self, xc - larg / 2, min(y, base - 3), xc + larg / 2, base, 4,
                              fill=T.SERIE, outline="", tags="barra")
            if k % self.rotulo_cada == 0:
                self.create_text(xc, base + 13, text=rot, fill=T.MUDO, font=F.tk(10))
            alvo = self.create_rectangle(xc - slot / 2, topo, xc + slot / 2, base, outline="", fill="")
            self.dicas[alvo] = f"{rot}\n{brl(v)}"
            if b:
                self.dicas_barra[alvo] = b
            self.tag_lower(alvo)
