@echo off
echo === Pushing AI Investment Dashboard to GitHub ===
cd /d "%~dp0"

echo Initializing git...
git init
git branch -M main

echo Adding all files...
git add -A

echo Committing...
git commit -m "Initial commit: AI Investment Landscape Dashboard with 84 companies across 5 categories"

echo Setting remote...
git remote add origin https://github.com/armanamirzhan/ai_invest_dashboard.git

echo Pushing to GitHub...
git push -u origin main

echo.
echo === Done! Now open a Codespace: ===
echo https://github.com/armanamirzhan/ai_invest_dashboard
echo Click the green "Code" button, then "Codespaces" tab, then "Create codespace on main"
pause
