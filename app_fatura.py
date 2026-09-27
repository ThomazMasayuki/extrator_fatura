"""Extrator de Faturas — abre o aplicativo.

    python app_fatura.py

Estrutura:
    fatura_extractor.py   motor de extração (também roda por linha de comando)
    ui/app.py             janela principal, navegação, senhas, extração e exportação
    ui/tema.py            paleta, fontes e estilo
    ui/componentes.py     cartões, botões, diálogos, medidor, gráficos
    ui/estado.py          sessão, ajustes do usuário e configuração
    ui/telas/             boas-vindas, início, processamento, conferência, concluído, visualizar
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import customtkinter  # noqa: F401
except ImportError:
    sys.exit("Falta o customtkinter. Rode:  pip install -r requirements.txt")

from ui.app import main  # noqa: E402

if __name__ == "__main__":
    main()
