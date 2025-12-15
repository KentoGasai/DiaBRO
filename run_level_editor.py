#!/usr/bin/env python3
"""
Запуск редактора уровней DiaBRO
"""

import sys
import os

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 50)
    print("   DiaBRO Level Editor")
    print("=" * 50)
    print()
    print("Управление:")
    print("  ЛКМ (зажать) - Рисовать тайлы")
    print("  ПКМ (зажать) - Стирать тайлы")
    print("  СКМ          - Перемещение камеры")
    print("  Колесо       - Сменить тайл")
    print("  Ctrl+Колесо  - Масштаб (zoom)")
    print("  Shift+Колесо - Изменить размер области размещения")
    print("  ← →          - Сменить тайлсет")
    print("  G            - Показать/скрыть сетку")
    print("  E            - Режим ластика")
    print("  Ctrl+S       - Сохранить уровень")
    print("  ESC          - Выход")
    print()
    print("=" * 50)
    
    from tools.level_editor.editor import main as run_editor
    run_editor()

if __name__ == "__main__":
    main()