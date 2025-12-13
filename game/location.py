"""
Система локаций
"""
import pygame
import math
import random
from game.enemy import Enemy


class Portal:
    """Точка перехода между локациями"""
    
    def __init__(self, x, y, target_location, label=""):
        """
        Args:
            x, y: Позиция портала в мировых координатах
            target_location: Имя целевой локации
            label: Текстовая метка для портала
        """
        self.world_x = x
        self.world_y = y
        self.target_location = target_location
        self.label = label
        self.size = 60  # Увеличенный размер
        self.animation_time = 0.0
    
    def update(self, dt):
        """Обновляет анимацию портала"""
        self.animation_time += dt * 3.0
    
    def check_collision(self, player_x, player_y):
        """Проверяет столкновение с игроком"""
        dx = player_x - self.world_x
        dy = player_y - self.world_y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance <= self.size / 2
    
    def draw(self, screen, iso_converter, camera_offset):
        """Отрисовывает портал"""
        screen_x, screen_y = iso_converter.world_to_screen(
            self.world_x, self.world_y
        )
        screen_x += camera_offset[0]
        screen_y += camera_offset[1]
        
        # Анимированный портал
        pulse = math.sin(self.animation_time) * 8
        radius = self.size // 2 + int(pulse)
        
        # Внешнее свечение (большой радиус)
        glow_radius = radius + 15
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (150, 100, 255, 80), 
                         (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (screen_x - glow_radius, screen_y - glow_radius))
        
        # Внешнее кольцо (толстое и яркое)
        pygame.draw.circle(screen, (150, 50, 255), (int(screen_x), int(screen_y)), radius, 5)
        # Среднее кольцо
        pygame.draw.circle(screen, (200, 100, 255), (int(screen_x), int(screen_y)), radius - 8, 4)
        # Внутреннее кольцо
        pygame.draw.circle(screen, (255, 150, 255), (int(screen_x), int(screen_y)), radius - 15, 3)
        # Центр (пульсирующий)
        center_radius = max(5, radius - 20 + int(pulse * 0.5))
        pygame.draw.circle(screen, (255, 200, 255), (int(screen_x), int(screen_y)), center_radius)
        
        # Текстовая метка
        if self.label:
            font = pygame.font.Font(None, 32)
            text_surface = font.render(self.label, True, (255, 255, 100))
            text_rect = text_surface.get_rect(center=(int(screen_x), int(screen_y) - radius - 25))
            # Фон для текста
            bg_rect = text_rect.inflate(10, 5)
            pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
            pygame.draw.rect(screen, (255, 255, 100), bg_rect, 2)
            screen.blit(text_surface, text_rect)


class Location:
    """Класс локации"""
    
    def __init__(self, name, background_color=(20, 20, 30)):
        """
        Args:
            name: Имя локации
            background_color: Цвет фона локации
        """
        self.name = name
        self.background_color = background_color
        self.enemies = []
        self.portals = []
        self.spawned = False
    
    def spawn_enemies(self, count=5, spawn_radius=200):
        """Создает врагов вокруг центра"""
        if self.spawned:
            return
        
        for i in range(count):
            angle = (2 * math.pi / count) * i
            distance = random.uniform(spawn_radius * 0.5, spawn_radius)
            x = math.cos(angle) * distance
            y = math.sin(angle) * distance
            enemy = Enemy(x, y, max_health=30)
            self.enemies.append(enemy)
        
        self.spawned = True
    
    def add_portal(self, x, y, target_location, label=""):
        """Добавляет портал"""
        portal = Portal(x, y, target_location, label)
        self.portals.append(portal)
        return portal
    
    def update(self, dt, player_x, player_y):
        """Обновляет локацию"""
        # Обновление врагов
        for enemy in self.enemies[:]:
            enemy.update(dt, player_x, player_y)
            if enemy.is_dead:
                self.enemies.remove(enemy)
        
        # Обновление порталов
        for portal in self.portals:
            portal.update(dt)
    
    def check_portal_collision(self, player_x, player_y):
        """Проверяет столкновение с порталами"""
        for portal in self.portals:
            if portal.check_collision(player_x, player_y):
                return portal.target_location
        return None
    
    def draw(self, screen, iso_converter, camera_offset):
        """Отрисовывает локацию"""
        # Отрисовка врагов
        for enemy in self.enemies:
            enemy.draw(screen, iso_converter, camera_offset)
        
        # Отрисовка порталов
        for portal in self.portals:
            portal.draw(screen, iso_converter, camera_offset)


class LocationManager:
    """Менеджер локаций"""
    
    def __init__(self):
        self.locations = {}
        self.current_location = None
    
    def add_location(self, location):
        """Добавляет локацию"""
        self.locations[location.name] = location
    
    def set_location(self, location_name):
        """Устанавливает текущую локацию"""
        if location_name in self.locations:
            self.current_location = self.locations[location_name]
            return True
        return False
    
    def get_current_location(self):
        """Возвращает текущую локацию"""
        return self.current_location

