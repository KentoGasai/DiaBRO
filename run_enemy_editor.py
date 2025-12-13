#!/usr/bin/env python
"""
Запуск редактора врагов DiaBRO

Использование:
    python run_enemy_editor.py

Откройте в браузере: http://localhost:5000
"""
import sys
import os

# Добавляем путь к tools
sys.path.insert(0, os.path.dirname(__file__))

# Проверяем Flask
try:
    import flask
except ImportError:
    print("❌ Flask не установлен!")
    print("Установите: pip install flask")
    sys.exit(1)

# Запускаем сервер
from tools.enemy_editor.server import app

if __name__ == '__main__':
    print("=" * 50)
    print("🎮 DiaBRO Enemy Editor")
    print("=" * 50)
    print("🌐 Откройте в браузере: http://localhost:5000")
    print("⏹️  Нажмите Ctrl+C для остановки")
    print("=" * 50)
    app.run(debug=True, port=5000)