"""
Класс врагов
"""
import pygame
import math
import random
from game.stats import Stats, HealthBar


class Enemy:
    """Класс врага"""
    
    def __init__(self, x, y, max_health=30, damage=5):
        """
        Args:
            x, y: Начальная позиция в мировых координатах
            max_health: Максимальное здоровье
            damage: Урон врага
        """
        self.world_x = x
        self.world_y = y
        self.max_health = max_health
        self.damage = damage
        self.stats = Stats(max_health=max_health, max_mana=0)
        self.health_bar = HealthBar(width=60, height=8)
        
        # Визуальное представление
        self.size = 18
        self.color = (200, 50, 50)  # Красноватый цвет
        self.angle = 0
        
        # AI параметры
        self.speed = 50.0  # Скорость движения
        self.aggro_range = 150  # Дистанция агрессии (мировые координаты)
        self.attack_range = 1.2  # Дистанция атаки (мировые координаты, ~42 экранных пикселя)
        self.attack_cooldown = 0.0
        self.attack_cooldown_time = 1.5
        
        # Состояние
        self.is_dead = False
        self.target = None
        self.is_highlighted = False  # Подсветка при наведении
        
        # Анимация смерти
        self.death_animation_time = 0.0
        self.death_animation_duration = 0.5  # 0.5 секунды на анимацию
        self.dying = False  # Флаг анимации смерти
        
        # Анимация атаки
        self.attack_animation_time = 0.0
        self.attack_animation_duration = 0.3  # 0.3 секунды на анимацию атаки
        self.is_attacking = False
    
    def update(self, dt, player_x, player_y):
        """
        Обновляет состояние врага
        
        Args:
            dt: Delta time
            player_x, player_y: Позиция игрока
            
        Returns:
            dict или None: Информация об атаке, если враг атакует
        """
        # Обновление анимации атаки
        if self.is_attacking:
            self.attack_animation_time += dt
            if self.attack_animation_time >= self.attack_animation_duration:
                self.is_attacking = False
        
        # Обновление анимации смерти
        if self.dying:
            self.death_animation_time += dt
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
            elif distance > self.attack_range:
                # Движение к игроку
                move_x = (dx / distance) * self.speed * dt
                move_y = (dy / distance) * self.speed * dt
                self.world_x += move_x
                self.world_y += move_y
            
            self.angle = math.atan2(dy, dx)
        else:
            self.target = None
        
        return attack_info
    
    def take_damage(self, damage):
        """Наносит урон врагу"""
        if self.is_dead or self.dying:
            return False
        
        is_dead = self.stats.take_damage(damage)
        if is_dead:
            self.dying = True
            self.death_animation_time = 0.0
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
        
        # Анимация смерти (fade out + уменьшение)
        alpha = 255
        size_modifier = 1.0
        if self.dying:
            progress = self.death_animation_time / self.death_animation_duration
            alpha = int(255 * (1 - progress))
            size_modifier = 1 - progress * 0.5  # Уменьшается до 50%
        
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
            # Цвет с альфа-каналом
            color_with_alpha = (*highlight_color, alpha)
            pygame.draw.rect(enemy_surface, color_with_alpha, (0, 0, current_size, current_size))
            screen.blit(enemy_surface, (screen_x - current_size // 2, screen_y - current_size // 2))
        else:
            # Отрисовка врага (красный квадрат)
            rect = pygame.Rect(
                screen_x - current_size // 2,
                screen_y - current_size // 2,
                current_size,
                current_size
            )
            pygame.draw.rect(screen, highlight_color, rect)
            
            # Рамка при подсветке
            if self.is_highlighted:
                pygame.draw.rect(screen, (255, 255, 0), rect, 3)
        
        # Отрисовка Health Bar над врагом (не показываем при смерти)
        if not self.dying:
            bar_x = screen_x - self.health_bar.width // 2
            bar_y = screen_y - self.size - 15
            self.health_bar.draw(screen, bar_x, bar_y, self.stats, is_enemy=True)
        
        # Анимация атаки - красная вспышка в сторону игрока
        if self.is_attacking and not self.dying:
            progress = self.attack_animation_time / self.attack_animation_duration
            
            # Длина удара (уменьшается к концу анимации)
            attack_length = 25 * (1 - progress)
            
            # Позиция конца удара
            end_x = screen_x + math.cos(self.angle) * attack_length
            end_y = screen_y + math.sin(self.angle) * attack_length
            
            # Толщина линии (уменьшается)
            line_width = max(1, int(5 * (1 - progress)))
            
            # Цвет (от яркого к тёмному)
            red_intensity = int(255 * (1 - progress * 0.5))
            attack_color = (red_intensity, 50, 50)
            
            # Линия удара
            pygame.draw.line(screen, attack_color, 
                           (int(screen_x), int(screen_y)), 
                           (int(end_x), int(end_y)), line_width)
            
            # Вспышка на конце
            flash_size = max(2, int(8 * (1 - progress)))
            pygame.draw.circle(screen, (255, 100, 100), (int(end_x), int(end_y)), flash_size)
