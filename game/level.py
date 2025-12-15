"""
Модуль для работы с уровнями
Загрузка, отображение и управление уровнями игры
"""

import json
import os
import sys
from pathlib import Path
import random
import math

import pygame


def _get_base_path():
    """Получает базовый путь для ресурсов"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


# Константы тайлов
TILE_WIDTH = 128
TILE_HEIGHT = 64


class TileSet:
    """Набор тайлов из спрайтшита"""
    
    def __init__(self, name, image_path):
        self.name = name
        self.image_path = image_path
        self.tiles = []
        self._load()
    
    def _load(self):
        """Загружает и разрезает спрайтшит на тайлы"""
        try:
            # Загружаем изображение с оптимизацией для аппаратного ускорения
            image = pygame.image.load(str(self.image_path))
            # convert_alpha() оптимизирует изображение для быстрого blitting
            image = image.convert_alpha()
            
            cols = image.get_width() // TILE_WIDTH
            rows = image.get_height() // TILE_HEIGHT
            
            for row in range(rows):
                for col in range(cols):
                    rect = pygame.Rect(
                        col * TILE_WIDTH,
                        row * TILE_HEIGHT,
                        TILE_WIDTH,
                        TILE_HEIGHT
                    )
                    # Используем subsurface для эффективного доступа без копирования
                    tile = image.subsurface(rect)
                    # Копируем только при необходимости (для независимости от исходного изображения)
                    tile = tile.copy()
                    # Дополнительная оптимизация: конвертируем в формат экрана для быстрого blitting
                    # Это особенно эффективно при использовании аппаратного ускорения
                    self.tiles.append(tile)
            
            print(f"TileSet '{self.name}' loaded: {len(self.tiles)} tiles")
        except Exception as e:
            print(f"Error loading tileset {self.name}: {e}")
    
    def get_tile(self, index):
        """Возвращает тайл по индексу"""
        if 0 <= index < len(self.tiles):
            return self.tiles[index]
        return None


class Level:
    """Уровень игры с тайловой картой"""
    
    def __init__(self, name="default", procedural=False, seed=None):
        """
        Args:
            name: Имя уровня
            procedural: Если True, использует процедурную генерацию
            seed: Зерно для процедурной генерации (None = случайное)
        """
        self.name = name
        self.width = 20
        self.height = 20
        self.tiles = {}  # {(x, y): {'tileset': name, 'tile': index}}
        self.tilesets = {}  # {name: TileSet}
        
        # Процедурная генерация
        self.procedural = procedural
        self.procedural_generator = None
        if procedural:
            from game.procedural_world import ProceduralWorldGenerator
            self.procedural_generator = ProceduralWorldGenerator(seed=seed)
            # Радиус загрузки тайлов (оптимизирован для производительности)
            self.load_radius = 20
        
        # Кэши для оптимизации производительности
        self._dark_tiles_cache = {}  # Кэш затемненных тайлов {(tileset_name, tile_index): surface}
        
        self._load_tilesets()
    
    def _load_tilesets(self):
        """Загружает все доступные тайлсеты"""
        base_path = _get_base_path()
        textures_dir = base_path / "game" / "images" / "textures"
        
        if textures_dir.exists():
            for file in textures_dir.glob("*.png"):
                name = file.stem
                self.tilesets[name] = TileSet(name, file)
    
    def load(self, level_name):
        """Загружает уровень из файла"""
        base_path = _get_base_path()
        level_file = base_path / "game" / "levels" / f"{level_name}.json"
        
        if not level_file.exists():
            print(f"Level file not found: {level_file}")
            return False
        
        try:
            with open(level_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.name = data.get('name', level_name)
            self.width = data.get('width', 20)
            self.height = data.get('height', 20)
            
            self.tiles = {}
            for key, value in data.get('tiles', {}).items():
                x, y = map(int, key.split(','))
                self.tiles[(x, y)] = value
            
            self._dark_tiles_cache.clear()  # Очищаем кэш затемненных тайлов
            
            print(f"Level '{self.name}' loaded: {len(self.tiles)} tiles")
            return True
        except Exception as e:
            print(f"Error loading level {level_name}: {e}")
            return False
    
    def get_tile_surface(self, x, y):
        """Возвращает поверхность тайла по координатам"""
        # Если процедурная генерация, получаем тайл из генератора
        if self.procedural:
            tile_data = self.procedural_generator.get_tile(x, y)
        else:
            tile_data = self.tiles.get((x, y))
        
        if not tile_data:
            return None
        
        tileset_name = tile_data.get('tileset')
        tile_index = tile_data.get('tile', 0)
        
        tileset = self.tilesets.get(tileset_name)
        if tileset:
            return tileset.get_tile(tile_index)
        
        return None
    
    def update_procedural_tiles(self, center_x, center_y, force=False):
        """
        Обновляет тайлы для процедурной генерации вокруг центра
        Вызывается при движении игрока
        
        Args:
            center_x, center_y: Позиция центра
            force: Принудительное обновление (игнорирует порог)
        """
        if not self.procedural or not self.procedural_generator:
            return
        
        # Оптимизация: обновляем только при значительном перемещении
        if not force:
            dx = center_x - getattr(self, '_last_update_x', center_x)
            dy = center_y - getattr(self, '_last_update_y', center_y)
            distance_sq = dx * dx + dy * dy
            
            # Обновляем только если переместились на значительное расстояние (без sqrt для производительности)
            if distance_sq < 5.0 * 5.0:  # Порог обновления 5 тайлов (в квадрате для скорости)
                return
        
        # Сохраняем позицию последнего обновления
        self._last_update_x = center_x
        self._last_update_y = center_y
        
        # Получаем новые тайлы в радиусе
        new_tiles = self.procedural_generator.get_all_tiles_in_radius(
            center_x, center_y, self.load_radius
        )
        
        # Объединяем с существующими тайлами
        self.tiles.update(new_tiles)
        
        # Ограничиваем размер кэша тайлов для производительности
        max_tiles = 1500  # Уменьшено для производительности
        
        if len(self.tiles) > max_tiles:
            # Удаляем самые дальние тайлы от центра (оптимизировано - без sqrt)
            px, py = center_x, center_y
            tiles_with_distance_sq = [
                ((x, y), (x - px)**2 + (y - py)**2)
                for (x, y) in self.tiles.keys()
            ]
            # Сортируем по расстоянию (дальние первыми)
            tiles_with_distance_sq.sort(key=lambda item: item[1], reverse=True)
            
            # Удаляем самые дальние тайлы
            tiles_to_remove = len(self.tiles) - max_tiles
            for i in range(tiles_to_remove):
                tile_pos = tiles_with_distance_sq[i][0]
                del self.tiles[tile_pos]
    
    def world_to_iso(self, world_x, world_y):
        """Конвертирует мировые координаты в изометрические экранные"""
        # Размер тайла в мировых координатах
        tile_world_size = 1.0
        
        # Координаты тайла
        tile_x = world_x / tile_world_size
        tile_y = world_y / tile_world_size
        
        # Изометрическое преобразование
        screen_x = (tile_x - tile_y) * (TILE_WIDTH // 2)
        screen_y = (tile_x + tile_y) * (TILE_HEIGHT // 2)
        
        return screen_x, screen_y
    
    def draw(self, screen, camera_offset, iso_converter=None, fog_of_war=None, player_pos=None):
        """
        Отрисовывает уровень с учётом тумана войны
        
        Args:
            player_pos: (x, y) позиция игрока для обновления процедурных тайлов
        """
        # Обновляем процедурные тайлы если нужно
        if self.procedural and player_pos:
            # При первом вызове принудительно обновляем
            force = not hasattr(self, '_last_update_x')
            self.update_procedural_tiles(player_pos[0], player_pos[1], force=force)
        
        # Предвычисляем границы экрана для оптимизации
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Более строгие границы для отрисовки (только видимые тайлы)
        screen_left = -TILE_WIDTH * 2
        screen_right = screen_width + TILE_WIDTH * 2
        screen_top = -TILE_HEIGHT * 2
        screen_bottom = screen_height + TILE_HEIGHT * 2
        
        # Кэш видимых тайлов для оптимизации (обновляется только при движении)
        cache_key = None
        if player_pos:
            # Используем грубую сетку для кэширования (каждые 5 тайлов)
            cache_x = int(player_pos[0] // 5) * 5
            cache_y = int(player_pos[1] // 5) * 5
            cache_key = (cache_x, cache_y)
        
        # Проверяем кэш видимых тайлов
        if hasattr(self, '_visible_tiles_cache') and cache_key == getattr(self, '_last_cache_key', None):
            tiles_to_draw = self._visible_tiles_cache
        else:
            # Вычисляем видимую область в мировых координатах для предварительной фильтрации
            if iso_converter and player_pos:
                # Примерная видимая область в мировых координатах
                # Учитываем изометрию: экранные координаты зависят от суммы/разности мировых
                # Оптимизировано: уменьшено для производительности, но достаточно для видимости
                visible_radius = max(screen_width, screen_height) / (TILE_WIDTH // 2) + 12
                px, py = player_pos
                visible_radius_sq = visible_radius * visible_radius
                
                # Предварительная фильтрация по расстоянию (быстрее чем изометрические преобразования)
                tiles_to_draw = []
                for (tx, ty) in self.tiles.keys():
                    # Быстрая проверка расстояния без sqrt
                    dx = tx - px
                    dy = ty - py
                    distance_sq = dx * dx + dy * dy
                    if distance_sq > visible_radius_sq:
                        continue
                    
                    tiles_to_draw.append((tx, ty))
            else:
                tiles_to_draw = list(self.tiles.keys())
            
            # Сортируем только видимые тайлы (для правильного порядка отрисовки)
            tiles_to_draw.sort(key=lambda pos: (pos[0] + pos[1], pos[0]))
            
            # Кэшируем результат
            if cache_key is not None:
                self._visible_tiles_cache = tiles_to_draw
                self._last_cache_key = cache_key
        
        # Отрисовываем тайлы
        # Тайлы отрисовываются всегда (без проверки тумана войны)
        # Туман войны применяется только к объектам (врагам, предметам)
        # Оптимизация: предварительно фильтруем тайлы по экранным координатам
        tiles_to_render = []
        
        for (tx, ty) in tiles_to_draw:
            # Изометрические координаты
            screen_x = (tx - ty) * (TILE_WIDTH // 2)
            screen_y = (tx + ty) * (TILE_HEIGHT // 2)
            
            # Применяем смещение камеры
            final_x = screen_x + camera_offset[0]
            final_y = screen_y + camera_offset[1]
            
            # Строгая проверка видимости на экране
            if final_x < screen_left or final_x > screen_right:
                continue
            if final_y < screen_top or final_y > screen_bottom:
                continue
            
            # Получаем данные тайла
            tile_data = self.tiles.get((tx, ty))
            if not tile_data:
                continue
            
            tileset_name = tile_data.get('tileset')
            tile_index = tile_data.get('tile', 0)
            
            # Быстрый доступ к тайлсету
            tileset = self.tilesets.get(tileset_name)
            if not tileset:
                continue
            
            tile_surface = tileset.get_tile(tile_index)
            if not tile_surface:
                continue
            
            # Добавляем в список для отрисовки
            tiles_to_render.append((tile_surface, final_x, final_y))
        
        # Batch отрисовка всех тайлов
        for tile_surface, x, y in tiles_to_render:
            screen.blit(tile_surface, (x, y))


class LevelManager:
    """Менеджер уровней - загрузка и переключение"""
    
    def __init__(self):
        self.current_level = None
        self.available_levels = []
        self._scan_levels()
        
        # Создаем процедурный уровень по умолчанию
        self.procedural_level = None
        self._create_procedural_level()
    
    def _scan_levels(self):
        """Сканирует доступные уровни"""
        base_path = _get_base_path()
        levels_dir = base_path / "game" / "levels"
        
        self.available_levels = []
        if levels_dir.exists():
            for file in levels_dir.glob("*.json"):
                self.available_levels.append(file.stem)
        
        self.available_levels.sort()
        # Добавляем процедурный уровень в список
        self.available_levels.insert(0, "procedural")
        print(f"Found {len(self.available_levels)} levels: {self.available_levels}")
    
    def _create_procedural_level(self):
        """Создает процедурный уровень"""
        self.procedural_level = Level(name="procedural", procedural=True, seed=None)
    
    def load_level(self, level_name):
        """Загружает указанный уровень"""
        # Если процедурный уровень
        if level_name == "procedural":
            if not self.procedural_level:
                self._create_procedural_level()
            self.current_level = self.procedural_level
            return True
        
        # Обычный уровень из файла
        self.current_level = Level(level_name)
        if self.current_level.load(level_name):
            return True
        return False
    
    def get_current_level(self):
        """Возвращает текущий уровень"""
        return self.current_level
    
    def get_available_levels(self):
        """Возвращает список доступных уровней"""
        return self.available_levels
    
    def next_level(self):
        """Переключает на следующий уровень"""
        if not self.available_levels:
            return False
        
        current_name = self.current_level.name if self.current_level else ""
        try:
            idx = self.available_levels.index(current_name)
            next_idx = (idx + 1) % len(self.available_levels)
        except ValueError:
            next_idx = 0
        
        return self.load_level(self.available_levels[next_idx])
    
    def prev_level(self):
        """Переключает на предыдущий уровень"""
        if not self.available_levels:
            return False
        
        current_name = self.current_level.name if self.current_level else ""
        try:
            idx = self.available_levels.index(current_name)
            prev_idx = (idx - 1) % len(self.available_levels)
        except ValueError:
            prev_idx = 0
        
        return self.load_level(self.available_levels[prev_idx])

