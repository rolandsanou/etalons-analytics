#!/usr/bin/env bash
# Publish the generated site to GitHub Pages.
#
# Pages currently serves the `gh-pages` branch (the site/ folder pushed at its
# root) because GitHub Actions is unavailable on this account. Once Actions runs
# again, .github/workflows/pages.yml deploys on every push to main and this
# script is no longer needed — switch Pages back to "GitHub Actions" in the
# repository settings.
set -euo pipefail

cd "$(dirname "$0")/.."

python -m etl load
python tools/build_site.py
python tools/check_links.py

git add site data
git diff --cached --quiet || git commit -m "Rebuild site data and pages"
git push origin main
git subtree push --prefix site origin gh-pages

echo "deployed: https://rolandsanou.github.io/etalons-analytics/"
