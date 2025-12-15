"""
Основной файл игры - изометрическая игра в стиле Diablo
"""
import pygame
import sys
import time
import math
import random
from game.isometric import IsometricConverter
from game.input_handler import InputHandler
from game.player import Player
from game.camera import Camera
from game.combat import CombatSystem
from game.location import Location, LocationManager
from game.enemy import Enemy, create_enemy, get_enemy_types, reload_enemy_types
from game.level import LevelManager
from game.fog_of_war import FogOfWar

# Константы
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)


class Game:
    """Главный класс игры"""
    
    def __init__(self):
        # Инициализация Pygame
        pygame.init()
        
        # Включаем аппаратное ускорение и двойную буферизацию
        # HWSURFACE - использование видеопамяти
        # DOUBLEBUF - двойная буферизация для плавности
        try:
            self.screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.HWSURFACE | pygame.DOUBLEBUF
            )
            print("Hardware acceleration enabled")
        except:
            # Если аппаратное ускорение недоступно, используем обычный режим
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            print("Hardware acceleration not available, using software mode")
        
        pygame.display.set_caption("PyDiab - Изометрическая игра")
        # Включаем VSync для синхронизации с частотой обновления монитора
        self.clock = pygame.time.Clock()
        
        # Кэшированные шрифты (создаём один раз!)
        self.font_small = pygame.font.Font(None, 16)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Инициализация систем
        # Увеличенный масштаб для приближения камеры к персонажу
        self.iso_converter = IsometricConverter(tile_width=128, tile_height=64)
        self.input_handler = InputHandler()
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Создание персонажа
        self.player = Player(x=0, y=0, speed=8.0, max_health=100, max_mana=100)
        self.combat_system = CombatSystem()
        
        # Снаряды врагов
        self.enemy_projectiles = []
        
        # Создание локаций
        self.location_manager = LocationManager()
        self._setup_locations()
        
        # Менеджер уровней (тайловые карты)
        self.level_manager = LevelManager()
        self._load_default_level()
        
        # Туман войны
        self.fog_of_war = FogOfWar(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Миникарта (создаём поверхность один раз!)
        self.minimap_size = 150
        self.minimap_radius = 200
        self.minimap_surface = pygame.Surface((self.minimap_size, self.minimap_size), pygame.SRCALPHA)
        pygame.draw.rect(self.minimap_surface, (0, 0, 0, 180), (0, 0, self.minimap_size, self.minimap_size))
        pygame.draw.rect(self.minimap_surface, WHITE, (0, 0, self.minimap_size, self.minimap_size), 2)
        
        # Состояние игры
        self.running = True
        self.game_over = False
        self.paused = False
        self.last_time = time.time()
        
        # Режим врагов (по умолчанию выключен)
        self.enemies_enabled = False
        
        # Настройки спавна врагов (можно менять динамически)
        self.enemy_spawn_frequency = 2.0  # Интервал проверки спавна в секундах (частота)
        self.max_enemies = 12  # Максимальное количество врагов одновременно
        
        # Кэш позиции для оптимизации обновления тайлов
        self.last_tile_update_pos = (0, 0)
        self.tile_update_threshold = 5.0  # Обновляем тайлы только при перемещении на 5+ тайлов
        
        # Кэш для спавна врагов (не спавним каждый кадр)
        self.last_enemy_spawn_pos = (0, 0)
        self.enemy_spawn_cooldown = 0.0  # Кулдаун между проверками спавна
        self.enemy_spawn_interval = self.enemy_spawn_frequency  # Используем настройку частоты
        
        # Меню паузы (будет обновляться динамически)
        self.menu_items = []
        self.selected_menu_item = 0
        self._build_menu_items()
        
        # Подменю уровней
        self.in_level_submenu = False
        self.selected_level = 0
        self.level_submenu_items = []
        
        # Подменю противников
        self.in_enemy_submenu = False
        self.enemy_submenu_items = []
        self.selected_enemy_type = 0
        self._build_enemy_submenu()
    
    def _setup_locations(self):
        """Настройка локаций"""
        # Начальная локация (открытое поле) - без врагов
        field_location = Location("field", background_color=(30, 40, 50))
        field_location.spawned = True
        
        self.location_manager.add_location(field_location)
        self.location_manager.set_location("field")
    
    def _load_default_level(self):
        """Загружает уровень по умолчанию"""
        # Загружаем процедурный уровень по умолчанию
        if self.level_manager.load_level("procedural"):
            print("Loaded procedural level")
        else:
            available = self.level_manager.get_available_levels()
            if available:
                self.level_manager.load_level(available[0])
                print(f"Loaded level: {available[0]}")
    
    def _spawn_enemies(self, count=5, enemy_type='default'):
        """
        Спавнит врагов вокруг игрока
        
        Args:
            count: Количество врагов
            enemy_type: Тип врага ('default', 'skeleton', 'zombie' и т.д.)
                       Если спрайты не найдены, используется fallback отрисовка
        
        Примеры использования со спрайтами:
            # Враги со спрайтами (поместите спрайты в game/images/enemy/)
            self._spawn_enemies(5, enemy_type='skeleton')
            
            # Или напрямую через Enemy:
            enemy = Enemy(x, y, sprite_path='game/images/enemy/skeleton.png')
            
            # Или через фабрику create_enemy:
            enemy = create_enemy(x, y, enemy_type='skeleton', max_health=50)
        """
        location = self.location_manager.get_current_location()
        if not location:
            return
        
        player_x, player_y = self.player.get_position()
        
        for i in range(count):
            angle = (2 * math.pi / count) * i + random.uniform(-0.3, 0.3)
            distance = random.uniform(3, 6)  # В мировых координатах
            x = player_x + math.cos(angle) * distance
            y = player_y + math.sin(angle) * distance
            
            # Используем фабрику для создания врагов с разными типами
            enemy = create_enemy(x, y, enemy_type=enemy_type, max_health=30, damage=8)
            location.enemies.append(enemy)
    
    def run(self):
        """Главный игровой цикл"""
        while self.running:
            # Расчет времени между кадрами
            current_time = time.time()
            dt = min(current_time - self.last_time, 0.1)
            self.last_time = current_time
            
            # Обработка событий
            self._handle_events()
            
            # Обновление
            if not self.game_over and not self.paused:
                self._update(dt)
            
            # Отрисовка
            self._draw()
            
            # Меню паузы поверх всего
            if self.paused:
                self._draw_pause_menu()
            
            # Обновление экрана с VSync для синхронизации с частотой обновления монитора
            # Это уменьшает разрывы экрана и использует возможности видеокарты
            pygame.display.flip()
            # VSync автоматически синхронизирует с частотой обновления монитора
            # при использовании DOUBLEBUF и HWSURFACE
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
    
    def _handle_events(self):
        """Обработка событий"""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_over:
                        self.running = False
                    else:
                        self.paused = not self.paused
                        self.selected_menu_item = 0
                        # Обновляем меню при открытии паузы
                        if self.paused:
                            self._build_menu_items()
                elif self.paused:
                    self._handle_menu_input(event)
                elif event.key == pygame.K_r and self.game_over:
                    self._restart_game()
        
        if not self.paused:
            self.input_handler.update(events)
    
    def _handle_menu_input(self, event):
        """Обработка ввода в меню"""
        if self.in_level_submenu:
            self._handle_level_submenu_input(event)
        elif self.in_enemy_submenu:
            self._handle_enemy_submenu_input(event)
        else:
            self._handle_main_menu_input(event)
    
    def _handle_main_menu_input(self, event):
        """Обработка ввода в главном меню"""
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.selected_menu_item = (self.selected_menu_item - 1) % len(self.menu_items)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.selected_menu_item = (self.selected_menu_item + 1) % len(self.menu_items)
        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
            # Изменение настроек влево
            selected_item = self.menu_items[self.selected_menu_item]
            if selected_item.get("type") == "setting":
                setting = selected_item.get("setting")
                if setting == "frequency":
                    # Уменьшить частоту спавна (увеличить интервал)
                    self.enemy_spawn_frequency = min(10.0, self.enemy_spawn_frequency + 0.5)
                elif setting == "max_enemies":
                    # Уменьшить максимальное количество
                    self.max_enemies = max(2, self.max_enemies - 2)
                # Обновляем интервал спавна
                self.enemy_spawn_interval = self.enemy_spawn_frequency
        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            # Изменение настроек вправо
            selected_item = self.menu_items[self.selected_menu_item]
            if selected_item.get("type") == "setting":
                setting = selected_item.get("setting")
                if setting == "frequency":
                    # Увеличить частоту спавна (уменьшить интервал)
                    self.enemy_spawn_frequency = max(0.5, self.enemy_spawn_frequency - 0.5)
                elif setting == "max_enemies":
                    # Увеличить максимальное количество
                    self.max_enemies = min(50, self.max_enemies + 2)
                # Обновляем интервал спавна
                self.enemy_spawn_interval = self.enemy_spawn_frequency
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            selected_item = self.menu_items[self.selected_menu_item]
            # Настройки не имеют действия, только действия выполняются
            if selected_item.get("type") == "action" and selected_item.get("action"):
                selected_item["action"]()
    
    def _handle_level_submenu_input(self, event):
        """Обработка ввода в подменю уровней"""
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.selected_level = (self.selected_level - 1) % len(self.level_submenu_items)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.selected_level = (self.selected_level + 1) % len(self.level_submenu_items)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.level_submenu_items[self.selected_level]["action"]()
        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self._close_level_submenu()
        elif event.key == pygame.K_ESCAPE:
            self._close_level_submenu()
    
    def _handle_enemy_submenu_input(self, event):
        """Обработка ввода в подменю противников"""
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.selected_enemy_type = (self.selected_enemy_type - 1) % len(self.enemy_submenu_items)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.selected_enemy_type = (self.selected_enemy_type + 1) % len(self.enemy_submenu_items)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.enemy_submenu_items[self.selected_enemy_type]["action"]()
        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self._close_enemy_submenu()
        elif event.key == pygame.K_ESCAPE:
            self._close_enemy_submenu()
    
    def _restart_game(self):
        """Перезапуск игры"""
        self.player = Player(x=0, y=0, speed=8.0, max_health=100, max_mana=100)
        self.combat_system = CombatSystem()
        self.enemy_projectiles = []  # Очищаем снаряды врагов
        self._setup_locations()
        self.game_over = False
        self.paused = False
        # Режим врагов остается как был (не сбрасываем)
        # Настройки спавна остаются как были (не сбрасываем)
    
    def _resume_game(self):
        """Продолжить игру"""
        self.paused = False
    
    def _quit_game(self):
        """Выход из игры"""
        self.running = False
    
    def _kill_all_enemies(self):
        """Убить всех врагов"""
        location = self.location_manager.get_current_location()
        if location:
            location.enemies.clear()
    
    def _build_menu_items(self):
        """Строит список пунктов меню (динамически, в зависимости от состояния)"""
        self.menu_items = [
            {"text": "Продолжить", "action": self._resume_game, "type": "action"},
            {"text": "Уровни ▶", "action": self._open_level_submenu, "type": "action"},
            {"text": "Противники ▶", "action": self._open_enemy_submenu, "type": "action"},
            {"text": self._get_enemy_mode_text, "action": self._toggle_enemy_mode, "type": "action"},
        ]
        
        # Если враги включены, добавляем настройки спавна
        if self.enemies_enabled:
            self.menu_items.append({
                "text": self._get_spawn_frequency_text, 
                "action": None, 
                "type": "setting",
                "setting": "frequency"
            })
            self.menu_items.append({
                "text": self._get_max_enemies_text, 
                "action": None, 
                "type": "setting",
                "setting": "max_enemies"
            })
        
        # Остальные пункты меню
        self.menu_items.extend([
            {"text": "Убить всех врагов", "action": self._kill_all_enemies, "type": "action"},
            {"text": "Перезапуск", "action": self._restart_game, "type": "action"},
            {"text": "Выход", "action": self._quit_game, "type": "action"},
        ])
    
    def _get_enemy_mode_text(self):
        """Возвращает текст для режима врагов"""
        return f"Враги: {'ВКЛ' if self.enemies_enabled else 'ВЫКЛ'}"
    
    def _get_spawn_frequency_text(self):
        """Возвращает текст для частоты спавна"""
        return f"Частота спавна: {self.enemy_spawn_frequency:.1f} сек"
    
    def _get_max_enemies_text(self):
        """Возвращает текст для максимального количества врагов"""
        return f"Макс. врагов: {self.max_enemies}"
    
    def _toggle_enemy_mode(self):
        """Переключает режим врагов"""
        self.enemies_enabled = not self.enemies_enabled
        # Если выключаем врагов, убиваем всех существующих
        if not self.enemies_enabled:
            self._kill_all_enemies()
        # Обновляем интервал спавна
        self.enemy_spawn_interval = self.enemy_spawn_frequency
        # Перестраиваем меню
        old_selection = self.selected_menu_item
        self._build_menu_items()
        # Восстанавливаем выбор (но не выходим за границы)
        self.selected_menu_item = min(old_selection, len(self.menu_items) - 1)
    
    def _build_enemy_submenu(self):
        """Создаёт подменю с типами врагов"""
        enemy_types = get_enemy_types()
        
        self.enemy_submenu_items = [
            {"text": "◀ Назад", "action": self._close_enemy_submenu, "type": None}
        ]
        
        for enemy_id, enemy_data in enemy_types.items():
            name = enemy_data.get('name', enemy_id)
            hp = enemy_data.get('max_health', 30)
            dmg = enemy_data.get('damage', 5)
            
            self.enemy_submenu_items.append({
                "text": f"{name} (HP:{hp} DMG:{dmg})",
                "action": lambda eid=enemy_id: self._spawn_enemy_type(eid),
                "type": enemy_id
            })
        
        self.enemy_submenu_items.append({
            "text": "🔄 Обновить список", 
            "action": self._refresh_enemy_types,
            "type": None
        })
    
    def _open_enemy_submenu(self):
        """Открывает подменю противников"""
        self._build_enemy_submenu()
        self.in_enemy_submenu = True
        self.selected_enemy_type = 0
    
    def _close_enemy_submenu(self):
        """Закрывает подменю противников"""
        self.in_enemy_submenu = False
    
    def _spawn_enemy_type(self, enemy_type):
        """Спавнит врага выбранного типа"""
        self._spawn_enemies(1, enemy_type=enemy_type)
    
    def _refresh_enemy_types(self):
        """Обновляет список типов врагов из конфига"""
        reload_enemy_types()
        self._build_enemy_submenu()
    
    def _open_level_submenu(self):
        """Открывает подменю уровней"""
        self._build_level_submenu()
        self.in_level_submenu = True
        self.selected_level = 0
    
    def _close_level_submenu(self):
        """Закрывает подменю уровней"""
        self.in_level_submenu = False
    
    def _build_level_submenu(self):
        """Строит подменю уровней"""
        self.level_submenu_items = []
        
        # Доступные уровни
        for level_name in self.level_manager.get_available_levels():
            current = self.level_manager.get_current_level()
            is_current = current and current.name == level_name
            prefix = "● " if is_current else ""
            self.level_submenu_items.append({
                "text": f"{prefix}{level_name}",
                "action": lambda name=level_name: self._load_level(name)
            })
        
        if not self.level_submenu_items:
            self.level_submenu_items.append({
                "text": "(нет уровней)",
                "action": lambda: None
            })
        
        self.level_submenu_items.append({
            "text": "← Назад",
            "action": self._close_level_submenu
        })
    
    def _load_level(self, level_name):
        """Загружает выбранный уровень"""
        if self.level_manager.load_level(level_name):
            print(f"Loaded level: {level_name}")
            self._close_level_submenu()
            self._resume_game()
    
    def _update(self, dt):
        """Обновление игровой логики"""
        current_location = self.location_manager.get_current_location()
        
        # Обновление камеры
        player_x, player_y = self.player.get_position()
        self.camera.update(player_x, player_y, self.iso_converter)
        
        # Подсветка врагов при наведении
        self._update_enemy_highlight(current_location)
        
        # Обработка атак игрока
        self._handle_player_attacks(current_location)
        
        # Обработка движения
        keyboard_input = self._get_keyboard_input()
        self.player.update(dt, keyboard_input=keyboard_input)
        
        # Обновление камеры после движения
        player_x, player_y = self.player.get_position()
        self.camera.update(player_x, player_y, self.iso_converter)
        
        # Обновление тумана войны
        self.fog_of_war.update(player_x, player_y)
        
        # Обновление процедурного спавна врагов (с кулдауном для производительности)
        self.enemy_spawn_cooldown -= dt
        # Обновляем интервал спавна из настроек (на случай изменения)
        self.enemy_spawn_interval = self.enemy_spawn_frequency
        if self.enemy_spawn_cooldown <= 0.0:
            # Проверяем, переместился ли игрок значительно
            dx = player_x - self.last_enemy_spawn_pos[0]
            dy = player_y - self.last_enemy_spawn_pos[1]
            distance_sq = dx * dx + dy * dy
            
            if distance_sq >= 10.0 * 10.0:  # Проверяем спавн только при перемещении на 10+ тайлов
                self._update_procedural_enemy_spawn(current_location, player_x, player_y)
                self.last_enemy_spawn_pos = (player_x, player_y)
                self.enemy_spawn_cooldown = self.enemy_spawn_interval
        
        
        # Обновление локации и получение атак врагов
        if current_location:
            self._update_location(current_location, dt, player_x, player_y)
        
        # Обновление системы боя
        self.combat_system.update(dt)
        
        # Проверка попаданий по врагам
        self._check_attack_hits(current_location)
        
        # Восстановление маны
        self.player.restore_mana(5 * dt)
        
        # Проверка смерти игрока
        if self.player.is_dead():
            self.game_over = True
    
    def _update_enemy_highlight(self, location):
        """Обновление подсветки врагов при наведении"""
        if not location or not location.enemies:
            return
        
        mouse_screen_x, mouse_screen_y = self.input_handler.get_mouse_pos()
        mouse_world_x, mouse_world_y = self.camera.screen_to_world(
            mouse_screen_x, mouse_screen_y, self.iso_converter
        )
        
        # Сброс подсветки
        for enemy in location.enemies:
            enemy.set_highlighted(False)
        
        # Проверка наведения
        for enemy in location.enemies:
            if enemy.check_mouse_hover(mouse_world_x, mouse_world_y):
                enemy.set_highlighted(True)
                break
    
    def _handle_player_attacks(self, location):
        """Обработка атак игрока"""
        player_x, player_y = self.player.get_position()
        enemies_list = location.enemies if location else []
        
        # ЛКМ - атака
        if self.input_handler.is_mouse_button_just_pressed('left'):
            mouse_screen_x, mouse_screen_y = self.input_handler.get_mouse_pos()
            attack_target_x, attack_target_y = self.camera.screen_to_world(
                mouse_screen_x, mouse_screen_y, self.iso_converter
            )
            if self.combat_system.perform_attack(
                player_x, player_y, self.player.angle,
                attack_target_x, attack_target_y, enemies_list
            ):
                # Запускаем анимацию атаки с поворотом к цели
                self.player.play_attack_animation(
                    is_melee=self.combat_system.is_melee_mode,
                    target_world_x=attack_target_x,
                    target_world_y=attack_target_y
                )
        
        # Клавиша 2 - переключение режима боя
        if self.input_handler.is_key_just_pressed(pygame.K_2):
            self.combat_system.set_melee_mode(not self.combat_system.is_melee_mode)
        
        # Способности (1, 3-9) - атакуют в направлении курсора
        ability_keys = [
            pygame.K_1, pygame.K_3, pygame.K_4, pygame.K_5,
            pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9
        ]
        for key in ability_keys:
            if self.input_handler.is_key_just_pressed(key):
                # Получаем позицию курсора для направления
                mouse_screen_x, mouse_screen_y = self.input_handler.get_mouse_pos()
                ability_target_x, ability_target_y = self.camera.screen_to_world(
                    mouse_screen_x, mouse_screen_y, self.iso_converter
                )
                if self.combat_system.perform_attack(
                    player_x, player_y, self.player.angle,
                    ability_target_x, ability_target_y, enemies_list
                ):
                    self.player.play_attack_animation(
                        is_melee=self.combat_system.is_melee_mode,
                        target_world_x=ability_target_x,
                        target_world_y=ability_target_y
                    )
    
    def _get_keyboard_input(self):
        """Получение ввода с клавиатуры для движения (адаптировано под изометрию)"""
        # Экранные направления
        screen_up = 0.0
        screen_down = 0.0
        screen_left = 0.0
        screen_right = 0.0
        
        if self.input_handler.is_key_pressed(pygame.K_w):
            screen_up = 1.0
        if self.input_handler.is_key_pressed(pygame.K_s):
            screen_down = 1.0
        if self.input_handler.is_key_pressed(pygame.K_a):
            screen_left = 1.0
        if self.input_handler.is_key_pressed(pygame.K_d):
            screen_right = 1.0
        
        # Преобразование экранных направлений в мировые координаты (изометрия)
        # Вверх на экране = (-1, -1) в мировых
        # Вниз на экране = (+1, +1) в мировых
        # Вправо на экране = (+1, -1) в мировых
        # Влево на экране = (-1, +1) в мировых
        world_x = 0.0
        world_y = 0.0
        
        world_x += -screen_up + screen_down + screen_right - screen_left
        world_y += -screen_up + screen_down - screen_right + screen_left
        
        if world_x != 0 or world_y != 0:
            return (world_x, world_y)
        return None
    
    def _update_procedural_enemy_spawn(self, location, player_x, player_y):
        """
        Обновляет спавн врагов в процедурном мире
        Спавнит врагов на основе точек спавна из генератора
        """
        # Проверяем, включен ли режим врагов
        if not self.enemies_enabled:
            return
        
        if not location:
            return
        
        level = self.level_manager.get_current_level()
        if not level or not level.procedural or not level.procedural_generator:
            return
        
        # Радиус проверки спавна (оптимизирован)
        spawn_check_radius = 30
        
        # Получаем точки спавна в радиусе
        spawn_points = level.procedural_generator.get_enemy_spawn_points_in_radius(
            player_x, player_y, spawn_check_radius
        )
        
        # Создаем множество уже заспавненных позиций (чтобы не дублировать)
        spawned_positions = set()
        for enemy in location.enemies:
            ex, ey = enemy.get_position()
            # Используем более грубую сетку для проверки (каждые 5 тайлов)
            grid_x = int(ex // 5) * 5
            grid_y = int(ey // 5) * 5
            spawned_positions.add((grid_x, grid_y))
        
        # Получаем все типы врагов кроме default
        from game.enemy import get_enemy_types
        enemy_types = get_enemy_types()
        available_enemy_types = [eid for eid in enemy_types.keys() if eid != 'default']
        
        if not available_enemy_types:
            return
        
        # Максимальное количество врагов (из настроек)
        max_enemies = self.max_enemies
        
        # Спавним врагов на точках спавна
        for x, y, biome in spawn_points:
            # Проверяем, не превышен ли лимит
            if len(location.enemies) >= max_enemies:
                break
            
            # Проверяем расстояние от игрока (не спавним слишком близко)
            # Уменьшено, чтобы враги были видны в радиусе тумана войны (12 тайлов)
            dx = x - player_x
            dy = y - player_y
            distance_sq = dx * dx + dy * dy
            
            # Минимальное расстояние 15 тайлов, максимальное 30 тайлов (чтобы были видны)
            if distance_sq < 15.0 * 15.0:  # Минимальное расстояние 15 тайлов от игрока
                continue
            if distance_sq > 30.0 * 30.0:  # Максимальное расстояние 30 тайлов (чтобы были видны)
                continue
            
            # Проверяем, нет ли врага слишком близко (минимальное расстояние между врагами) - УВЕЛИЧЕНО
            grid_x = int(x // 5) * 5
            grid_y = int(y // 5) * 5
            if (grid_x, grid_y) in spawned_positions:
                continue
            
            # Проверяем расстояние до других врагов - УВЕЛИЧЕНО
            too_close = False
            min_enemy_distance_sq = 8.0 * 8.0  # Минимальное расстояние 8 тайлов между врагами
            for enemy in location.enemies:
                ex, ey = enemy.get_position()
                edx = x - ex
                edy = y - ey
                enemy_distance_sq = edx * edx + edy * edy
                if enemy_distance_sq < min_enemy_distance_sq:
                    too_close = True
                    break
            
            if too_close:
                continue
            
            # Случайно выбираем тип врага
            enemy_type = random.choice(available_enemy_types)
            
            # Создаем врага
            from game.enemy import create_enemy
            enemy = create_enemy(x, y, enemy_type=enemy_type)
            location.enemies.append(enemy)
            spawned_positions.add((grid_x, grid_y))
    
    def _update_location(self, location, dt, player_x, player_y):
        """Обновление локации и обработка атак врагов"""
        for enemy in location.enemies[:]:
            attack_info = enemy.update(dt, player_x, player_y)
            
            # Враг атакует игрока
            if attack_info:
                is_melee = attack_info.get('is_melee', True)
                
                if is_melee:
                    # Ближний бой - мгновенный урон
                    damage = attack_info['damage']
                    self.player.take_damage(damage)
                else:
                    # Дальний бой - создаём снаряд врага
                    self._create_enemy_projectile(attack_info)
            
            # Удаляем мёртвых врагов
            if enemy.is_dead:
                location.enemies.remove(enemy)
        
        # Обновление снарядов врагов
        self._update_enemy_projectiles(dt, player_x, player_y)
        
        # Обновление порталов
        for portal in location.portals:
            portal.update(dt)
    
    def _create_enemy_projectile(self, attack_info):
        """Создаёт снаряд врага"""
        start_x = attack_info['start_x']
        start_y = attack_info['start_y']
        target_x = attack_info['target_x']
        target_y = attack_info['target_y']
        damage = attack_info['damage']
        
        dx = target_x - start_x
        dy = target_y - start_y
        angle = math.atan2(dy, dx)
        
        projectile = {
            'x': start_x,
            'y': start_y,
            'angle': angle,
            'speed': 10.0,  # Скорость снаряда
            'damage': damage,
            'range': 15.0,  # Максимальная дальность
            'distance': 0.0,
            'active': True,
            'age': 0.0
        }
        
        self.enemy_projectiles.append(projectile)
    
    def _update_enemy_projectiles(self, dt, player_x, player_y):
        """Обновляет снаряды врагов"""
        for proj in self.enemy_projectiles[:]:
            if not proj['active']:
                self.enemy_projectiles.remove(proj)
                continue
            
            proj['age'] += dt
            
            # Движение
            move_dist = proj['speed'] * dt
            proj['x'] += math.cos(proj['angle']) * move_dist
            proj['y'] += math.sin(proj['angle']) * move_dist
            proj['distance'] += move_dist
            
            # Проверка дальности
            if proj['distance'] >= proj['range']:
                proj['active'] = False
                continue
            
            # Проверка попадания в игрока
            dx = proj['x'] - player_x
            dy = proj['y'] - player_y
            dist_to_player = math.sqrt(dx * dx + dy * dy)
            
            if dist_to_player < 0.8:  # Радиус попадания
                self.player.take_damage(proj['damage'])
                proj['active'] = False
    
    def _check_attack_hits(self, location):
        """Проверка попаданий атак по врагам"""
        if not location or not location.enemies:
            return
        
        hits = self.combat_system.check_hits(location.enemies)
        for attack, enemy in hits:
            if not attack.is_melee:
                enemy.take_damage(attack.damage)
    
    def _draw_enemy_projectiles(self, camera_offset):
        """Отрисовка снарядов врагов"""
        for proj in self.enemy_projectiles:
            if not proj['active']:
                continue
            
            screen_x, screen_y = self.iso_converter.world_to_screen(proj['x'], proj['y'])
            screen_x += camera_offset[0]
            screen_y += camera_offset[1]
            
            # Тёмный магический снаряд (фиолетовый/тёмный)
            pulse = math.sin(proj['age'] * 15) * 2
            size = int(6 + pulse)
            
            # Внешнее свечение
            pygame.draw.circle(self.screen, (80, 0, 120), (int(screen_x), int(screen_y)), size + 3)
            # Среднее
            pygame.draw.circle(self.screen, (140, 0, 200), (int(screen_x), int(screen_y)), size + 1)
            # Ядро
            pygame.draw.circle(self.screen, (200, 100, 255), (int(screen_x), int(screen_y)), size - 1)
            # Центр
            pygame.draw.circle(self.screen, (255, 200, 255), (int(screen_x), int(screen_y)), max(1, size - 3))
    
    def _draw(self):
        """Отрисовка игры"""
        current_location = self.location_manager.get_current_location()
        camera_offset = self.camera.get_offset()
        
        # Фон
        if current_location:
            self.screen.fill(current_location.background_color)
        else:
            self.screen.fill(BLACK)
        
        # Сетка
        self._draw_grid(current_location, camera_offset)
        
        # Уровень (тайловая карта)
        self._draw_level(camera_offset)
        
        # Туман войны (затемнение неисследованных областей)
        level = self.level_manager.get_current_level()
        if level and level.tiles:
            self.fog_of_war.draw_fog(
                self.screen, 
                camera_offset, 
                self.iso_converter,
                level_tiles=level.tiles
            )
        
        # Локация (враги) - только видимые
        if current_location:
            self._draw_visible_enemies(current_location, camera_offset)
        
        # Персонаж
        self.player.draw(self.screen, self.iso_converter, camera_offset)
        
        # Атаки
        self.combat_system.draw(self.screen, self.iso_converter, camera_offset)
        
        # Снаряды врагов
        self._draw_enemy_projectiles(camera_offset)
        
        # UI
        self._draw_ui(current_location)
        
        # Game Over экран
        if self.game_over:
            self._draw_game_over()
    
    def _draw_grid(self, location, camera_offset):
        """Отрисовка сетки (оптимизированная версия)"""
        # Оптимизация: уменьшаем плотность сетки и используем более эффективную отрисовку
        grid_size = 15  # Уменьшено для производительности
        grid_color = DARK_GRAY if not location or location.name == "field" else (20, 20, 30)
        
        # Предвычисляем границы экрана для оптимизации
        screen_left = -100
        screen_right = SCREEN_WIDTH + 100
        screen_top = -100
        screen_bottom = SCREEN_HEIGHT + 100
        
        # Рисуем только видимые точки сетки
        for i in range(-grid_size, grid_size, 2):  # Пропускаем каждый второй для производительности
            for j in range(-grid_size, grid_size, 2):
                screen_x, screen_y = self.iso_converter.world_to_screen(i, j)
                screen_x += camera_offset[0]
                screen_y += camera_offset[1]
                
                # Оптимизированная проверка видимости
                if screen_left <= screen_x <= screen_right and screen_top <= screen_y <= screen_bottom:
                    # Используем простые точки вместо кругов для лучшей производительности
                    if 0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT:
                        self.screen.set_at((int(screen_x), int(screen_y)), grid_color)
    
    def _draw_visible_enemies(self, location, camera_offset):
        """Отрисовка только видимых врагов (в зоне видимости игрока)"""
        if not location or not location.enemies:
            return
        
        for enemy in location.enemies:
            if enemy.is_dead:
                continue
            
            ex, ey = enemy.get_position()
            
            # Проверяем, виден ли враг
            if self.fog_of_war.is_position_visible(ex, ey):
                enemy.draw(self.screen, self.iso_converter, camera_offset)
    
    def _draw_level(self, camera_offset):
        """Отрисовка тайловой карты уровня"""
        level = self.level_manager.get_current_level()
        if level:
            player_x, player_y = self.player.get_position()
            level.draw(self.screen, camera_offset, self.iso_converter, self.fog_of_war, 
                      player_pos=(player_x, player_y))
    
    def _draw_ui(self, location):
        """Отрисовка UI"""
        player_x, player_y = self.player.get_position()
        
        # Health и Mana бары
        self.player.draw_ui(self.screen, 10, SCREEN_HEIGHT - 60)
        
        # Миникарта
        self._draw_minimap(location, player_x, player_y)
        
        # Информация
        self._draw_info(location, player_x, player_y)
    
    def _draw_minimap(self, location, player_x, player_y):
        """Отрисовка миникарты с туманом войны"""
        minimap_x = SCREEN_WIDTH - self.minimap_size - 10
        minimap_y = 10
        
        # Создаём временную поверхность для миникарты
        minimap_temp = pygame.Surface((self.minimap_size, self.minimap_size), pygame.SRCALPHA)
        minimap_temp.fill((0, 0, 0, 220))
        
        # Центр миникарты
        minimap_center_x = self.minimap_size // 2
        minimap_center_y = self.minimap_size // 2
        
        # Масштаб: 1 тайл = несколько пикселей на миникарте
        tile_size = 5
        
        # Получаем исследованные и видимые тайлы
        explored_tiles = self.fog_of_war.get_explored_for_minimap()
        visible_tiles = self.fog_of_war.get_visible_for_minimap()
        
        # Отрисовка тайлов уровня (только исследованные)
        # Оптимизация: ограничиваем количество тайлов для миникарты
        level = self.level_manager.get_current_level()
        if level and level.tiles:
            # Предварительная фильтрация по расстоянию для производительности
            tiles_for_minimap = []
            for (tx, ty), tile_data in level.tiles.items():
                # Показываем только исследованные тайлы
                if (tx, ty) not in explored_tiles:
                    continue
                
                # Позиция тайла относительно игрока
                dx = tx - player_x
                dy = ty - player_y
                
                # Проверяем расстояние для миникарты (быстрая проверка без sqrt)
                distance_sq = dx * dx + dy * dy
                if distance_sq > self.minimap_radius * self.minimap_radius:
                    continue
                
                tiles_for_minimap.append(((tx, ty), tile_data, distance_sq))
            
            # Ограничиваем количество тайлов для миникарты (максимум 500)
            if len(tiles_for_minimap) > 500:
                tiles_for_minimap.sort(key=lambda item: item[2])  # Сортируем по расстоянию
                tiles_for_minimap = tiles_for_minimap[:500]  # Берем ближайшие
            
            # Отрисовываем отфильтрованные тайлы
            for (tx, ty), tile_data, _ in tiles_for_minimap:
                # Позиция тайла относительно игрока
                dx = tx - player_x
                dy = ty - player_y
                
                # Изометрическое преобразование для миникарты
                iso_x = (dx - dy) * tile_size // 2
                iso_y = (dx + dy) * tile_size // 4
                
                tile_minimap_x = minimap_center_x + iso_x
                tile_minimap_y = minimap_center_y + iso_y
                
                # Получаем цвет тайла
                tileset_name = tile_data.get('tileset', '')
                if 'grass' in tileset_name.lower():
                    base_color = (60, 120, 60)
                elif 'dirt' in tileset_name.lower():
                    base_color = (120, 80, 50)
                elif 'sand' in tileset_name.lower():
                    base_color = (180, 160, 100)
                elif 'stone' in tileset_name.lower():
                    base_color = (100, 100, 110)
                elif 'forest' in tileset_name.lower():
                    base_color = (40, 80, 40)
                else:
                    base_color = (80, 80, 80)
                
                # Яркость зависит от видимости
                if (tx, ty) in visible_tiles:
                    # Видимый сейчас - яркий
                    tile_color = (*base_color, 255)
                else:
                    # Исследованный но не видимый - тусклый
                    dim_color = tuple(int(c * 0.5) for c in base_color)
                    tile_color = (*dim_color, 180)
                
                # Рисуем ромб тайла
                if 0 <= tile_minimap_x < self.minimap_size and 0 <= tile_minimap_y < self.minimap_size:
                    points = [
                        (tile_minimap_x, tile_minimap_y - tile_size // 4),
                        (tile_minimap_x + tile_size // 2, tile_minimap_y),
                        (tile_minimap_x, tile_minimap_y + tile_size // 4),
                        (tile_minimap_x - tile_size // 2, tile_minimap_y)
                    ]
                    pygame.draw.polygon(minimap_temp, tile_color, points)
        
        # Игрок (яркая синяя точка в центре)
        pygame.draw.circle(minimap_temp, (100, 180, 255), (minimap_center_x, minimap_center_y), 4)
        pygame.draw.circle(minimap_temp, WHITE, (minimap_center_x, minimap_center_y), 4, 1)
        
        # Враги (только видимые!)
        if location and location.enemies:
            for enemy in location.enemies:
                if enemy.is_dead:
                    continue
                
                ex, ey = enemy.get_position()
                
                # Показываем врага только если он в зоне видимости
                if not self.fog_of_war.is_position_visible(ex, ey):
                    continue
                
                dx = ex - player_x
                dy = ey - player_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance <= self.minimap_radius:
                    iso_x = (dx - dy) * tile_size // 2
                    iso_y = (dx + dy) * tile_size // 4
                    
                    enemy_minimap_x = minimap_center_x + iso_x
                    enemy_minimap_y = minimap_center_y + iso_y
                    
                    if 0 <= enemy_minimap_x < self.minimap_size and 0 <= enemy_minimap_y < self.minimap_size:
                        pygame.draw.circle(minimap_temp, RED, (int(enemy_minimap_x), int(enemy_minimap_y)), 3)
        
        # Рамка миникарты
        pygame.draw.rect(minimap_temp, WHITE, (0, 0, self.minimap_size, self.minimap_size), 2)
        
        # Отрисовываем миникарту на экран
        self.screen.blit(minimap_temp, (minimap_x, minimap_y))
    
    def _draw_info(self, location, player_x, player_y):
        """Отрисовка информации"""
        # FPS и позиция
        fps_text = self.font_medium.render(f"FPS: {int(self.clock.get_fps())}", True, WHITE)
        pos_text = self.font_medium.render(f"Позиция: ({player_x:.1f}, {player_y:.1f})", True, WHITE)
        location_text = self.font_medium.render(
            f"Локация: {location.name if location else 'None'}", True, WHITE
        )
        mode_text = self.font_medium.render(
            f"Режим боя: {'Ближний' if self.combat_system.is_melee_mode else 'Дальний'}", True, WHITE
        )
        
        self.screen.blit(fps_text, (10, 10))
        self.screen.blit(pos_text, (10, 35))
        self.screen.blit(location_text, (10, 60))
        self.screen.blit(mode_text, (10, 85))
        
        # Настройки врагов (если включены)
        if self.enemies_enabled:
            current_location = self.location_manager.get_current_location()
            current_enemies = len(current_location.enemies) if current_location else 0
            enemy_settings_text = self.font_medium.render(
                f"Враги: {current_enemies}/{self.max_enemies} (частота: {self.enemy_spawn_frequency:.1f}с)", 
                True, (150, 255, 150)
            )
            self.screen.blit(enemy_settings_text, (10, 110))
        
        # Управление
        controls = [
            "Управление:",
            "WASD - движение",
            "ЛКМ - атака",
            "Клавиша 2 - переключение ближний/дальний бой",
            "Клавиши 1, 3-9 - способности",
            "ESC - меню"
        ]
        y_offset = 135 if self.enemies_enabled else 110
        for text in controls:
            rendered = self.font_medium.render(text, True, GRAY)
            self.screen.blit(rendered, (10, y_offset))
            y_offset += 25
        
        # Управление настройками врагов (если включены)
        if self.enemies_enabled:
            enemy_controls = [
                "Настройки врагов:",
                "+/- - частота спавна",
                "[/] - макс. количество"
            ]
            for text in enemy_controls:
                rendered = self.font_medium.render(text, True, (150, 255, 150))
                self.screen.blit(rendered, (10, y_offset))
                y_offset += 25
    
    def _draw_game_over(self):
        """Отрисовка экрана Game Over"""
        # Затемнение
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Текст
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        restart_text = self.font_medium.render("Нажмите R для перезапуска", True, WHITE)
        
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(restart_text, restart_rect)
    
    def _draw_pause_menu(self):
        """Отрисовка меню паузы"""
        # Затемнение
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        if self.in_level_submenu:
            self._draw_level_submenu()
        elif self.in_enemy_submenu:
            self._draw_enemy_submenu()
        else:
            self._draw_main_menu()
    
    def _draw_main_menu(self):
        """Отрисовка главного меню паузы"""
        # Заголовок
        title = self.font_large.render("ПАУЗА", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Пункты меню
        menu_y = 220
        for i, item in enumerate(self.menu_items):
            if i == self.selected_menu_item:
                color = (255, 255, 100)
                prefix = "> "
                suffix = " <"
            else:
                color = GRAY
                prefix = "  "
                suffix = "  "
            
            # Получаем текст пункта меню (может быть функцией)
            menu_text = item['text']
            if callable(menu_text):
                menu_text = menu_text()
            
            # Для настроек добавляем стрелки только если выбраны
            if item.get("type") == "setting" and i == self.selected_menu_item:
                menu_text = f"◄ {menu_text} ►"
            
            text = self.font_medium.render(f"{prefix}{menu_text}{suffix}", True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, menu_y))
            self.screen.blit(text, text_rect)
            menu_y += 40
        
        # Подсказка (динамическая, в зависимости от выбранного пункта)
        selected_item = self.menu_items[self.selected_menu_item] if self.menu_items else None
        if selected_item and selected_item.get("type") == "setting":
            hint_text = "←/→ или A/D - изменение настройки, ESC - закрыть"
        else:
            hint_text = "W/S или ↑/↓ - выбор, Enter - подтверждение, ESC - закрыть"
        hint = self.font_small.render(hint_text, True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)
    
    def _draw_level_submenu(self):
        """Отрисовка подменю уровней"""
        # Заголовок
        title = self.font_large.render("УРОВНИ", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Подсказка
        subtitle = self.font_small.render("Выберите уровень для загрузки", True, GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 135))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Пункты подменю
        menu_y = 180
        for i, item in enumerate(self.level_submenu_items):
            if i == self.selected_level:
                color = (255, 255, 100)
                prefix = "> "
                suffix = " <"
            else:
                color = GRAY
                prefix = "  "
                suffix = "  "
            
            text = self.font_medium.render(f"{prefix}{item['text']}{suffix}", True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, menu_y))
            self.screen.blit(text, text_rect)
            menu_y += 30
        
        # Подсказка навигации
        nav_hint = self.font_small.render("← Назад | ↑↓ Выбор | Enter Загрузить", True, GRAY)
        nav_rect = nav_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(nav_hint, nav_rect)
    
    def _draw_enemy_submenu(self):
        """Отрисовка подменю противников"""
        # Заголовок
        title = self.font_large.render("ПРОТИВНИКИ", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Подсказка
        subtitle = self.font_small.render("Выберите тип врага для спавна", True, GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 135))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Пункты подменю (с прокруткой если много)
        visible_items = 12
        start_idx = max(0, self.selected_enemy_type - visible_items // 2)
        end_idx = min(len(self.enemy_submenu_items), start_idx + visible_items)
        
        if end_idx - start_idx < visible_items:
            start_idx = max(0, end_idx - visible_items)
        
        menu_y = 180
        for i in range(start_idx, end_idx):
            item = self.enemy_submenu_items[i]
            
            if i == self.selected_enemy_type:
                color = (255, 255, 100)
                prefix = "> "
                suffix = " <"
            else:
                color = GRAY
                prefix = "  "
                suffix = "  "
            
            # Цветной индикатор для типов врагов
            if item.get("type"):
                enemy_types = get_enemy_types()
                enemy_data = enemy_types.get(item["type"], {})
                enemy_color = enemy_data.get('color', (200, 50, 50))
                if isinstance(enemy_color, list):
                    enemy_color = tuple(enemy_color)
                
                # Квадрат с цветом врага
                indicator_x = SCREEN_WIDTH // 2 - 180
                indicator_rect = pygame.Rect(indicator_x, menu_y - 8, 16, 16)
                pygame.draw.rect(self.screen, enemy_color, indicator_rect)
                pygame.draw.rect(self.screen, WHITE, indicator_rect, 1)
            
            text = self.font_medium.render(f"{prefix}{item['text']}{suffix}", True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, menu_y))
            self.screen.blit(text, text_rect)
            menu_y += 35
        
        # Индикатор прокрутки
        if start_idx > 0:
            arrow_up = self.font_medium.render("▲", True, GRAY)
            self.screen.blit(arrow_up, (SCREEN_WIDTH // 2 - 8, 160))
        
        if end_idx < len(self.enemy_submenu_items):
            arrow_down = self.font_medium.render("▼", True, GRAY)
            self.screen.blit(arrow_down, (SCREEN_WIDTH // 2 - 8, menu_y + 5))
        
        # Подсказка
        hint = self.font_small.render("W/S - выбор, Enter - спавн, ← или ESC - назад", True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)
    


if __name__ == "__main__":
    game = Game()
    game.run()
