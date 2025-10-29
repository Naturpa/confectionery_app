@echo off
chcp 65001
echo === СБОРКА С ИСПРАВЛЕННЫМИ ПУТЯМИ ===
pyinstaller --onefile --console --name ConfectioneryApp --add-data "ui;ui" --add-data "media;media" main.py
if exist "dist\ConfectioneryApp.exe" (
    echo ✅ УСПЕХ! Запускаем...
    cd dist
    ConfectioneryApp.exe
    cd ..
) else (
    echo ❌ ОШИБКА
)
pause