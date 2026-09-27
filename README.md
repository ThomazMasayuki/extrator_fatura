**Extrator de Faturas**

App desktop em Python que lê faturas de cartão em PDF, extrai os lançamentos, confronta a soma com o total da fatura e exporta para Excel. Todo o processamento é local.

**Funcionalidades**

Leitura genérica de layouts: qualquer linha DATA  DESCRIÇÃO  VALOR (BB, Itaú, Nubank e outros), com data em 27/08, 27/08/2026 ou 27 AGO.
Parcelas, créditos e internacionais: reconhece 04/10, estornos (−R$, 40,00-, sufixo C) e compras no exterior.
Resumo da fatura: vencimento, total, mínimo e limites, inclusive quando o valor está numa caixa separada do rótulo.
Conciliação: compara a soma extraída com o total e mostra a diferença. O pagamento da fatura anterior fica fora da soma.
PDF com senha: pede a senha, reaproveita na sessão (só em memória) e gera cópia sem senha, se você quiser.
Conferência antes de exportar: você confirma os valores, exclui linhas com duplo clique ou ajusta o total manualmente.
Análise visual: gastos por categoria, maiores estabelecimentos, ritmo de gastos e parcelas já comprometidas.
Instalação

**Requisitos: Python 3.10+ e Tk** 

Se for usar windows (instalação normal da versão mais recente do Tkinter)
Se for usar linux -> (sudo pacman -S tk no Arch/Omarchy).


**Para rodar no terminal do OS**
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python app_fatura.py (Abre o App)

**Fluxo: Selecionar → Extrair → Conferir → Exportar.**

**Linha de comando, sem interface:**

bash
python fatura_extractor.py fatura.pdf --conta itau --saida ./saida
python fatura_extractor.py fatura.pdf --senha 12345                    # PDF protegido
python fatura_extractor.py fatura.pdf --remover-senha --senha 12345    # só gera cópia sem senha
python fatura_extractor.py fatura.pdf --texto                          # texto bruto p/ diagnóstico
Saída

Um arquivo conta__AAAA-MM.xlsx (mês do vencimento) com as abas:

**Aba	Conteúdo**
Lancamentos	Data, Descricao, Valor, Parcela, Categoria_banco, Tipo, Data_compra
Resumo	Dados da fatura, soma extraída e diferença
Por Categoria	Total e quantidade por categoria do banco
Avisos	Linhas ignoradas, ajustes manuais e divergências

Valores positivos são compras e negativos são créditos. Cada parcela é datada no mês em que é cobrada.

**Estrutura**
fatura_extractor.py   motor de extração (sem interface)
app_fatura.py         ponto de entrada do app
ui/
├── app.py            janela, navegação, senhas, extração e exportação
├── tema.py           paleta, fontes e estilos
├── componentes.py    cartões, diálogos, medidor e gráficos
├── estado.py         sessão e preferências (~/.config/extrator-fatura.json)
└── telas/            boas-vindas, início, processamento, conferência, concluído, análise

**Observações**
PDFs escaneados (imagem) não têm texto extraível e exigiriam OCR.
Se um layout não fechar a conciliação, use Diagnóstico para gerar o .txt e ajustar o leitor.
