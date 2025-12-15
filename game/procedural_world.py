"""
Модуль процедурной генерации мира на основе шума Перлина
Реализует бесконечный мир с чанками и биомами
"""
import random
import math


class PerlinNoise:
    """
    Упрощенная реализация шума Перлина для процедурной генерации
    """
    
    def __init__(self, seed=None):
        """Инициализация генератора шума с зерном"""
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        
        self.seed = seed
        random.seed(seed)
        
        # Генерируем перестановочную таблицу
        self.permutation = list(range(256))
        random.shuffle(self.permutation)
        self.permutation += self.permutation  # Дублируем для упрощения
        
        # Градиентные векторы
        self.gradients = []
        for i in range(256):
            angle = random.uniform(0, 2 * math.pi)
            self.gradients.append((math.cos(angle), math.sin(angle)))
    
    def _fade(self, t):
        """Функция затухания для плавности"""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a, b, t):
        """Линейная интерполяция"""
        return a + t * (b - a)
    
    def _dot(self, grad, x, y):
        """Скалярное произведение градиента и вектора"""
        return grad[0] * x + grad[1] * y
    
    def noise(self, x, y):
        """
        Генерирует значение шума для координат (x, y)
        Возвращает значение от -1.0 до 1.0
        """
        # Определяем углы единичного квадрата
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        
        # Дробные части
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        
        # Применяем функцию затухания
        u = self._fade(xf)
        v = self._fade(yf)
        
        # Получаем градиенты для углов
        aa = self.permutation[self.permutation[X] + Y]
        ab = self.permutation[self.permutation[X] + Y + 1]
        ba = self.permutation[self.permutation[X + 1] + Y]
        bb = self.permutation[self.permutation[X + 1] + Y + 1]
        
        # Скалярные произведения
        n00 = self._dot(self.gradients[aa], xf, yf)
        n01 = self._dot(self.gradients[ab], xf, yf - 1)
        n10 = self._dot(self.gradients[ba], xf - 1, yf)
        n11 = self._dot(self.gradients[bb], xf - 1, yf - 1)
        
        # Интерполяция
        x1 = self._lerp(n00, n10, u)
        x2 = self._lerp(n01, n11, u)
        return self._lerp(x1, x2, v)
    
    def octave_noise(self, x, y, octaves=4, persistence=0.5, scale=1.0):
        """
        Многооктавный шум для более естественного вида
        """
        value = 0.0
        amplitude = 1.0
        frequency = scale
        max_value = 0.0
        
        for _ in range(octaves):
            value += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0
        
        return value / max_value


class Biome:
    """Класс биома с правилами генерации"""
    
    def __init__(self, name, tileset_name, tile_index, spawn_chance=0.0, enemy_types=None):
        """
        Args:
            name: Название биома
            tileset_name: Имя тайлсета для этого биома
            tile_index: Индекс тайла в тайлсете
            spawn_chance: Вероятность спавна врагов (0.0 - 1.0)
            enemy_types: Список типов врагов для этого биома (None = все кроме default)
        """
        self.name = name
        self.tileset_name = tileset_name
        self.tile_index = tile_index
        self.spawn_chance = spawn_chance
        self.enemy_types = enemy_types if enemy_types else []
    
    def get_tile_data(self):
        """Возвращает данные тайла для этого биома"""
        return {
            'tileset': self.tileset_name,
            'tile': self.tile_index
        }


# Определение биомов
BIOMES = {
    'plains': Biome('plains', 'grass_green_128x64', 0, spawn_chance=0.15),
    'forest': Biome('forest', 'forest_ground_128x64', 0, spawn_chance=0.25),
    'desert': Biome('desert', 'sand_128x64', 0, spawn_chance=0.20),
    'dirt': Biome('dirt', 'dirt_128x64', 0, spawn_chance=0.10),
    'dry_grass': Biome('dry_grass', 'grass_dry_128x64', 0, spawn_chance=0.18),
    'medium_grass': Biome('medium_grass', 'grass_medium_128x64', 0, spawn_chance=0.12),
    'stone': Biome('stone', 'stone_path_128x64', 0, spawn_chance=0.05),
    'dark_dirt': Biome('dark_dirt', 'dirt_dark_128x64', 0, spawn_chance=0.22),
}

BIOME_LIST = list(BIOMES.keys())


class Chunk:
    """Чанк мира - единица генерации"""
    
    def __init__(self, chunk_x, chunk_y, size=16):
        """
        Args:
            chunk_x, chunk_y: Координаты чанка
            size: Размер чанка в тайлах
        """
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size
        self.tiles = {}  # {(x, y): {'tileset': name, 'tile': index}}
        self.generated = False
        self.enemy_spawn_points = []  # Точки спавна врагов
    
    def get_world_bounds(self):
        """Возвращает границы чанка в мировых координатах"""
        start_x = self.chunk_x * self.size
        start_y = self.chunk_y * self.size
        end_x = start_x + self.size
        end_y = start_y + self.size
        return start_x, start_y, end_x, end_y


