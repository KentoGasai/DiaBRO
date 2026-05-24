# DiaBRO — Godot 4

Порт изометрической ARPG с Pygame ([`main.py`](../main.py)) на **Godot 4 + GDScript**.

## Требования

- [Godot 4.2+](https://godotengine.org/download)

## Запуск

1. Откройте [`project.godot`](project.godot) в Godot Editor.
2. Нажмите **F5** (главная сцена: `scenes/main.tscn`).

Стартовый уровень: **`wilderness`** (карта 64×64).

При **F5** сначала показывается экран загрузки: генерация биомов и сборка тайлмапа Kenney, затем старт игры.

### Тайлы Kenney (биомы)

Паки лежат в [`assets/sprites/bioms_tiles/`](assets/sprites/bioms_tiles/) (например `kenney_isometricMiniatureFarm`, `kenney_isometricDungeon`).  
Размер клетки: **256×128** (ромб), спрайт **256×512** — как в [Kenney Knowledge Base](https://kenney.nl/knowledge-base).

Биомы задаются в [`scripts/level_generator.gd`](scripts/level_generator.gd) (поля `pack` + `base`): **9 зон** (пустыня, лес, библиотека, подземелье и т.д.).

**Окружение** (заборы, стены, крыши, мебель, кукуруза, бочки) — [`scripts/world_props.gd`](scripts/world_props.gd), пулы в [`scripts/kenney_prop_catalog.gd`](scripts/kenney_prop_catalog.gd). На карте появляются одиночные пропсы и мини-«здания» (2×2 стены + крыша / комната из камня / угол библиотеки).

Старые уровни JSON с `grass_green_128x64` нужно перегенерировать или перевести на Kenney-формат (`pack`, `base`, `facing`).

## Спрайты и анимации (редактор Godot)

Анимации — **`AnimatedSprite2D` + `SpriteFrames`** (встроенная панель Godot). Код только выбирает направление (`walk_3`, `attack_melee_5` …).

### Первичная генерация `.tres` из PNG

После `sync_data.ps1` или смены листов:

1. Откройте сцену [`scenes/tools/sprite_frames_generator.tscn`](scenes/tools/sprite_frames_generator.tscn).
2. В инспекторе нажмите **«Сгенерировать все SpriteFrames (.tres)»**.

Либо откройте [`editor/regenerate_sprite_frames.gd`](editor/regenerate_sprite_frames.gd) → **Файл → Запустить** (EditorScript).

Создаются:

| Файл | Источник |
|------|----------|
| `assets/sprites/frames/player.tres` | тело + меч |
| `assets/sprites/frames/enemies/<id>.tres` | каждый тип из `enemy_types.json` |

### Правка в UI Godot

1. Сгенерируйте `player.tres` (см. выше).
2. Откройте [`scenes/entities/player.tscn`](scenes/entities/player.tscn) → узел **Player** → поле **Editor Sprite Frames** → перетащите `player.tres`  
   *(или **AnimatedSprite2D → Sprite Frames → Редактировать**)*.
3. Меняйте FPS, loop, кадры, порядок анимаций — как в обычном Godot-проекте.

Для врага: откройте соответствующий `assets/sprites/frames/enemies/skeleton.tres` или назначьте его на `AnimatedSprite2D` в префабе.

Логика направления (8 сторон) остаётся в `player.gd` / `enemy.gd`; имена анимаций: `walk_0`…`walk_7`, `attack_melee_*`, `attack_ranged_*`, `hurt_*`, `death_*`.

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
| `props` | Окружение Kenney (генерируется вместе с уровнем) |
| `structures` | Зарезервировано для JSON-уровней |

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
| `scripts/sprite_frames_pipeline.gd` | PNG → `.tres` для редактора |
| `assets/sprites/frames/` | SpriteFrames ресурсы (редактируются в Godot) |
| `scenes/tools/sprite_frames_generator.tscn` | Кнопка пересборки `.tres` |
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
