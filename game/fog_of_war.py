"""
Система тумана войны (Fog of War)
Управляет видимостью областей карты
"""

import pygame
import math


class FogOfWar:
    """Система тумана войны"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Радиус видимости игрока (в мировых координатах)
        self.vision_radius = 5.0  # Уменьшено для врагов
        
        # Радиус для исследования карты (больше чем видимость врагов)
        self.exploration_radius = 6.0
        
        # Исследованные тайлы
        self.explored_tiles = set()
        
        # Видимые сейчас тайлы
        self.visible_tiles = set()
        
        # Позиция игрока
        self.last_player_pos = None
    
    def update(self, player_x, player_y):
        """
        Обновляет туман войны
        """
        self.visible_tiles.clear()
        
        # Определяем тайлы в радиусе исследования
        radius_int = int(self.exploration_radius) + 1
        
        for dx in range(-radius_int, radius_int + 1):
            for dy in range(-radius_int, radius_int + 1):
                tile_x = int(player_x) + dx
                tile_y = int(player_y) + dy
                
                # Проверяем расстояние от центра тайла до игрока
                tile_center_x = tile_x + 0.5
                tile_center_y = tile_y + 0.5
                distance = math.sqrt(
                    (tile_center_x - player_x) ** 2 + 
                    (tile_center_y - player_y) ** 2
                )
                
                if distance <= self.exploration_radius:
                    self.visible_tiles.add((tile_x, tile_y))
                    self.explored_tiles.add((tile_x, tile_y))
        
        self.last_player_pos = (player_x, player_y)
    
    def is_tile_visible(self, tile_x, tile_y):
        """Проверяет, виден ли тайл сейчас"""
        return (tile_x, tile_y) in self.visible_tiles
    
    def is_tile_explored(self, tile_x, tile_y):
        """Проверяет, был ли тайл исследован"""
        return (tile_x, tile_y) in self.explored_tiles
    
    def is_position_visible(self, world_x, world_y):
        """Проверяет, видна ли позиция (для врагов) - меньший радиус"""
        if self.last_player_pos is None:
            return False
        
        player_x, player_y = self.last_player_pos
        distance = math.sqrt(
            (world_x - player_x) ** 2 + 
            (world_y - player_y) ** 2
        )
        return distance <= self.vision_radius
    
    def draw_fog(self, screen, camera_offset, iso_converter):
        """
        Отрисовывает затемнение неисследованных областей
        Без круглого ореола - только затемнение по тайлам
        """
        # Ничего не рисуем - туман реализован через затемнение в level.py
        # и скрытие врагов
        pass
    
    def get_explored_for_minimap(self):
        """Возвращает множество исследованных тайлов для миникарты"""
        return self.explored_tiles
    
    def get_visible_for_minimap(self):
        """Возвращает множество видимых сейчас тайлов для миникарты"""
        return self.visible_tiles
