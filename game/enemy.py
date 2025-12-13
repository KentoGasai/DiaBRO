"""
Класс врагов
"""
import pygame
import math
import random
import json
import os
from game.stats import Stats, HealthBar
from game.sprites import AnimatedSprite


def _get_base_path():
    """Возвращает базовый путь (поддержка PyInstaller)"""
    import sys
    if getattr(sys, 'frozen', False):
        # Запуск из exe — данные в _MEIPASS
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(__file__))


def load_enemy_types_from_config():
    """
    Загружает типы врагов из JSON конфига (создаётся редактором).
    
    Returns:
        dict: Словарь типов врагов
    """
    config_path = os.path.join(_get_base_path(), 'game', 'enemy_types.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки enemy_types.json: {e}")
    
    return {}


class Enemy:
    """Класс врага"""
    
    def __init__(self, x, y, max_health=30, damage=5, 
                 sprite_path=None, weapon_path=None, sprite_scale=1.0,
                 attack_type='melee', projectile_path=None):
        """
        Args:
            x, y: Начальная позиция в мировых координатах
            max_health: Максимальное здоровье
            damage: Урон врага
            sprite_path: Путь к спрайтшиту (опционально)
            weapon_path: Путь к спрайтшиту оружия (опционально)
            sprite_scale: Масштаб спрайтов (1.0 = размер игрока)
            attack_type: Тип атаки ('melee' или 'ranged')
            projectile_path: Путь к спрайту снаряда (для ranged)
        """
        self.world_x = x
        self.world_y = y
        self.max_health = max_health
        self.damage = damage
        self.stats = Stats(max_health=max_health, max_mana=0)
        self.health_bar = HealthBar(width=60, height=8)
        
        # Визуальное представление (fallback)
        self.size = 18
        self.color = (200, 50, 50)  # Красноватый цвет
        self.angle = 0
        self.sprite_angle = 0  # Угол для спрайта (экранные координаты)
        
        # Спрайтовая анимация
        self.animated_sprite = None
        self.use_sprites = False
        if sprite_path:
            self.set_sprite(sprite_path, weapon_path, sprite_scale)
        
        # Тип атаки
        self.attack_type = attack_type  # 'melee' или 'ranged'
        self.projectile_path = projectile_path  # Спрайт снаряда
        self.is_melee = attack_type == 'melee'
        
        # AI параметры
        self.speed = 6.0  # Скорость движения (немного медленнее игрока 8.0)
        self.aggro_range = 150  # Дистанция агрессии (мировые координаты)
        self.attack_range = 1.2 if self.is_melee else 8.0  # Ближний: 1.2, Дальний: 8.0
        self.attack_cooldown = 0.0
        self.attack_cooldown_time = 1.5
        
        # Состояние
        self.is_dead = False
        self.target = None
        self.is_highlighted = False  # Подсветка при наведении
        self.is_moving = False  # Флаг движения
        
        # Анимация смерти
        self.death_animation_time = 0.0
        self.death_animation_duration = 0.5  # 0.5 секунды на анимацию
        self.dying = False  # Флаг анимации смерти
        
        # Анимация атаки
        self.attack_animation_time = 0.0
        self.attack_animation_duration = 0.3  # 0.3 секунды на анимацию атаки
        self.is_attacking = False
    
    def set_sprite(self, sprite_path, weapon_path=None, scale=0.25, animation_speeds=None):
        """
        Устанавливает спрайт для врага
        
        Args:
            sprite_path: Путь к спрайтшиту
            weapon_path: Путь к спрайтшиту оружия (опционально)
            scale: Масштаб спрайтов
            animation_speeds: Словарь скоростей анимаций (опционально)
        """
        self.animated_sprite = AnimatedSprite(
            sprite_path=sprite_path,
            weapon_path=weapon_path,
            scale=scale,
            animation_speeds=animation_speeds
        )
        self.use_sprites = self.animated_sprite.is_loaded()
        
        # Обновляем размер для коллизий если спрайты загружены
        if self.use_sprites:
            self.size = self.animated_sprite.get_frame_size() // 4
    
    def update(self, dt, player_x, player_y):
        """
        Обновляет состояние врага
        
        Args:
            dt: Delta time
            player_x, player_y: Позиция игрока
            
        Returns:
            dict или None: Информация об атаке, если враг атакует
        """
        self.is_moving = False
        
        # Обновление анимации атаки (fallback)
        if self.is_attacking and not self.use_sprites:
            self.attack_animation_time += dt
            if self.attack_animation_time >= self.attack_animation_duration:
                self.is_attacking = False
        
        # Обновление анимации смерти
        if self.dying:
            self.death_animation_time += dt
            
            # Для спрайтов обновляем анимацию
            if self.use_sprites and self.animated_sprite:
                self.animated_sprite.update(dt, is_walking=False)
            
            if self.death_animation_time >= self.death_animation_duration:
                self.is_dead = True
            return None
        
        if self.is_dead:
            return None
        
        # Обновление кулдауна атаки
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        # Проверка расстояния до игрока
        dx = player_x - self.world_x
        dy = player_y - self.world_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        attack_info = None
        
        # Если игрок в зоне агрессии
        if distance <= self.aggro_range:
            self.target = (player_x, player_y)
            
            # Проверяем, можем ли атаковать
            if distance <= self.attack_range and self.attack_cooldown <= 0:
                # Атакуем игрока
                attack_info = {
                    'damage': self.damage,
                    'attacker': self
                }
                self.attack_cooldown = self.attack_cooldown_time
                
                # Запускаем анимацию атаки
                self.is_attacking = True
                self.attack_animation_time = 0.0
                
                if self.use_sprites and self.animated_sprite:
                    self.animated_sprite.play_attack(
                        is_melee=True,
                        on_complete=self._on_attack_complete
                    )
            elif distance > self.attack_range:
                # Движение к игроку
                move_x = (dx / distance) * self.speed * dt
                move_y = (dy / distance) * self.speed * dt
                self.world_x += move_x
                self.world_y += move_y
                self.is_moving = True
            
            # Мировой угол
            self.angle = math.atan2(dy, dx)
            
            # Вычисляем экранный угол для спрайта (как у игрока)
            screen_dir_x = dx - dy
            screen_dir_y = -(dx + dy)
            if screen_dir_x != 0 or screen_dir_y != 0:
                self.sprite_angle = math.atan2(screen_dir_y, screen_dir_x)
        else:
            self.target = None
        
        # Обновление спрайтовой анимации
        if self.use_sprites and self.animated_sprite:
            self.animated_sprite.set_direction(self.sprite_angle)
            self.animated_sprite.update(dt, is_walking=self.is_moving)
        
        return attack_info
    
    def _on_attack_complete(self):
        """Callback по завершению анимации атаки"""
        self.is_attacking = False
    
    def take_damage(self, damage):
        """Наносит урон врагу"""
        if self.is_dead or self.dying:
            return False
        
        is_dead = self.stats.take_damage(damage)
        if is_dead:
            self.dying = True
            self.death_animation_time = 0.0
            
            # Запускаем анимацию смерти
            if self.use_sprites and self.animated_sprite:
                self.animated_sprite.play_death()
        else:
            # Анимация получения урона
            if self.use_sprites and self.animated_sprite:
                self.animated_sprite.play_hurt()
        
        return is_dead
    
    def can_attack(self):
        """Проверяет, может ли враг атаковать"""
        return self.attack_cooldown <= 0 and self.target is not None and not self.dying
    
    def attack(self):
        """Выполняет атаку"""
        if self.can_attack():
            self.attack_cooldown = self.attack_cooldown_time
            return True
        return False
    
    def get_position(self):
        """Возвращает позицию"""
        return self.world_x, self.world_y
    
    def check_mouse_hover(self, mouse_world_x, mouse_world_y, hover_radius=1.0):
        """
        Проверяет, наведена ли мышь на врага
        
        Args:
            mouse_world_x, mouse_world_y: Позиция мыши в мировых координатах
            hover_radius: Радиус наведения
            
        Returns:
            True если мышь наведена на врага
        """
        if self.is_dead or self.dying:
            return False
        
        dx = mouse_world_x - self.world_x
        dy = mouse_world_y - self.world_y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance <= hover_radius
    
    def set_highlighted(self, highlighted):
        """Устанавливает состояние подсветки"""
        self.is_highlighted = highlighted
    
    def draw(self, screen, iso_converter, camera_offset):
        """Отрисовывает врага"""
        if self.is_dead:
            return
        
        # Преобразование в экранные координаты
        screen_x, screen_y = iso_converter.world_to_screen(
            self.world_x, self.world_y
        )
        screen_x += camera_offset[0]
        screen_y += camera_offset[1]
        
        # Анимация смерти (fade out)
        alpha = 255
        if self.dying:
            progress = self.death_animation_time / self.death_animation_duration
            alpha = int(255 * (1 - progress))
        
        # Отрисовка спрайтов или fallback
        if self.use_sprites and self.animated_sprite:
            self._draw_sprite(screen, screen_x, screen_y, alpha)
        else:
            self._draw_fallback(screen, screen_x, screen_y, alpha)
        
        # Отрисовка Health Bar над врагом (не показываем при смерти)
        if not self.dying:
            bar_y_offset = self.size + 15
            if self.use_sprites and self.animated_sprite:
                bar_y_offset = self.animated_sprite.get_frame_size() // 2 + 10
            bar_x = screen_x - self.health_bar.width // 2
            bar_y = screen_y - bar_y_offset
            self.health_bar.draw(screen, bar_x, bar_y, self.stats, is_enemy=True)
    
    def _draw_sprite(self, screen, screen_x, screen_y, alpha):
        """Отрисовывает спрайт врага"""
        # Оттенок при подсветке
        tint_color = (100, 100, 0) if self.is_highlighted and not self.dying else None
        
        # Отрисовка свечения при подсветке
        if self.is_highlighted and not self.dying:
            frame_size = self.animated_sprite.get_frame_size()
            glow_radius = frame_size // 2 + 8
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 255, 0, 60), 
                             (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surface, 
                       (screen_x - glow_radius, screen_y - glow_radius - frame_size // 4))
        
        # Отрисовка спрайта
        self.animated_sprite.draw(screen, screen_x, screen_y, alpha=alpha, tint_color=tint_color)
    
    def _draw_fallback(self, screen, screen_x, screen_y, alpha):
        """Отрисовывает fallback (если нет спрайтов)"""
        size_modifier = 1.0
        if self.dying:
            progress = self.death_animation_time / self.death_animation_duration
            size_modifier = 1 - progress * 0.5
        
        current_size = int(self.size * size_modifier)
        
        # Подсветка при наведении
        if self.is_highlighted and not self.dying:
            # Внешнее свечение
            glow_radius = current_size + 8
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 255, 0, 100), 
                             (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surface, 
                       (screen_x - glow_radius, screen_y - glow_radius))
            highlight_color = (255, 255, 100)
        else:
            highlight_color = self.color
        
        # Создаём поверхность с альфа-каналом для fade out
        if self.dying:
            enemy_surface = pygame.Surface((current_size, current_size), pygame.SRCALPHA)
            color_with_alpha = (*highlight_color, alpha)
            pygame.draw.rect(enemy_surface, color_with_alpha, (0, 0, current_size, current_size))
            screen.blit(enemy_surface, (screen_x - current_size // 2, screen_y - current_size // 2))
        else:
            rect = pygame.Rect(
                screen_x - current_size // 2,
                screen_y - current_size // 2,
                current_size,
                current_size
            )
            pygame.draw.rect(screen, highlight_color, rect)
            
            if self.is_highlighted:
                pygame.draw.rect(screen, (255, 255, 0), rect, 3)
        
        # Анимация атаки - красная вспышка (только для fallback)
        if self.is_attacking and not self.dying:
            progress = self.attack_animation_time / self.attack_animation_duration
            attack_length = 25 * (1 - progress)
            end_x = screen_x + math.cos(self.angle) * attack_length
            end_y = screen_y + math.sin(self.angle) * attack_length
            line_width = max(1, int(5 * (1 - progress)))
            red_intensity = int(255 * (1 - progress * 0.5))
            attack_color = (red_intensity, 50, 50)
            pygame.draw.line(screen, attack_color, 
                           (int(screen_x), int(screen_y)), 
                           (int(end_x), int(end_y)), line_width)
            flash_size = max(2, int(8 * (1 - progress)))
            pygame.draw.circle(screen, (255, 100, 100), (int(end_x), int(end_y)), flash_size)


# Размер спрайта игрока (для сравнения)
PLAYER_SPRITE_SCALE = 1.0  # 256x256 px
PLAYER_SPEED = 8.0  # Скорость игрока для сравнения

# Базовые типы врагов (встроенные)
# sprite_scale: 1.0 = размер игрока (256px)
# speed: относительно игрока (8.0), немного медленнее = 6.0-7.0
# attack_type: 'melee' (ближний) или 'ranged' (дальний)
BUILTIN_ENEMY_TYPES = {
    'default': {
        'sprite_path': None,
        'weapon_path': None,
        'projectile_path': None,  # Спрайт снаряда для дальнего боя
        'sprite_scale': 1.0,
        'max_health': 30,
        'damage': 5,
        'speed': 6.0,  # Немного медленнее игрока (8.0)
        'attack_type': 'melee',  # Тип атаки: melee/ranged
        'color': (200, 50, 50),
    },
}
# Остальные типы врагов добавляются через веб-редактор (enemy_types.json)

# Кэш загруженных типов врагов
_cached_enemy_types = None


def get_enemy_types():
    """
    Возвращает все доступные типы врагов (встроенные + из конфига).
    
    Returns:
        dict: Объединённый словарь типов врагов
    """
    global _cached_enemy_types
    
    if _cached_enemy_types is None:
        # Начинаем со встроенных типов
        _cached_enemy_types = {**BUILTIN_ENEMY_TYPES}
        
        # Добавляем/переопределяем типами из конфига
        config_types = load_enemy_types_from_config()
        for enemy_id, enemy_data in config_types.items():
            # Преобразуем color из списка в кортеж
            if 'color' in enemy_data and isinstance(enemy_data['color'], list):
                enemy_data['color'] = tuple(enemy_data['color'])
            _cached_enemy_types[enemy_id] = enemy_data
    
    return _cached_enemy_types


def reload_enemy_types():
    """Перезагружает типы врагов из конфига"""
    global _cached_enemy_types
    _cached_enemy_types = None
    return get_enemy_types()


def create_enemy(x, y, enemy_type='default', **kwargs):
    """
    Фабрика для создания врагов с разными типами.
    
    Args:
        x, y: Позиция врага
        enemy_type: Тип врага (строка или dict с параметрами)
        **kwargs: Дополнительные параметры (max_health, damage, speed и т.д.)
    
    Returns:
        Enemy: Экземпляр врага
    
    Примеры использования:
        # Враг без спрайтов (fallback квадрат)
        enemy = create_enemy(5, 5)
        
        # Враг со спрайтом (из редактора)
        enemy = create_enemy(5, 5, enemy_type='skeleton')
        
        # Дальнобойный враг
        enemy = create_enemy(5, 5, attack_type='ranged')
    """
    ENEMY_TYPES = get_enemy_types()
    
    # Получаем базовые параметры типа
    if isinstance(enemy_type, dict):
        params = {**ENEMY_TYPES['default'], **enemy_type}
    else:
        params = {**ENEMY_TYPES.get(enemy_type, ENEMY_TYPES['default'])}
    
    # Переопределяем из kwargs
    params.update(kwargs)
    
    # Определяем тип атаки
    attack_type = params.get('attack_type', 'melee')
    
    # Создаём врага
    enemy = Enemy(
        x=x,
        y=y,
        max_health=params.get('max_health', 30),
        damage=params.get('damage', 5),
        sprite_path=params.get('sprite_path'),
        weapon_path=params.get('weapon_path'),
        sprite_scale=params.get('sprite_scale', 1.0),
        attack_type=attack_type,
        projectile_path=params.get('projectile_path')
    )
    
    # Дополнительные параметры
    if 'speed' in params:
        enemy.speed = params['speed']
    if 'color' in params:
        color = params['color']
        if isinstance(color, list):
            color = tuple(color)
        enemy.color = color
    if 'aggro_range' in params:
        enemy.aggro_range = params['aggro_range']
    if 'attack_range' in params:
        enemy.attack_range = params['attack_range']
    if 'attack_cooldown_time' in params:
        enemy.attack_cooldown_time = params['attack_cooldown_time']
    if 'attack_cooldown' in params:
        enemy.attack_cooldown_time = params['attack_cooldown']
    
    return enemy
