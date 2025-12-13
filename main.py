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

# Константы
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
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
        
        # Экран
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PyDiab - Изометрическая игра")
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
        
        # Создание локаций
        self.location_manager = LocationManager()
        self._setup_locations()
        
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
        
        # Меню паузы
        self.menu_items = [
            {"text": "Продолжить", "action": self._resume_game},
            {"text": "Противники ▶", "action": self._open_enemy_submenu},
            {"text": "Убить всех врагов", "action": self._kill_all_enemies},
            {"text": "Перезапуск", "action": self._restart_game},
            {"text": "Выход", "action": self._quit_game},
        ]
        self.selected_menu_item = 0
        
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
            
            # Обновление экрана
            pygame.display.flip()
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
                elif self.paused:
                    self._handle_menu_input(event)
                elif event.key == pygame.K_r and self.game_over:
                    self._restart_game()
        
        if not self.paused:
            self.input_handler.update(events)
    
    def _handle_menu_input(self, event):
        """Обработка ввода в меню"""
        if self.in_enemy_submenu:
            self._handle_enemy_submenu_input(event)
        else:
            self._handle_main_menu_input(event)
    
    def _handle_main_menu_input(self, event):
        """Обработка ввода в главном меню"""
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.selected_menu_item = (self.selected_menu_item - 1) % len(self.menu_items)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.selected_menu_item = (self.selected_menu_item + 1) % len(self.menu_items)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.menu_items[self.selected_menu_item]["action"]()
    
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
        self._setup_locations()
        self.game_over = False
        self.paused = False
    
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
    
    def _update_location(self, location, dt, player_x, player_y):
        """Обновление локации и обработка атак врагов"""
        for enemy in location.enemies[:]:
            attack_info = enemy.update(dt, player_x, player_y)
            
            # Враг атакует игрока
            if attack_info:
                damage = attack_info['damage']
                self.player.take_damage(damage)
            
            # Удаляем мёртвых врагов
            if enemy.is_dead:
                location.enemies.remove(enemy)
        
        # Обновление порталов
        for portal in location.portals:
            portal.update(dt)
    
    def _check_attack_hits(self, location):
        """Проверка попаданий атак по врагам"""
        if not location or not location.enemies:
            return
        
        hits = self.combat_system.check_hits(location.enemies)
        for attack, enemy in hits:
            if not attack.is_melee:
                enemy.take_damage(attack.damage)
    
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
        
        # Локация (враги)
        if current_location:
            current_location.draw(self.screen, self.iso_converter, camera_offset)
        
        # Персонаж
        self.player.draw(self.screen, self.iso_converter, camera_offset)
        
        # Атаки
        self.combat_system.draw(self.screen, self.iso_converter, camera_offset)
        
        # UI
        self._draw_ui(current_location)
        
        # Game Over экран
        if self.game_over:
            self._draw_game_over()
    
    def _draw_grid(self, location, camera_offset):
        """Отрисовка сетки"""
        grid_size = 20
        grid_color = DARK_GRAY if not location or location.name == "field" else (20, 20, 30)
        
        for i in range(-grid_size, grid_size):
            for j in range(-grid_size, grid_size):
                screen_x, screen_y = self.iso_converter.world_to_screen(i, j)
                screen_x += camera_offset[0]
                screen_y += camera_offset[1]
                
                if 0 <= screen_x <= SCREEN_WIDTH and 0 <= screen_y <= SCREEN_HEIGHT:
                    pygame.draw.circle(self.screen, grid_color, (screen_x, screen_y), 2)
    
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
        """Отрисовка миникарты"""
        minimap_x = SCREEN_WIDTH - self.minimap_size - 10
        minimap_y = 10
        
        # Фон миникарты (используем кэшированную поверхность)
        self.screen.blit(self.minimap_surface, (minimap_x, minimap_y))
        
        # Центр миникарты
        minimap_center_x = minimap_x + self.minimap_size // 2
        minimap_center_y = minimap_y + self.minimap_size // 2
        
        # Игрок (синяя точка)
        pygame.draw.circle(self.screen, (100, 150, 255), (minimap_center_x, minimap_center_y), 4)
        
        # Враги (красные точки)
        if location and location.enemies:
            scale = self.minimap_size / (2 * self.minimap_radius)
            for enemy in location.enemies:
                if enemy.is_dead:
                    continue
                
                ex, ey = enemy.get_position()
                dx = ex - player_x
                dy = ey - player_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance <= self.minimap_radius:
                    enemy_minimap_x = minimap_center_x + dx * scale
                    enemy_minimap_y = minimap_center_y + dy * scale
                    
                    if (minimap_x <= enemy_minimap_x <= minimap_x + self.minimap_size and
                        minimap_y <= enemy_minimap_y <= minimap_y + self.minimap_size):
                        pygame.draw.circle(self.screen, RED, 
                                         (int(enemy_minimap_x), int(enemy_minimap_y)), 3)
    
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
        
        # Управление
        controls = [
            "Управление:",
            "WASD - движение",
            "ЛКМ - атака",
            "Клавиша 2 - переключение ближний/дальний бой",
            "Клавиши 1, 3-9 - способности",
            "ESC - меню"
        ]
        y_offset = 110
        for text in controls:
            rendered = self.font_medium.render(text, True, GRAY)
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
        
        if self.in_enemy_submenu:
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
            
            text = self.font_medium.render(f"{prefix}{item['text']}{suffix}", True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, menu_y))
            self.screen.blit(text, text_rect)
            menu_y += 40
        
        # Подсказка
        hint = self.font_small.render("W/S или ↑/↓ - выбор, Enter - подтверждение, ESC - закрыть", True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)
    
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
