@echo off
git add .
git commit -m "Fix TOTP to try using short secret instead of empty"
git push origin main
echo Changes pushed to GitHub!
pause
