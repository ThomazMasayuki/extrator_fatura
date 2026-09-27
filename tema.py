"""Tema único do app: paleta 'meia-noite e ouro', fontes e estilo da tabela."""
from __future__ import annotations

import tkinter.font as tkfont
from tkinter import ttk

import customtkinter as ctk

# ----------------------------------------------------------------- paleta
BG = "#0B0F17"            # fundo da janela
SURFACE = "#121826"       # cartões
SURFACE_2 = "#182032"     # cartões internos / hover
SURFACE_3 = "#212B40"     # botões secundários, trilhos
ZEBRA = "#151C2B"         # linha alternada da tabela
BORDA = "#2A3550"
LINHA = "#222C42"         # divisórias finas e grade de gráfico

TEXTO = "#EEF2F8"
TEXTO_2 = "#B3BDD0"
MUDO = "#76819A"

OURO = "#D9B46A"          # cor de destaque
OURO_HOVER = "#E8C98A"
OURO_ESCURO = "#8C7342"
OURO_FUNDO = "#2A2418"
SOBRE_OURO = "#1A1408"    # texto sobre botão dourado
SELECIONADO = "#4A3C1F"   # segmento selecionado (texto claro legível)
SELECIONADO_HOVER = "#5A4926"

BOM = "#3DD68C"
BOM_FUNDO = "#11281E"
ALERTA = "#F2B84B"
ALERTA_FUNDO = "#2D2413"
RUIM = "#F47C7C"
RUIM_FUNDO = "#2E1719"

SERIE = "#C9A45C"         # cor única dos gráficos (uma série = um tom)
SERIE_HOVER = "#E8C98A"

SANS = ["Inter", "Inter Display", "SF Pro Text", "Segoe UI", "Cantarell", "Noto Sans",
        "Ubuntu", "Roboto", "DejaVu Sans", "FreeSans"]
SERIF = ["Playfair Display", "Cormorant Garamond", "Libre Baskerville", "Noto Serif Display",
         "Noto Serif", "Georgia", "DejaVu Serif", "FreeSerif"]
MONO = ["JetBrainsMono Nerd Font", "JetBrains Mono", "Fira Code", "Noto Sans Mono",
        "DejaVu Sans Mono", "FreeMono"]


class _Fontes:
    """Fontes criadas depois da janela raiz existir (exigência do Tk)."""

    def carregar(self, root) -> None:
        fams = set(tkfont.families(root))
        padrao = tkfont.nametofont("TkDefaultFont").actual("family")

        def escolher(prefs: list[str]) -> str:
            return next((f for f in prefs if f in fams), padrao)

        self.sans = escolher(SANS)
        self.serif = escolher(SERIF)
        self.mono = escolher(MONO)

        s = self.sans
        self.display = ctk.CTkFont(self.serif, 46, "bold")
        self.titulo = ctk.CTkFont(s, 26, "bold")
        self.subtitulo = ctk.CTkFont(s, 18, "bold")
        self.secao = ctk.CTkFont(s, 15, "bold")
        self.corpo = ctk.CTkFont(s, 13)
        self.corpo_b = ctk.CTkFont(s, 13, "bold")
        self.pequena = ctk.CTkFont(s, 11)
        self.pequena_b = ctk.CTkFont(s, 11, "bold")
        self.rotulo = ctk.CTkFont(s, 10, "bold")
        self.numero_g = ctk.CTkFont(s, 30, "bold")
        self.numero = ctk.CTkFont(s, 20, "bold")
        self.botao = ctk.CTkFont(s, 13, "bold")
        self.botao_g = ctk.CTkFont(s, 16, "bold")

    # fontes para Canvas/ttk (tamanho negativo = pixels, igual ao CustomTkinter)
    def tk(self, px: int, peso: str = "normal", familia: str | None = None) -> tuple:
        return (familia or self.sans, -px, peso)


F = _Fontes()


def carregar(root) -> None:
    ctk.set_appearance_mode("dark")
    F.carregar(root)
    _estilo_tabela(root)


def _estilo_tabela(root) -> None:
    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure("Fatura.Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXTO,
                 rowheight=32, borderwidth=0, relief="flat", font=F.tk(13),
                 bordercolor=SURFACE, lightcolor=SURFACE, darkcolor=SURFACE)
    st.configure("Fatura.Treeview.Heading", background=SURFACE_2, foreground=MUDO, relief="flat",
                 borderwidth=0, font=F.tk(11, "bold"), padding=(10, 8),
                 bordercolor=SURFACE_2, lightcolor=SURFACE_2, darkcolor=SURFACE_2)
    st.map("Fatura.Treeview.Heading", background=[("active", SURFACE_3)], foreground=[("active", TEXTO)])
    st.map("Fatura.Treeview", background=[("selected", OURO_FUNDO)], foreground=[("selected", OURO_HOVER)])
    st.layout("Fatura.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])


def misturar(c1: str, c2: str, t: float) -> str:
    """Interpola duas cores hex (t=0 -> c1, t=1 -> c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))
