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
        
        # Радиус видимости игрока для объектов (враги, предметы) - в мировых координатах
        self.vision_radius = 12.0  # Увеличено для лучшей видимости врагов
        
        # Радиус для исследования карты (для миникарты и статистики)
        self.exploration_radius = 10.0
        
        # Исследованные тайлы
        self.explored_tiles = set()
        
        # Видимые сейчас тайлы
        self.visible_tiles = set()
        
        # Позиция игрока
        self.last_player_pos = None
        
        # Кэш для оптимизации отрисовки тумана
        self._fog_cache = None
        self._fog_cache_key = None
    
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
    
    def draw_fog(self, screen, camera_offset, iso_converter, level_tiles=None):
        """
        Отрисовывает затемнение областей вне радиуса видимости (оптимизированная версия)
        
        Затемняет тайлы, которые видны на экране, но не в текущем радиусе видимости игрока.
        
        Args:
            screen: Экран для отрисовки
            camera_offset: Смещение камеры (x, y)
            iso_converter: Конвертер изометрических координат
            level_tiles: Словарь тайлов уровня {(x, y): tile_data}
        """
        if self.last_player_pos is None:
            return
        
        # Размеры тайла (изометрические)
        TILE_WIDTH = 128
        TILE_HEIGHT = 64
        
        # Получаем границы экрана (те же, что в level.draw())
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        screen_left = -TILE_WIDTH * 2
        screen_right = screen_width + TILE_WIDTH * 2
        screen_top = -TILE_HEIGHT * 2
        screen_bottom = screen_height + TILE_HEIGHT * 2
        
        player_x, player_y = self.last_player_pos
        
        # Создаем поверхность для затемнения
        fog_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Оптимизация: используем тот же радиус, что и в level.draw() для согласованности
        visible_radius = max(screen_width, screen_height) / (TILE_WIDTH // 2) + 12
        visible_radius_sq = visible_radius * visible_radius
        
        fog_tiles = []
        
        # Округляем координаты для стабильности
        player_tile_x = int(player_x)
        player_tile_y = int(player_y)
        
        # Генерируем тайлы для затемнения на основе видимой области экрана
        # Это гарантирует, что все тайлы в видимой области будут затемнены
        radius_int = int(visible_radius) + 2
        
        for dx in range(-radius_int, radius_int + 1):
            for dy in range(-radius_int, radius_int + 1):
                tx = player_tile_x + dx
                ty = player_tile_y + dy
                
                # Быстрая проверка расстояния от игрока (без sqrt)
                distance_sq = dx * dx + dy * dy
                if distance_sq > visible_radius_sq:
                    continue  # Слишком далеко
                
                # Проверяем, виден ли тайл в радиусе видимости
                if (tx, ty) in self.visible_tiles:
                    continue  # Видимые тайлы не затемняем
                
                # Изометрические координаты
                screen_x = (tx - ty) * (TILE_WIDTH // 2)
                screen_y = (tx + ty) * (TILE_HEIGHT // 2)
                
                # Применяем смещение камеры
                final_x = screen_x + camera_offset[0]
                final_y = screen_y + camera_offset[1]
                
                # Проверяем видимость на экране (с запасом, как в level.draw())
                if final_x < screen_left or final_x > screen_right:
                    continue
                if final_y < screen_top or final_y > screen_bottom:
                    continue
                
                # Определяем уровень затемнения
                # Исследованные, но не видимые - менее затемненные
                # Неисследованные - более затемненные
                if (tx, ty) in self.explored_tiles:
                    # Исследованные, но не видимые - легкое затемнение
                    fog_alpha = 140
                else:
                    # Неисследованные - сильное затемнение
                    fog_alpha = 200
                
                # Добавляем в список для отрисовки
                fog_tiles.append((int(final_x), int(final_y), fog_alpha))
        
        # Убрано ограничение на количество тайлов - теперь затемняются все тайлы в видимой области
        
        # Batch отрисовка затемнения
        for final_x, final_y, fog_alpha in fog_tiles:
            # Рисуем затемнение (ромб тайла)
            points = [
                (final_x, final_y - TILE_HEIGHT // 2),  # Верх
                (final_x + TILE_WIDTH // 2, final_y),   # Право
                (final_x, final_y + TILE_HEIGHT // 2),   # Низ
                (final_x - TILE_WIDTH // 2, final_y)     # Лево
            ]
            
            # Затемнение (темный полупрозрачный цвет)
            pygame.draw.polygon(fog_surface, (0, 0, 0, fog_alpha), points)
        
        # Отрисовываем затемнение на экран
        screen.blit(fog_surface, (0, 0))
    
    def get_explored_for_minimap(self):
        """Возвращает множество исследованных тайлов для миникарты"""
        return self.explored_tiles
    
    def get_visible_for_minimap(self):
        """Возвращает множество видимых сейчас тайлов для миникарты"""
        return self.visible_tiles
