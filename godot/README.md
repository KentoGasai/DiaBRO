# DiaBRO — Godot 4

Порт изометрической ARPG с Pygame ([`main.py`](../main.py)) на **Godot 4 + GDScript**.

## Требования

- [Godot 4.2+](https://godotengine.org/download)

## Запуск

1. Откройте [`project.godot`](project.godot) в Godot Editor.
2. Нажмите **F5** (главная сцена: `scenes/main.tscn`).

Стартовый уровень: **`wilderness`** (карта 64×64, генерация один раз при загрузке).

## Синхронизация ассетов и данных

После правок в Pygame или веб-редакторе врагов **обязательно** синхронизируйте данные:

```powershell
.\sync_data.ps1
```

Копирует `game/images/`, `game/enemy_types.json` и `game/levels/` в `godot/assets/` и `godot/data/`.

В Godot-версии в меню паузы: **«Противники»** → **«Обновить список»** (перечитает `data/enemy_types.json`).

Типы врагов из веб-редактора (`tools/enemy_editor`) сохраняются в `game/enemy_types.json` — без `sync_data.ps1` Godot их не увидит.

## Уровни (фиксированный размер)

Файлы в `data/levels/*.json`:

| Поле | Описание |
|------|----------|
| `width`, `height` | Размер карты в тайлах |
| `source: "tiles"` | Готовая раскладка в `tiles` |
| `source: "generator"` | Заполнение через `LevelGenerator` (seed, preset) |
| `player_spawn` | `[x, y]` старта игрока |
| `spawn_points` | Точки врагов/NPC (`kind`, координаты) |
| `structures` | Задел под стены, данжи (пока пустой массив) |

Пример: [`data/levels/wilderness.json`](data/levels/wilderness.json).

Бесконечной подгрузки тайлов при беге **нет** — `TileMapLayer` собирается один раз при смене уровня.

## Управление

| Клавиша | Действие |
|---------|----------|
| WASD | Движение |
| ЛКМ | Атака к курсору |
| 2 | Ближний / дальний бой |
| 1, 3–9 | Атака (способности) |
| ESC | Пауза / меню |
| R | Перезапуск (Game Over) |

В меню паузы: уровни, спавн врагов, настройки спавна по точкам уровня.

## Структура

| Путь | Назначение |
|------|------------|
| `autoload/` | IsoMath, GameState, EnemyRegistry |
| `scripts/` | Игровая логика (порт `game/*.py`) |
| `scripts/level_generator.gd` | Генерация фиксированной карты |
| `scenes/` | Сцены Godot |
| `assets/sprites/` | Спрайты (копия `game/images/`) |
| `data/` | `enemy_types.json`, уровни JSON |

## Отличия от Pygame-версии

- Один `World` вместо `LocationManager` + разрозненных слоёв.
- Тайлы через `TileMapLayer` (изометрический TileSet), без стриминга.
- Godot: фиксированные уровни; Pygame: по-прежнему может использовать бесконечный мир.
- Веб-редактор врагов: [`tools/enemy_editor/`](../tools/enemy_editor/) — `sync_data.ps1`.

Оригинальная Pygame-версия: `python main.py` из корня репозитория.
