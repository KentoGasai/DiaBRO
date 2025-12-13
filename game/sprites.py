"""
Система спрайтов и анимаций
"""
import pygame
import math
import os


class SpriteSheet:
    """Класс для работы со спрайтшитами"""
    
    def __init__(self, filepath, frame_width, frame_height):
        """
        Args:
            filepath: Путь к файлу спрайтшита
            frame_width: Ширина одного кадра
            frame_height: Высота одного кадра
        """
        self.sheet = pygame.image.load(filepath).convert_alpha()
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Количество кадров по горизонтали и вертикали
        self.cols = self.sheet.get_width() // frame_width
        self.rows = self.sheet.get_height() // frame_height
    
    def get_frame(self, col, row, scale=1.0):
        """
        Извлекает один кадр из спрайтшита
        
        Args:
            col: Номер столбца (0-based)
            row: Номер строки (0-based)
            scale: Масштаб (1.0 = оригинальный размер)
            
        Returns:
            pygame.Surface с кадром
        """
        frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
        frame.blit(self.sheet, (0, 0), 
                   (col * self.frame_width, row * self.frame_height,
                    self.frame_width, self.frame_height))
        
        if scale != 1.0:
            new_width = int(self.frame_width * scale)
            new_height = int(self.frame_height * scale)
            frame = pygame.transform.scale(frame, (new_width, new_height))
        
        return frame
    
    def get_animation_frames(self, row, start_col, end_col, scale=1.0):
        """
        Извлекает несколько кадров для анимации
        
        Args:
            row: Номер строки
            start_col: Начальный столбец
            end_col: Конечный столбец (не включая)
            scale: Масштаб
            
        Returns:
            Список pygame.Surface
        """
        frames = []
        for col in range(start_col, end_col):
            frames.append(self.get_frame(col, row, scale))
        return frames


class CharacterSprites:
    """Спрайты персонажа с 8 направлениями"""
    
    # Маппинг угла в радианах на индекс направления (строку спрайтшита)
    # Порядок в спрайтшите: влево, влево-вверх, вверх, вправо-вверх, 
    #                       вправо, вправо-вниз, вниз, влево-вниз
    DIRECTION_MAP = {
        0: 4,   # вправо (0°)
        1: 3,   # вправо-вверх (45°)
        2: 2,   # вверх (90°)
        3: 1,   # влево-вверх (135°)
        4: 0,   # влево (180°)
        5: 7,   # влево-вниз (225°)
        6: 6,   # вниз (270°)
        7: 5,   # вправо-вниз (315°)
    }
    
    def __init__(self, character_path, weapon_path=None, scale=0.25):
        """
        Args:
            character_path: Путь к спрайтшиту персонажа
            weapon_path: Путь к спрайтшиту оружия (опционально)
            scale: Масштаб спрайтов (256px * 0.25 = 64px)
        """
        self.scale = scale
        self.frame_size = int(256 * scale)  # Размер кадра после масштабирования
        
        # Загрузка спрайтшитов
        self.character_sheet = SpriteSheet(character_path, 256, 256)
        self.weapon_sheet = None
        if weapon_path and os.path.exists(weapon_path):
            self.weapon_sheet = SpriteSheet(weapon_path, 256, 256)
        
        # Кэш анимаций: {(animation_name, direction): [frames]}
        self.animation_cache = {}
        
        # Предзагрузка всех анимаций
        self._preload_animations()
    
    def _preload_animations(self):
        """Предзагружает все анимации в кэш"""
        animations = {
            'walk': (0, 4),      # столбцы 0-3 (4 кадра)
            'attack_melee': (4, 5),  # столбец 4 (1 кадр)
            'attack_ranged': (5, 6), # столбец 5 (1 кадр)
            'hurt': (6, 7),     # столбец 6 (1 кадр)
            'death': (7, 8),    # столбец 7 (1 кадр)
        }
        
        for direction in range(8):
            row = self.DIRECTION_MAP[direction]
            for anim_name, (start_col, end_col) in animations.items():
                # Персонаж
                char_frames = self.character_sheet.get_animation_frames(
                    row, start_col, end_col, self.scale
                )
                
                # Оружие (если есть)
                if self.weapon_sheet:
                    weapon_frames = self.weapon_sheet.get_animation_frames(
                        row, start_col, end_col, self.scale
                    )
                    # Объединяем спрайты персонажа и оружия
                    combined_frames = []
                    for char_frame, weapon_frame in zip(char_frames, weapon_frames):
                        combined = char_frame.copy()
                        combined.blit(weapon_frame, (0, 0))
                        combined_frames.append(combined)
                    self.animation_cache[(anim_name, direction)] = combined_frames
                else:
                    self.animation_cache[(anim_name, direction)] = char_frames
    
    def angle_to_direction(self, angle):
        """
        Конвертирует угол в индекс направления (0-7)
        
        Args:
            angle: Угол в радианах
            
        Returns:
            Индекс направления (0-7)
        """
        # Нормализуем угол в диапазон [0, 2π)
        angle = angle % (2 * math.pi)
        if angle < 0:
            angle += 2 * math.pi
        
        # Делим круг на 8 секторов по 45° каждый
        # Смещаем на 22.5° чтобы границы секторов были между направлениями
        sector = int((angle + math.pi / 8) / (math.pi / 4)) % 8
        
        return sector
    
    def get_frame(self, animation_name, direction, frame_index):
        """
        Получает конкретный кадр анимации
        
        Args:
            animation_name: Название анимации ('walk', 'attack_melee', etc.)
            direction: Индекс направления (0-7) или угол в радианах
            frame_index: Индекс кадра
            
        Returns:
            pygame.Surface
        """
        # Если direction - это угол, конвертируем
        if isinstance(direction, float):
            direction = self.angle_to_direction(direction)
        
        key = (animation_name, direction)
        if key not in self.animation_cache:
            # Fallback на направление 0
            key = (animation_name, 0)
        
        frames = self.animation_cache.get(key, [])
        if not frames:
            # Возвращаем пустую поверхность если нет кадров
            return pygame.Surface((self.frame_size, self.frame_size), pygame.SRCALPHA)
        
        return frames[frame_index % len(frames)]
    
    def get_animation_length(self, animation_name):
        """Возвращает количество кадров в анимации"""
        key = (animation_name, 0)
        return len(self.animation_cache.get(key, []))


