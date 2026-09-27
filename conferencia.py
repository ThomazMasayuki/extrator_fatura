"""Conferência: tabela de lançamentos + painel de conciliação com o total da fatura."""
from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

from .. import tema as T
from ..componentes import Card, Dialogo, Medidor, badge, botao, definir_badge, divisoria, rotulo
from ..fmt import brl, cartao, data_br, ler_brl, plural
from ..tema import F

FILTROS = ["Todos", "Compras", "Créditos", "Parcelados", "Internacionais", "Excluídos"]


class Conferencia(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.app = app
        self.revisao = False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---------------- topo
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=32, pady=(22, 14))
        topo.grid_columnconfigure(1, weight=1)
        tit = ctk.CTkFrame(topo, fg_color="transparent")
        tit.grid(row=0, column=0, sticky="w")
        rotulo(tit, "Conferência", F.titulo).pack(anchor="w")
        rotulo(tit, "Revise os lançamentos e confronte a soma com o total da fatura.", F.corpo, T.TEXTO_2).pack(anchor="w")
        self.seletor = ctk.CTkSegmentedButton(topo, command=self._trocar_fatura, font=F.pequena_b, height=34,
                                              fg_color=T.SURFACE_2, selected_color=T.SELECIONADO,
                                              selected_hover_color=T.SELECIONADO_HOVER, unselected_color=T.SURFACE_2,
                                              unselected_hover_color=T.SURFACE_3, text_color=T.TEXTO,
                                              text_color_disabled=T.MUDO)
        self.seletor.grid(row=0, column=1, sticky="e", padx=12)
        self.badge = badge(topo, "—")
        self.badge.grid(row=0, column=2, sticky="e")

        # ---------------- corpo
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.grid(row=1, column=0, sticky="nsew", padx=32)
        corpo.grid_columnconfigure(0, weight=1)
        corpo.grid_rowconfigure(0, weight=1)

        # tabela
        tab = Card(corpo)
        tab.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        barra = ctk.CTkFrame(tab, fg_color="transparent")
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 10))
        barra.grid_columnconfigure(0, weight=1)
        self.busca = ctk.CTkEntry(barra, placeholder_text="⌕  Buscar descrição ou categoria…",
                                  height=36, corner_radius=18, fg_color=T.SURFACE_2, border_color=T.BORDA,
                                  text_color=T.TEXTO, placeholder_text_color=T.MUDO, font=F.corpo, width=260)
        self.busca.grid(row=0, column=0, sticky="w")
        self.busca.bind("<KeyRelease>", lambda _e: self._preencher())
        self.filtro = ctk.CTkSegmentedButton(barra, values=FILTROS, command=lambda _v: self._preencher(),
                                             font=F.pequena_b, height=32, fg_color=T.SURFACE_2,
                                             selected_color=T.SURFACE_3, selected_hover_color=T.SURFACE_3,
                                             unselected_color=T.SURFACE_2, unselected_hover_color=T.SURFACE_3,
                                             text_color=T.TEXTO_2)
        self.filtro.set("Todos")
        self.filtro.grid(row=0, column=1, sticky="e")

        cols = ("marca", "data", "desc", "parcela", "cat", "tipo", "valor")
        titulos = ("", "DATA", "DESCRIÇÃO", "PARCELA", "CATEGORIA (BANCO)", "TIPO", "VALOR")
        larg = (34, 96, 330, 74, 170, 110, 120)
        self.tree = ttk.Treeview(tab, columns=cols, show="headings", style="Fatura.Treeview", selectmode="browse")
        for c, t, w in zip(cols, titulos, larg):
            self.tree.heading(c, text=t, anchor="e" if c == "valor" else "w")
            self.tree.column(c, width=w, minwidth=30, anchor="e" if c == "valor" else ("center" if c == "marca" else "w"),
                             stretch=c == "desc")
        self.tree.tag_configure("par", background=T.SURFACE)
        self.tree.tag_configure("impar", background=T.ZEBRA)
        self.tree.tag_configure("credito", foreground=T.BOM)
        self.tree.tag_configure("excluido", foreground=T.MUDO)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 4))
        sb = ctk.CTkScrollbar(tab, command=self.tree.yview, button_color=T.SURFACE_3, button_hover_color=T.BORDA)
        sb.grid(row=1, column=1, sticky="ns", padx=(0, 6), pady=(0, 4))
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Configure>", self._ajustar_colunas)
        self.tree.bind("<Double-1>", self._alternar_linha)
        self.tree.bind("<Delete>", self._alternar_linha)
        rodape = ctk.CTkFrame(tab, fg_color="transparent")
        rodape.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(4, 12))
        rodape.grid_columnconfigure(0, weight=1)
        rotulo(rodape, "Dica: dê dois cliques numa linha (ou Delete) para excluí-la ou incluí-la de volta na soma.",
               F.pequena, T.MUDO).grid(row=0, column=0, sticky="w")
        self.contador = rotulo(rodape, "", F.pequena_b, T.TEXTO_2, anchor="e")
        self.contador.grid(row=0, column=1, sticky="e")

        # painel de conciliação
        self.painel = ctk.CTkScrollableFrame(corpo, width=350, fg_color=T.SURFACE, corner_radius=16,
                                             border_width=1, border_color=T.OURO_ESCURO,
                                             scrollbar_button_color=T.SURFACE_3,
                                             scrollbar_button_hover_color=T.BORDA)
        self.painel.grid(row=0, column=1, sticky="nsew")
        self._montar_painel(self.painel)

        # ---------------- barra de decisão
        self.decisao = Card(self, destaque=True)
        self.decisao.grid(row=2, column=0, sticky="ew", padx=32, pady=(16, 22))
        self.decisao.grid_columnconfigure(0, weight=1)
        txt = ctk.CTkFrame(self.decisao, fg_color="transparent")
        txt.grid(row=0, column=0, sticky="w", padx=22, pady=14)
        self.pergunta = rotulo(txt, "Os valores estão corretos?", F.secao)
        self.pergunta.pack(anchor="w")
        self.pergunta_sub = rotulo(txt, "Confirme para liberar a exportação e a visualização.", F.pequena, T.TEXTO_2)
        self.pergunta_sub.pack(anchor="w")
        self.acoes = ctk.CTkFrame(self.decisao, fg_color="transparent")
        self.acoes.grid(row=0, column=1, sticky="e", padx=18)
        self._acoes_normais()

    FIXAS = {"marca": 30, "data": 92, "parcela": 66, "cat": 148, "tipo": 102, "valor": 112}

    def _ajustar_colunas(self, e):
        desc = max(160, e.width - sum(self.FIXAS.values()) - 4)
        for c, w in self.FIXAS.items():
            self.tree.column(c, width=w, stretch=False)
        self.tree.column("desc", width=desc, stretch=False)

    # --------------------------------------------------------------- painel
    def _montar_painel(self, p):
        p.grid_columnconfigure(0, weight=1)
        rotulo(p, "CONCILIAÇÃO", F.rotulo, T.OURO).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 2))
        rotulo(p, "Total da fatura", F.pequena, T.TEXTO_2).grid(row=1, column=0, sticky="w", padx=14)
        linha_total = ctk.CTkFrame(p, fg_color="transparent")
        linha_total.grid(row=2, column=0, sticky="ew", padx=14)
        linha_total.grid_columnconfigure(0, weight=1)
        self.lbl_total = rotulo(linha_total, "—", F.numero_g)
        self.lbl_total.grid(row=0, column=0, sticky="w")
        botao(linha_total, "Editar", self.editar_total, "fantasma", altura=28, width=64,
              font=F.pequena_b, text_color=T.OURO).grid(row=0, column=1, sticky="e")
        self.lbl_origem_total = rotulo(p, "", F.pequena, T.MUDO)
        self.lbl_origem_total.grid(row=3, column=0, sticky="w", padx=14)

        self.medidor = Medidor(p, bg=T.SURFACE)
        self.medidor.grid(row=4, column=0, sticky="ew", padx=14, pady=(12, 6))

        self.linhas_valor = {}
        itens = [("compras", "Compras e débitos", "+"), ("creditos", "Créditos e estornos", "−"),
                 ("extraido", "Soma extraída", "="), ("diferenca", "Diferença para o total", "Δ")]
        grade = ctk.CTkFrame(p, fg_color=T.SURFACE_2, corner_radius=12)
        grade.grid(row=5, column=0, sticky="ew", padx=14, pady=(6, 0))
        grade.grid_columnconfigure(1, weight=1)
        for k, (chave, nome, sinal) in enumerate(itens):
            if chave == "extraido":
                divisoria(grade).grid(row=2 * k - 1, column=0, columnspan=3, sticky="ew", padx=12)
            ctk.CTkLabel(grade, text=sinal, font=F.corpo_b, text_color=T.OURO, width=18).grid(
                row=2 * k, column=0, padx=(12, 6), pady=7)
            rotulo(grade, nome, F.corpo_b if chave in ("extraido", "diferenca") else F.corpo,
                   T.TEXTO if chave in ("extraido", "diferenca") else T.TEXTO_2).grid(row=2 * k, column=1, sticky="w")
            v = rotulo(grade, "—", F.corpo_b, anchor="e")
            v.grid(row=2 * k, column=2, sticky="e", padx=12)
            self.linhas_valor[chave] = v

        self.caixa_status = ctk.CTkFrame(p, fg_color=T.BOM_FUNDO, corner_radius=12)
        self.caixa_status.grid(row=6, column=0, sticky="ew", padx=14, pady=(10, 0))
        self.lbl_status = rotulo(self.caixa_status, "", F.pequena_b, T.BOM, wraplength=296)
        self.lbl_status.pack(fill="x", padx=14, pady=10)

        self.lbl_pagamentos = rotulo(p, "", F.pequena, T.MUDO, wraplength=330)
        self.lbl_pagamentos.grid(row=7, column=0, sticky="w", padx=14, pady=(8, 0))

        rotulo(p, "DADOS DA FATURA", F.rotulo, T.MUDO).grid(row=8, column=0, sticky="w", padx=14, pady=(18, 6))
        self.dados = {}
        grade2 = ctk.CTkFrame(p, fg_color="transparent")
        grade2.grid(row=9, column=0, sticky="ew", padx=14)
        grade2.grid_columnconfigure(1, weight=1)
        for k, nome in enumerate(["Vencimento", "Titular", "Cartão", "Pagamento mínimo", "Limite total",
                                  "Limite utilizado", "Lançamentos"]):
            rotulo(grade2, nome, F.pequena, T.TEXTO_2).grid(row=k, column=0, sticky="w", pady=3)
            v = rotulo(grade2, "—", F.pequena_b, anchor="e")
            v.grid(row=k, column=1, sticky="e", pady=3)
            self.dados[nome] = v

        rotulo(p, "AVISOS", F.rotulo, T.MUDO).grid(row=10, column=0, sticky="w", padx=14, pady=(18, 6))
        self.avisos = ctk.CTkFrame(p, fg_color="transparent")
        self.avisos.grid(row=11, column=0, sticky="ew", padx=14, pady=(0, 16))

    # --------------------------------------------------------------- ciclo
    def on_show(self):
        s = self.app.sessao
        nomes = [self._curto(i.nome) for i in s.itens]
        if len(nomes) > 1:
            self.seletor.configure(values=nomes)
            self.seletor.set(nomes[s.atual])
            self.seletor.grid()
        else:
            self.seletor.grid_remove()
        self.revisao = False
        self._acoes_normais()
        self.atualizar()

    @staticmethod
    def _curto(nome: str, n: int = 22) -> str:
        return nome if len(nome) <= n else nome[: n - 1] + "…"

    def _trocar_fatura(self, valor):
        nomes = [self._curto(i.nome) for i in self.app.sessao.itens]
        self.app.sessao.atual = nomes.index(valor)
        self.seletor.set(valor)
        if self.busca.get():
            self.busca.delete(0, "end")
        self.filtro.set("Todos")
        self.atualizar()

    # --------------------------------------------------------------- tabela
    def _preencher(self):
        item = self.app.sessao.item
        self.tree.delete(*self.tree.get_children())
        if item is None:
            return
        df = item.df
        termo = self.busca.get().strip().lower() if self.busca.get() != self.busca.cget("placeholder_text") else ""
        filtro = self.filtro.get()
        k = 0
        for idx, r in df.iterrows():
            exc = idx in item.excluidos
            if filtro == "Compras" and (r.Valor <= 0 or exc):
                continue
            if filtro == "Créditos" and (r.Valor >= 0 or exc):
                continue
            if filtro == "Parcelados" and not r.Parcela:
                continue
            if filtro == "Internacionais" and r.Tipo != "Internacional":
                continue
            if filtro == "Excluídos" and not exc:
                continue
            if termo and termo not in f"{r.Descricao} {r.Categoria_banco}".lower():
                continue
            tags = ["par" if k % 2 == 0 else "impar"]
            if exc:
                tags.append("excluido")
            elif r.Valor < 0:
                tags.append("credito")
            self.tree.insert("", "end", iid=str(idx), tags=tags, values=(
                "✕" if exc else "", r.Data.strftime("%d/%m/%Y"), r.Descricao, r.Parcela or "",
                r.Categoria_banco or "—", r.Tipo, brl(r.Valor)))
            k += 1
        n_exc = len(item.excluidos)
        self.contador.configure(text=f"{plural(len(df) - n_exc, 'lançamento')} na soma"
                                     + (f"  ·  {n_exc} excluído(s)" if n_exc else ""))

    def _alternar_linha(self, _e=None):
        sel = self.tree.focus() or (self.tree.selection() or [None])[0]
        item = self.app.sessao.item
        if not sel or item is None:
            return
        item.alternar(int(sel))
        excluido = int(sel) in item.excluidos
        self.app.toast("Lançamento excluído da soma." if excluido else "Lançamento incluído de volta.",
                       "alerta" if excluido else "bom", 1800)
        self.atualizar(manter=sel)

    # --------------------------------------------------------------- atualização
    def atualizar(self, manter: str | None = None):
        item = self.app.sessao.item
        if item is None:
            return
        self._preencher()
        if manter and self.tree.exists(manter):
            self.tree.selection_set(manter)
            self.tree.focus(manter)
            self.tree.see(manter)
        f = item.fatura
        self.lbl_total.configure(text=brl(item.total), text_color=T.TEXTO if item.total else T.ALERTA)
        self.lbl_origem_total.configure(
            text="informado manualmente" if item.total_manual is not None
            else ("lido do PDF" if f.valor_total is not None else "não encontrado no PDF — clique em Editar"))
        self.medidor.definir(item.total, item.extraido, item.confere)
        self.linhas_valor["compras"].configure(text=brl(item.compras))
        self.linhas_valor["creditos"].configure(text=brl(item.creditos), text_color=T.BOM if item.creditos else T.TEXTO)
        self.linhas_valor["extraido"].configure(text=brl(item.extraido))
        dif = item.diferenca
        self.linhas_valor["diferenca"].configure(
            text=brl(dif), text_color=T.MUDO if dif is None else (T.BOM if item.confere else T.ALERTA))

        if dif is None:
            cor, fundo, msg = T.ALERTA, T.ALERTA_FUNDO, "Não achei o total no PDF. Clique em Editar e informe o valor da fatura para conciliar."
        elif item.confere:
            cor, fundo, msg = T.BOM, T.BOM_FUNDO, "✓  A soma dos lançamentos confere com o total da fatura."
        else:
            cor, fundo = T.ALERTA, T.ALERTA_FUNDO
            msg = (f"A soma difere do total em {brl(dif)}. Pode haver lançamento não lido, "
                   "encargo sem data ou linha duplicada — revise antes de confirmar.")
        self.caixa_status.configure(fg_color=fundo)
        self.lbl_status.configure(text=msg, text_color=cor)
        self.lbl_pagamentos.configure(
            text=(f"Pagamento da fatura anterior ({brl(f.pagamentos)}) fica fora da soma — "
                  "ele já aparece no extrato bancário.") if f.pagamentos else "")

        valores = {"Vencimento": data_br(f.vencimento), "Titular": (f.titular or "—").title(),
                   "Cartão": cartao(f.numero_cartao), "Pagamento mínimo": brl(f.pagamento_minimo),
                   "Limite total": f.limite_total if isinstance(f.limite_total, str) else brl(f.limite_total),
                   "Limite utilizado": brl(f.limite_utilizado), "Lançamentos": str(len(item.ativos))}
        for k, v in valores.items():
            self.dados[k].configure(text=v)

        for w in self.avisos.winfo_children():
            w.destroy()
        avisos = [a for a in f.avisos if not a.startswith(("Soma extraída difere", "Pagamento(s) da fatura"))]
        if not avisos:
            rotulo(self.avisos, "Nenhum aviso.", F.pequena, T.MUDO).pack(anchor="w")
        for a in avisos:
            rotulo(self.avisos, f"!  {a}", F.pequena, T.ALERTA, wraplength=330).pack(anchor="w", pady=2)

        if item.confirmada:
            definir_badge(self.badge, "✓  Confirmada", "bom")
        elif item.confere:
            definir_badge(self.badge, "Confere com o total", "bom")
        elif dif is None:
            definir_badge(self.badge, "Total não identificado", "alerta")
        else:
            definir_badge(self.badge, f"Diferença {brl(dif)}", "alerta")

    # --------------------------------------------------------------- decisão
    def _limpar_acoes(self):
        for w in self.acoes.winfo_children():
            w.destroy()

    def _acoes_normais(self):
        self._limpar_acoes()
        self.pergunta.configure(text="Os valores estão corretos?")
        self.pergunta_sub.configure(text="Confirme para liberar a exportação e a visualização.")
        botao(self.acoes, "Não, revisar", self._modo_revisao, "secundario", altura=44, width=150).pack(side="left", padx=6)
        botao(self.acoes, "Sim, confirmar   ✓", self.confirmar, "primario", altura=44, width=190).pack(side="left", padx=6)

    def _modo_revisao(self):
        self.revisao = True
        self._limpar_acoes()
        self.pergunta.configure(text="Modo revisão")
        self.pergunta_sub.configure(text="Exclua linhas com duplo clique, ajuste o total ou gere o texto para diagnóstico.")
        for texto, cmd in [("Editar total", self.editar_total),
                           ("Exportar texto", self.app.diagnostico_atual),
                           ("Trocar PDF", lambda: self.app.mostrar("inicio"))]:
            botao(self.acoes, texto, cmd, "secundario", altura=40).pack(side="left", padx=4)
        botao(self.acoes, "Conferir de novo", self._sair_revisao, "primario", altura=40).pack(side="left", padx=(10, 4))

    def _sair_revisao(self):
        self.revisao = False
        self._acoes_normais()

    def editar_total(self):
        item = self.app.sessao.item
        if item is None:
            return
        d = Dialogo(self.app, "Total da fatura",
                    "Digite o valor total desta fatura, como aparece na primeira página do PDF.",
                    [("Cancelar", None, "secundario"), ("Salvar", True, "primario")], campo="texto",
                    dica="Exemplo: 8.991,09  ·  deixe vazio para voltar ao valor lido do PDF.", glifo="R$")
        if item.total is not None:
            d.entrada.insert(0, f"{item.total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        valor = d.mostrar()
        if valor is None:
            return
        if not valor.strip():
            item.total_manual = None
        else:
            try:
                item.total_manual = ler_brl(valor)
            except ValueError:
                self.app.toast("Valor inválido. Use o formato 1.234,56.", "ruim")
                return
        item.confirmada = False
        self.atualizar()

    def confirmar(self):
        s = self.app.sessao
        item = s.item
        if item is None:
            return
        if not item.confere:
            msg = ("O total da fatura não foi identificado, então a soma não pôde ser conferida."
                   if item.diferenca is None else
                   f"A soma extraída difere do total da fatura em {brl(item.diferenca)}.")
            r = Dialogo(self.app, "Confirmar mesmo assim?", msg + "\n\nA diferença ficará registrada na aba Avisos do Excel.",
                        [("Voltar e revisar", None, "secundario"), ("Confirmar mesmo assim", "ok", "primario")],
                        glifo="!", tipo="alerta").mostrar()
            if r != "ok":
                return
        item.confirmada = True
        prox = s.proximo_pendente
        if prox is None:
            self.app.mostrar("concluido")
            return
        s.atual = prox
        self.app.toast(f"{item.nome} confirmada. Agora confira a próxima.", "bom")
        self.on_show()
