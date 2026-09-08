#!/bin/bash
set -e

echo "Setting up Luna..."

mkdir -pv "$HOME/.local/luna"
mkdir -pv "$HOME/.local/lunasource"
mkdir -pv "$HOME/.local/lunaorigin"

pip install --break-system-packages git+https://github.com/Neonwave175/luna.git

echo ""
echo "Adding ~/.local/luna to PATH in ~/.zshrc..."

LINE='export PATH="$HOME/.local/luna:$PATH"'
if ! grep -qF "$LINE" "$HOME/.zshrc" 2>/dev/null; then
    echo "$LINE" >> "$HOME/.zshrc"
    echo "Added. Run 'source ~/.zshrc' or open a new terminal to use it."
else
    echo "Already present in ~/.zshrc, skipping."
fi
