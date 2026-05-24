# DiaBRO — Godot 4

Порт изометрической ARPG с Pygame ([`main.py`](../main.py)) на **Godot 4 + GDScript**.

## Требования

- [Godot 4.2+](https://godotengine.org/download)

## Запуск

1. Откройте [`project.godot`](project.godot) в Godot Editor.
2. Нажмите **F5** (главная сцена: `scenes/main.tscn`).

## Синхронизация ассетов и данных

После правок в Pygame или веб-редакторе врагов **обязательно** синхронизируйте данные:

```powershell
.\sync_data.ps1
```

Копирует `game/images/`, `game/enemy_types.json` и `game/levels/` в `godot/assets/` и `godot/data/`.

В Godot-версии в меню паузы: **«Противники»** → **«Обновить список»** (перечитает `data/enemy_types.json`).

Типы врагов из веб-редактора (`tools/enemy_editor`) сохраняются в `game/enemy_types.json` — без `sync_data.ps1` Godot их не увидит.

## Управление

| Клавиша | Действие |
|---------|----------|
| WASD | Движение |
| ЛКМ | Атака к курсору |
| 2 | Ближний / дальний бой |
| 1, 3–9 | Атака (способности) |
| ESC | Пауза / меню |
| R | Перезапуск (Game Over) |

В меню паузы: уровни, спавн врагов, настройки процедурного спавна.

## Структура

| Путь | Назначение |
|------|------------|
| `autoload/` | IsoMath, GameState, EnemyRegistry |
| `scripts/` | Игровая логика (порт `game/*.py`) |
| `scenes/` | Сцены Godot |
| `assets/sprites/` | Спрайты (копия `game/images/`) |
| `data/` | `enemy_types.json`, уровни JSON |

## Отличия от Pygame-версии

- Один `World` вместо `LocationManager` + разрозненных слоёв.
- Тайлы через `TileMapLayer` (изометрический TileSet).
- Веб-редактор врагов по-прежнему в [`tools/enemy_editor/`](../tools/enemy_editor/) — сохраняйте JSON и запускайте `sync_data.ps1`.

Оригинальная Pygame-версия: `python main.py` из корня репозитория.
