#!/bin/bash
# setup_repo.sh — one-time: turn this folder into the GitHub repo and push it.
# Prereqs: (1) Ayan (AyanArora29) creates an EMPTY public repo named use-it-or-lose-it on github.com (no README/license);
#          (2) git is installed and you are logged in (git config user.name / user.email set; GitHub auth via browser prompt or SSH).
# Usage:   cd ~/Documents/MIT_Sloan_2026/repo && bash setup_repo.sh [https|ssh]
set -e
MODE=${1:-https}
if [ "$MODE" = "ssh" ]; then REMOTE="git@github.com:AyanArora29/use-it-or-lose-it.git"; else REMOTE="https://github.com/AyanArora29/use-it-or-lose-it.git"; fi
git init -b main
git add .
git commit -m "Initial import: pre-registered methods, data pipeline, engine, tutorials" || true
git remote add origin "$REMOTE" 2>/dev/null || git remote set-url origin "$REMOTE"
git push -u origin main
echo "Pushed. Now on github.com: Settings → Actions → General → allow all actions; then Actions tab → 'nightly-rebuild' → Run workflow (first run pulls data; ~1–2 h)."
