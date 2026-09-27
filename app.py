"""Janela principal: navegação entre telas, sessão, senhas, extração e exportação."""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from fatura_extractor import (FaturaExtractor, SenhaNecessaria, abrir_pdf, exportar_excel,
                              exportar_texto, nome_saida, remover_senha)

from . import tema as T
from .componentes import Dialogo, Stepper, Toaster, botao, rotulo
from .estado import (PASTA_PADRAO, RAIZ_PLANEJADOR, TEM_PLANEJADOR, ItemFatura, Sessao,
                     ler_config, salvar_config)
from .fmt import plural
from .tema import F
from .telas.boas_vindas import BoasVindas
from .telas.concluido import Concluido
from .telas.conferencia import Conferencia
from .telas.inicio import Inicio
from .telas.processando import Processando
from .telas.visualizar import Visualizar

PASSOS = ["Selecionar", "Extrair", "Conferir", "Exportar"]
PASSO_DA_TELA = {"inicio": 0, "processando": 1, "conferencia": 2, "concluido": 3, "visualizar": 3}


class App(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=T.BG)
        T.carregar(self)
        self.title("Extrator de Faturas")
        self.geometry("1320x860")
        self.minsize(1120, 720)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        cfg = ler_config()
        self.var_conta = tk.StringVar(value=cfg.get("conta", "cartao"))
        self.var_pasta = tk.StringVar(value=cfg.get("pasta", str(PASTA_PADRAO)))
        self.var_dup = tk.BooleanVar(value=cfg.get("remover_duplicados", False))
        self.var_atualizar = tk.BooleanVar(value=cfg.get("atualizar_painel", TEM_PLANEJADOR))
        self.sessao = Sessao()
        self.fila: queue.Queue = queue.Queue()
        self.toast = Toaster(self)

        self._montar_cabecalho()
        self.corpo = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        self.corpo.grid(row=1, column=0, sticky="nsew")
        self.corpo.grid_columnconfigure(0, weight=1)
        self.corpo.grid_rowconfigure(0, weight=1)
        self.telas = {
            "boas_vindas": BoasVindas(self.corpo, self),
            "inicio": Inicio(self.corpo, self),
            "processando": Processando(self.corpo, self),
            "conferencia": Conferencia(self.corpo, self),
            "concluido": Concluido(self.corpo, self),
            "visualizar": Visualizar(self.corpo, self),
        }
        self.tela_atual: str | None = None
        self.protocol("WM_DELETE_WINDOW", self._sair)
        self.after(60, self._consumir_fila)
        self.mostrar("boas_vindas")

    # --------------------------------------------------------------- cabeçalho
    def _montar_cabecalho(self):
        self.cabecalho = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=0, height=68)
        self.cabecalho.grid_columnconfigure(1, weight=1)
        marca = ctk.CTkFrame(self.cabecalho, fg_color="transparent")
        marca.grid(row=0, column=0, sticky="w", padx=(26, 10), pady=12)
        cv = tk.Canvas(marca, width=30, height=30, bg=T.SURFACE, highlightthickness=0)
        cv.create_polygon(15, 2, 28, 15, 15, 28, 2, 15, fill=T.OURO, outline="")
        cv.create_polygon(15, 9, 21, 15, 15, 21, 9, 15, fill=T.SURFACE, outline="")
        cv.pack(side="left")
        cv.bind("<Button-1>", lambda _e: self.mostrar("boas_vindas"))
        rotulo(marca, "Extrator de Faturas", F.secao).pack(side="left", padx=(10, 0))

        self.stepper = Stepper(self.cabecalho, PASSOS, bg=T.SURFACE)
        self.stepper.grid(row=0, column=1, sticky="ew", padx=10)

        ferramentas = ctk.CTkFrame(self.cabecalho, fg_color="transparent")
        ferramentas.grid(row=0, column=2, sticky="e", padx=(10, 22))
        botao(ferramentas, "Remover senha", self.ferramenta_remover_senha, "fantasma", altura=34).pack(side="left", padx=2)
        botao(ferramentas, "Diagnóstico", self.ferramenta_diagnostico, "fantasma", altura=34).pack(side="left", padx=2)
        self.linha_cab = ctk.CTkFrame(self, fg_color=T.BORDA, height=1, corner_radius=0)

    # --------------------------------------------------------------- navegação
    def mostrar(self, nome: str):
        if self.tela_atual:
            anterior = self.telas[self.tela_atual]
            if hasattr(anterior, "on_hide"):
                anterior.on_hide()
            anterior.grid_remove()
        if nome == "boas_vindas":
            self.cabecalho.grid_remove()
            self.linha_cab.grid_remove()
        else:
            self.cabecalho.grid(row=0, column=0, sticky="ew")
            self.linha_cab.place(in_=self.cabecalho, relx=0, rely=1.0, relwidth=1, anchor="sw")
            self.stepper.definir(PASSO_DA_TELA[nome])
        tela = self.telas[nome]
        tela.grid(row=0, column=0, sticky="nsew")
        self.tela_atual = nome
        tela.on_show()

    def iniciar(self):
        self.mostrar("inicio")

    def nova_extracao(self):
        self.sessao.nova()
        self.mostrar("inicio")

    # --------------------------------------------------------------- senhas
    def obter_senha(self, pdf: Path) -> str | None:
        """Senha que abre o PDF ('' se não tiver). None = cancelado."""
        s = self.sessao
        try:
            doc, senha = abrir_pdf(pdf, s.senhas_sessao)
            doc.close()
            return senha
        except SenhaNecessaria:
            pass
        msg = f"“{pdf.name}” está protegido. Digite a senha para abrir."
        dica = "Muitos bancos usam parte do CPF. A senha fica só na memória e é reaproveitada nesta sessão."
        for tentativa in range(3):
            senha = Dialogo(self, "PDF protegido", msg, [("Pular arquivo", None, "secundario"), ("Abrir", True, "primario")],
                            campo="senha", dica=dica, glifo="◈").mostrar()
            if senha is None:
                return None
            try:
                doc, _ = abrir_pdf(pdf, [senha])
                doc.close()
                if senha not in s.senhas_sessao:
                    s.senhas_sessao.append(senha)
                return senha
            except SenhaNecessaria:
                msg = f"Senha incorreta para “{pdf.name}”. Tentativa {tentativa + 2} de 3."
        self.toast(f"{pdf.name} foi ignorado: senha incorreta.", "ruim")
        return None

    # --------------------------------------------------------------- extração
    def iniciar_extracao(self):
        s = self.sessao
        s.senhas_pdf.clear()
        for pdf in s.pdfs:
            senha = self.obter_senha(pdf)
            if senha is not None:
                s.senhas_pdf[pdf] = senha
        if not s.senhas_pdf:
            self.toast("Nenhuma fatura pôde ser aberta.", "ruim")
            return
        salvar_config(conta=self.var_conta.get().strip() or "cartao", pasta=self.var_pasta.get(),
                      remover_duplicados=self.var_dup.get(), atualizar_painel=self.var_atualizar.get())
        s.itens.clear()
        s.erros.clear()
        s.atual = 0
        pdfs = list(s.senhas_pdf)
        self.mostrar("processando")
        self.telas["processando"].preparar(pdfs)
        dup = self.var_dup.get()
        threading.Thread(target=self._extrair_bg, args=(pdfs, dict(s.senhas_pdf), dup), daemon=True).start()

    def _extrair_bg(self, pdfs, senhas, dup):
        for i, pdf in enumerate(pdfs):
            self.fila.put(("inicio", i))
            try:
                fat = FaturaExtractor(pdf, dup, senhas[pdf] or None).process()
                self.fila.put(("ok", i, len(pdfs), fat))
            except Exception as e:  # noqa: BLE001 — qualquer falha vira mensagem para o usuário
                self.fila.put(("erro", i, len(pdfs), f"{pdf.name}: {e}"))
        self.fila.put(("fim",))

    def _consumir_fila(self):
        proc = self.telas["processando"]
        try:
            while True:
                msg = self.fila.get_nowait()
                tipo = msg[0]
                if tipo == "inicio":
                    proc.iniciou(msg[1])
                elif tipo == "ok":
                    _, i, n, fat = msg
                    self.sessao.itens.append(ItemFatura(fat))
                    proc.concluiu(i, n, True, plural(len(fat.lancamentos), "lançamento"))
                elif tipo == "erro":
                    _, i, n, erro = msg
                    self.sessao.erros.append(erro)
                    proc.concluiu(i, n, False, "falhou")
                elif tipo == "fim":
                    proc.terminar()
                    self._fim_extracao()
                elif tipo == "chamar":
                    msg[1]()
        except queue.Empty:
            pass
        self.after(60, self._consumir_fila)

    def _fim_extracao(self):
        s = self.sessao
        for e in s.erros:
            self.toast(e[:120], "ruim", 5000)
        if not s.itens:
            self.telas["processando"].falhou_tudo()
            return
        self.after(500, lambda: self.mostrar("conferencia"))

    # --------------------------------------------------------------- exportação
    def pasta_saida(self) -> Path:
        return Path(self.var_pasta.get()).expanduser()

    def exportar(self) -> list[Path]:
        itens = self.sessao.confirmados
        pasta = self.pasta_saida()
        conta = self.var_conta.get().strip() or "cartao"
        destinos = [pasta / nome_saida(i.fatura, conta) for i in itens]
        existentes = [d.name for d in destinos if d.exists()]
        if existentes:
            r = Dialogo(self, "Substituir arquivos?", "Já existem na pasta de saída:\n\n" + "\n".join(existentes),
                        [("Cancelar", None, "secundario"), ("Substituir", "ok", "primario")],
                        glifo="!", tipo="alerta").mostrar()
            if r != "ok":
                return []
        salvos = []
        for item, destino in zip(itens, destinos):
            try:
                salvos.append(exportar_excel(item.para_exportar(), destino))
                item.exportado = destino
            except PermissionError:
                self.toast(f"Feche {destino.name} no Excel/LibreOffice e tente de novo.", "ruim", 5000)
                return salvos
        salvar_config(conta=conta, pasta=str(pasta))
        self.toast(f"{plural(len(salvos), 'arquivo exportado', 'arquivos exportados')} para {pasta.name}/", "bom")
        if (TEM_PLANEJADOR and self.var_atualizar.get()
                and pasta.resolve() == (RAIZ_PLANEJADOR / "dados" / "faturas").resolve()):
            threading.Thread(target=self._atualizar_planejador, daemon=True).start()
        return salvos

    def _atualizar_planejador(self):
        r = subprocess.run([sys.executable, str(RAIZ_PLANEJADOR / "atualizar.py")], cwd=RAIZ_PLANEJADOR,
                           capture_output=True, text=True)
        if r.returncode == 0:
            self.fila.put(("chamar", lambda: self.toast("Painel do planejador atualizado.", "bom")))
        else:
            print(r.stdout, r.stderr, sep="\n")
            self.fila.put(("chamar", lambda: self.toast("Falha ao atualizar o planejador (veja o terminal).", "ruim")))

    def abrir_pasta(self):
        self._abrir(self.pasta_saida(), criar=True)

    @staticmethod
    def _abrir(caminho: Path, criar: bool = False):
        if criar:
            caminho.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(caminho)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(caminho)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # --------------------------------------------------------------- ferramentas
    def _escolher_pdf(self, titulo: str) -> Path | None:
        arq = filedialog.askopenfilename(parent=self, title=titulo, filetypes=[("PDF", "*.pdf *.PDF")],
                                         initialdir=ler_config().get("ultima_pasta_pdf", str(Path.home())))
        return Path(arq) if arq else None

    def ferramenta_remover_senha(self):
        pdf = self._escolher_pdf("PDF protegido")
        if not pdf:
            return
        senha = self.obter_senha(pdf)
        if senha is None:
            return
        if senha == "":
            self.toast(f"{pdf.name} não tem senha de abertura.", "ouro")
            return
        destino = filedialog.asksaveasfilename(parent=self, title="Salvar cópia sem senha", defaultextension=".pdf",
                                               initialdir=str(pdf.parent), initialfile=f"{pdf.stem}_sem_senha.pdf",
                                               filetypes=[("PDF", "*.pdf")])
        if not destino:
            return
        try:
            salvo = remover_senha(pdf, senha, destino)
            self.toast(f"Cópia sem senha salva: {salvo.name}", "bom")
        except Exception as e:  # noqa: BLE001
            self.toast(f"Não foi possível remover a senha: {e}", "ruim", 5000)

    def ferramenta_diagnostico(self, pdf: Path | None = None, senha: str | None = None):
        pdf = pdf or self._escolher_pdf("PDF para diagnóstico")
        if not pdf:
            return
        if senha is None:
            senha = self.obter_senha(pdf)
            if senha is None:
                return
        destino = filedialog.asksaveasfilename(parent=self, title="Salvar texto", defaultextension=".txt",
                                               initialdir=str(pdf.parent), initialfile=f"{pdf.stem}.txt",
                                               filetypes=[("Texto", "*.txt")])
        if destino:
            exportar_texto(pdf, senha or None, destino)
            self.toast(f"Texto salvo: {Path(destino).name}. Revise dados pessoais antes de compartilhar.", "bom", 4500)

    def diagnostico_atual(self):
        item = self.sessao.item
        if item:
            pdf = item.fatura.arquivo
            self.ferramenta_diagnostico(pdf, self.sessao.senhas_pdf.get(pdf, ""))

    def _sair(self):
        for t in self.telas.values():
            if hasattr(t, "on_hide"):
                t.on_hide()
        self.destroy()


def main():
    App().mainloop()
