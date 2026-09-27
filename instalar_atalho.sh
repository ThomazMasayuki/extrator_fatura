#!/usr/bin/env bash
# Cria o atalho "Extrator de Faturas" no menu de aplicativos (Omarchy/Walker, GNOME, KDE...).
# Rode a partir da raiz do projeto, com o venv já criado:  bash extrator/instalar_atalho.sh
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PY="$RAIZ/.venv/bin/python"
[ -x "$PY" ] || { echo "Crie o venv antes: python -m venv .venv && .venv/bin/pip install -r requirements.txt"; exit 1; }
"$PY" -c "import tkinter" 2>/dev/null || { echo "Tkinter ausente. No Arch/Omarchy: sudo pacman -S tk"; exit 1; }

DESTINO="$HOME/.local/share/applications/extrator-fatura.desktop"
mkdir -p "$(dirname "$DESTINO")"
cat > "$DESTINO" <<DESK
[Desktop Entry]
Type=Application
Name=Extrator de Faturas
Comment=Extrai lançamentos de faturas de cartão (PDF) para Excel
Exec=$PY $RAIZ/extrator/app_fatura.py
Path=$RAIZ
Icon=x-office-spreadsheet
Terminal=false
Categories=Office;Finance;
DESK
chmod +x "$DESTINO"
update-desktop-database "$(dirname "$DESTINO")" 2>/dev/null || true
echo "Atalho criado: procure 'Extrator de Faturas' no launcher (Super + Space)."
