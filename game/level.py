"""
Модуль для работы с уровнями
Загрузка, отображение и управление уровнями игры
"""

import json
import os
import sys
from pathlib import Path

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
            image = pygame.image.load(str(self.image_path)).convert_alpha()
            
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
                    tile = image.subsurface(rect).copy()
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
    
    def __init__(self, name="default"):
        self.name = name
        self.width = 20
        self.height = 20
        self.tiles = {}  # {(x, y): {'tileset': name, 'tile': index}}
        self.tilesets = {}  # {name: TileSet}
        
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
            
            print(f"Level '{self.name}' loaded: {len(self.tiles)} tiles")
            return True
        except Exception as e:
            print(f"Error loading level {level_name}: {e}")
            return False
    
    def get_tile_surface(self, x, y):
        """Возвращает поверхность тайла по координатам"""
        tile_data = self.tiles.get((x, y))
        if not tile_data:
            return None
        
        tileset_name = tile_data.get('tileset')
        tile_index = tile_data.get('tile', 0)
        
        tileset = self.tilesets.get(tileset_name)
        if tileset:
            return tileset.get_tile(tile_index)
        
        return None
    
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
    
    def draw(self, screen, camera_offset, iso_converter=None, fog_of_war=None):
        """Отрисовывает уровень с учётом тумана войны"""
        # Сортируем тайлы для правильного порядка отрисовки (дальние сначала)
        sorted_tiles = sorted(self.tiles.keys(), key=lambda pos: (pos[0] + pos[1], pos[0]))
        
        for (tx, ty) in sorted_tiles:
            tile_surface = self.get_tile_surface(tx, ty)
            if not tile_surface:
                continue
            
            # Изометрические координаты
            screen_x = (tx - ty) * (TILE_WIDTH // 2)
            screen_y = (tx + ty) * (TILE_HEIGHT // 2)
            
            # Применяем смещение камеры
            final_x = screen_x + camera_offset[0]
            final_y = screen_y + camera_offset[1]
            
            # Отрисовываем только видимые на экране тайлы
            if -TILE_WIDTH < final_x < screen.get_width() + TILE_WIDTH:
                if -TILE_HEIGHT < final_y < screen.get_height() + TILE_HEIGHT:
                    # Применяем затемнение для тумана войны
                    if fog_of_war:
                        if fog_of_war.is_tile_visible(tx, ty):
                            # Полностью видимый тайл
                            screen.blit(tile_surface, (final_x, final_y))
                        elif fog_of_war.is_tile_explored(tx, ty):
                            # Исследованный, но сейчас не видимый - затемняем
                            dark_tile = tile_surface.copy()
                            dark_tile.fill((80, 80, 80), special_flags=pygame.BLEND_MULT)
                            screen.blit(dark_tile, (final_x, final_y))
                        # Неисследованные тайлы не рисуем
                    else:
                        screen.blit(tile_surface, (final_x, final_y))


class LevelManager:
    """Менеджер уровней - загрузка и переключение"""
    
    def __init__(self):
        self.current_level = None
        self.available_levels = []
        self._scan_levels()
    
    def _scan_levels(self):
        """Сканирует доступные уровни"""
        base_path = _get_base_path()
        levels_dir = base_path / "game" / "levels"
        
        self.available_levels = []
        if levels_dir.exists():
            for file in levels_dir.glob("*.json"):
                self.available_levels.append(file.stem)
        
        self.available_levels.sort()
        print(f"Found {len(self.available_levels)} levels: {self.available_levels}")
    
    def load_level(self, level_name):
        """Загружает указанный уровень"""
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