class ProceduralWorldGenerator:
    """Генератор процедурного мира"""
    
    def __init__(self, seed=None, chunk_size=16):
        """
        Args:
            seed: Зерно для генерации (None = случайное)
            chunk_size: Размер чанка в тайлах
        """
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        
        self.seed = seed
        self.chunk_size = chunk_size
        
        # Генераторы шума для разных карт
        self.height_noise = PerlinNoise(seed)
        self.biome_noise = PerlinNoise(seed + 1000)  # Разное зерно для биомов
        self.detail_noise = PerlinNoise(seed + 2000)  # Для деталей
        
        # Кэш сгенерированных чанков
        self.chunks = {}  # {(chunk_x, chunk_y): Chunk}
        
        # Параметры генерации
        self.height_scale = 0.05  # Масштаб карты высот
        self.biome_scale = 0.03   # Масштаб карты биомов
        self.detail_scale = 0.15  # Масштаб деталей
        
        # Пороги для биомов
        self.biome_thresholds = {
            'desert': (-0.3, -0.1),
            'dirt': (-0.1, 0.0),
            'dry_grass': (0.0, 0.2),
            'plains': (0.2, 0.4),
            'medium_grass': (0.4, 0.6),
            'forest': (0.6, 0.8),
            'dark_dirt': (0.8, 0.9),
            'stone': (0.9, 1.0),
        }
    
    def _get_chunk_key(self, chunk_x, chunk_y):
        """Возвращает ключ чанка"""
        return (chunk_x, chunk_y)
    
    def _world_to_chunk(self, world_x, world_y):
        """Преобразует мировые координаты в координаты чанка"""
        chunk_x = int(math.floor(world_x / self.chunk_size))
        chunk_y = int(math.floor(world_y / self.chunk_size))
        return chunk_x, chunk_y
    
    def _get_biome(self, world_x, world_y):
        """
        Определяет биом для координат на основе шума
        """
        # Получаем значение шума биомов
        biome_value = self.biome_noise.octave_noise(
            world_x * self.biome_scale,
            world_y * self.biome_scale,
            octaves=3,
            persistence=0.6,
            scale=1.0
        )
        
        # Нормализуем от -1..1 к 0..1
        biome_value = (biome_value + 1.0) / 2.0
        
        # Определяем биом по порогам
        for biome_name, (min_val, max_val) in self.biome_thresholds.items():
            if min_val <= biome_value < max_val:
                return BIOMES[biome_name]
        
        # По умолчанию равнины
        return BIOMES['plains']
    
    def _get_height(self, world_x, world_y):
        """
        Получает высоту для координат (для будущего использования)
        """
        height = self.height_noise.octave_noise(
            world_x * self.height_scale,
            world_y * self.height_scale,
            octaves=4,
            persistence=0.5,
            scale=1.0
        )
        return (height + 1.0) / 2.0  # Нормализуем к 0..1
    
    def generate_chunk(self, chunk_x, chunk_y):
        """
        Генерирует чанк по координатам
        """
        chunk_key = self._get_chunk_key(chunk_x, chunk_y)
        
        # Проверяем кэш
        if chunk_key in self.chunks:
            return self.chunks[chunk_key]
        
        # Создаем новый чанк
        chunk = Chunk(chunk_x, chunk_y, self.chunk_size)
        
        # Генерируем тайлы
        start_x, start_y, end_x, end_y = chunk.get_world_bounds()
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                # Определяем биом
                biome = self._get_biome(x, y)
                
                # Получаем данные тайла
                tile_data = biome.get_tile_data()
                chunk.tiles[(x, y)] = tile_data
                
                # Определяем точки спавна врагов
                # Используем более редкий спавн - только каждый 3-й тайл проверяем
                if x % 3 == 0 and y % 3 == 0:
                    if random.random() < biome.spawn_chance * 0.5:  # Умеренная вероятность
                        # Проверяем, что это не слишком близко к центру (0, 0)
                        distance_from_origin = math.sqrt(x*x + y*y)
                        if distance_from_origin > 8.0:  # Минимальное расстояние от спавна
                            chunk.enemy_spawn_points.append((x, y, biome))
        
        chunk.generated = True
        self.chunks[chunk_key] = chunk
        
        return chunk
    
    def get_tile(self, world_x, world_y):
        """
        Получает тайл для мировых координат
        Генерирует чанк при необходимости
        """
        chunk_x, chunk_y = self._world_to_chunk(world_x, world_y)
        chunk = self.generate_chunk(chunk_x, chunk_y)
        
        # Получаем тайл из чанка
        tile_key = (int(world_x), int(world_y))
        return chunk.tiles.get(tile_key)
    
    def get_chunks_in_radius(self, center_x, center_y, radius):
        """
        Возвращает все чанки в радиусе от центра
        Используется для загрузки видимых чанков
        """
        chunks = []
        
        # Определяем границы в чанках
        min_chunk_x, min_chunk_y = self._world_to_chunk(
            center_x - radius, center_y - radius
        )
        max_chunk_x, max_chunk_y = self._world_to_chunk(
            center_x + radius, center_y + radius
        )
        
        # Генерируем все чанки в радиусе
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                chunk = self.generate_chunk(chunk_x, chunk_y)
                chunks.append(chunk)
        
        return chunks
    
    def get_enemy_spawn_points_in_radius(self, center_x, center_y, radius):
        """
        Возвращает точки спавна врагов в радиусе
        """
        spawn_points = []
        chunks = self.get_chunks_in_radius(center_x, center_y, radius)
        
        for chunk in chunks:
            for x, y, biome in chunk.enemy_spawn_points:
                # Проверяем расстояние
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance <= radius:
                    spawn_points.append((x, y, biome))
        
        return spawn_points
    
    def get_all_tiles_in_radius(self, center_x, center_y, radius):
        """
        Возвращает все тайлы в радиусе (для отрисовки)
        """
        tiles = {}
        chunks = self.get_chunks_in_radius(center_x, center_y, radius)
        
        for chunk in chunks:
            for (x, y), tile_data in chunk.tiles.items():
                # Проверяем расстояние
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance <= radius:
                    tiles[(x, y)] = tile_data
        
        return tiles