class AnimationController:
    """Контроллер анимаций персонажа"""
    
    def __init__(self, sprites: CharacterSprites):
        """
        Args:
            sprites: Объект CharacterSprites
        """
        self.sprites = sprites
        
        # Текущее состояние
        self.current_animation = 'walk'
        self.current_frame = 0
        self.animation_time = 0.0
        self.direction = 0  # Индекс направления (0-7)
        
        # Скорости анимаций (кадров в секунду)
        self.animation_speeds = {
            'walk': 8,
            'attack_melee': 3,  # Замедленная анимация атаки
            'attack_ranged': 3,
            'hurt': 5,
            'death': 5,
        }
        
        # Флаг для одноразовых анимаций
        self.is_playing_once = False
        self.on_animation_complete = None
    
    def set_direction(self, angle):
        """Устанавливает направление по углу в радианах"""
        self.direction = self.sprites.angle_to_direction(angle)
    
    def play(self, animation_name, loop=True, on_complete=None):
        """
        Запускает анимацию
        
        Args:
            animation_name: Название анимации
            loop: Зацикливать ли анимацию
            on_complete: Callback при завершении (для одноразовых анимаций)
        """
        if self.current_animation != animation_name:
            self.current_animation = animation_name
            self.current_frame = 0
            self.animation_time = 0.0
        
        self.is_playing_once = not loop
        self.on_animation_complete = on_complete
    
    def update(self, dt):
        """Обновляет анимацию"""
        speed = self.animation_speeds.get(self.current_animation, 8)
        self.animation_time += dt * speed
        
        anim_length = self.sprites.get_animation_length(self.current_animation)
        if anim_length == 0:
            return
        
        # Переход к следующему кадру
        if self.animation_time >= 1.0:
            self.animation_time -= 1.0
            self.current_frame += 1
            
            # Проверка конца анимации
            if self.current_frame >= anim_length:
                if self.is_playing_once:
                    self.current_frame = anim_length - 1  # Остаёмся на последнем кадре
                    if self.on_animation_complete:
                        self.on_animation_complete()
                        self.on_animation_complete = None
                else:
                    self.current_frame = 0
    
    def get_current_frame(self):
        """Возвращает текущий кадр анимации"""
        return self.sprites.get_frame(
            self.current_animation,
            self.direction,
            self.current_frame
        )
    
    def get_frame_size(self):
        """Возвращает размер кадра"""
        return self.sprites.frame_size

