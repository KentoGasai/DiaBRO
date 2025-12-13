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


class AnimatedSprite:
    """
    Универсальный компонент анимации для передвигающихся объектов.
    
    Можно подключить к любому объекту (враг, NPC, снаряд и т.д.) для добавления
    спрайтовой анимации с 8 направлениями.
    
    Использование:
        # Создание
        animated = AnimatedSprite(
            sprite_path='game/images/enemy/skeleton.png',
            weapon_path=None,  # Опционально
            scale=0.5
        )
        
        # В методе update объекта:
        if animated.is_loaded():
            animated.set_direction(self.angle)
            animated.update(dt, is_walking=is_moving)
        
        # В методе draw:
        if animated.is_loaded():
            animated.draw(screen, screen_x, screen_y)
    """
    
    def __init__(self, sprite_path, weapon_path=None, scale=0.25, 
                 animation_speeds=None, vertical_offset=0.25):
        """
        Args:
            sprite_path: Путь к спрайтшиту
            weapon_path: Путь к спрайтшиту оружия (опционально)
            scale: Масштаб спрайтов (256px * scale)
            animation_speeds: Словарь скоростей анимаций (опционально)
            vertical_offset: Вертикальное смещение для позиционирования (доля от размера кадра)
        """
        self.sprites = None
        self.animation = None
        self.loaded = False
        self.vertical_offset = vertical_offset
        
        # Текущее состояние
        self.current_state = 'idle'  # idle, walk, attack, hurt, death
        self.is_walking = False
        self.is_attacking = False
        self.is_hurt = False
        self.is_dying = False
        
        # Попытка загрузки спрайтов
        self._load_sprites(sprite_path, weapon_path, scale, animation_speeds)
    
    def _load_sprites(self, sprite_path, weapon_path, scale, animation_speeds):
        """Загружает спрайты"""
        import sys
        
        # Определяем путь (поддержка PyInstaller)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))
        
        # Если путь относительный, добавляем base_path
        if not os.path.isabs(sprite_path):
            full_sprite_path = os.path.join(base_path, sprite_path)
        else:
            full_sprite_path = sprite_path
        
        full_weapon_path = None
        if weapon_path:
            if not os.path.isabs(weapon_path):
                full_weapon_path = os.path.join(base_path, weapon_path)
            else:
                full_weapon_path = weapon_path
        
        if os.path.exists(full_sprite_path):
            try:
                self.sprites = CharacterSprites(
                    full_sprite_path,
                    full_weapon_path if full_weapon_path and os.path.exists(full_weapon_path) else None,
                    scale=scale
                )
                self.animation = AnimationController(self.sprites)
                
                # Кастомные скорости анимаций
                if animation_speeds:
                    self.animation.animation_speeds.update(animation_speeds)
                
                self.loaded = True
            except Exception as e:
                print(f"Ошибка загрузки спрайтов {full_sprite_path}: {e}")
                self.loaded = False
        else:
            print(f"Спрайты не найдены: {full_sprite_path}")
            self.loaded = False
    
    def is_loaded(self):
        """Проверяет, загружены ли спрайты"""
        return self.loaded
    
    def set_direction(self, angle):
        """
        Устанавливает направление спрайта
        
        Args:
            angle: Угол в радианах
        """
        if self.animation:
            self.animation.set_direction(angle)
    
    def update(self, dt, is_walking=False):
        """
        Обновляет анимацию
        
        Args:
            dt: Delta time
            is_walking: Флаг движения
        """
        if not self.loaded:
            return
        
        self.is_walking = is_walking
        
        # Приоритет анимаций: death > hurt > attack > walk > idle
        if self.is_dying:
            # Анимация смерти уже запущена
            self.animation.update(dt)
        elif self.is_hurt:
            self.animation.update(dt)
        elif self.is_attacking:
            self.animation.update(dt)
        elif self.is_walking:
            self.animation.play('walk')
            self.animation.update(dt)
        else:
            # Idle = первый кадр walk
            self.animation.current_animation = 'walk'
            self.animation.current_frame = 0
            self.animation.animation_time = 0.0
    
    def play_attack(self, is_melee=True, on_complete=None):
        """
        Запускает анимацию атаки
        
        Args:
            is_melee: Ближняя атака (True) или дальняя (False)
            on_complete: Callback по завершению
        """
        if not self.loaded:
            return
        
        self.is_attacking = True
        anim_name = 'attack_melee' if is_melee else 'attack_ranged'
        
        def complete_callback():
            self.is_attacking = False
            if on_complete:
                on_complete()
        
        self.animation.play(anim_name, loop=False, on_complete=complete_callback)
    
    def play_hurt(self, on_complete=None):
        """
        Запускает анимацию получения урона
        
        Args:
            on_complete: Callback по завершению
        """
        if not self.loaded:
            return
        
        self.is_hurt = True
        
        def complete_callback():
            self.is_hurt = False
            if on_complete:
                on_complete()
        
        self.animation.play('hurt', loop=False, on_complete=complete_callback)
    
    def play_death(self, on_complete=None):
        """
        Запускает анимацию смерти
        
        Args:
            on_complete: Callback по завершению
        """
        if not self.loaded:
            return
        
        self.is_dying = True
        self.animation.play('death', loop=False, on_complete=on_complete)
    
    def get_frame_size(self):
        """Возвращает размер кадра"""
        if self.animation:
            return self.animation.get_frame_size()
        return 64  # Значение по умолчанию
    
    def draw(self, screen, screen_x, screen_y, alpha=255, tint_color=None):
        """
        Отрисовывает спрайт
        
        Args:
            screen: Поверхность для отрисовки
            screen_x, screen_y: Экранные координаты центра объекта
            alpha: Прозрачность (0-255)
            tint_color: Цвет оттенка (R, G, B) или None
        """
        if not self.loaded:
            return
        
        frame = self.animation.get_current_frame()
        frame_size = self.animation.get_frame_size()
        
        # Центрируем спрайт, с учётом вертикального смещения
        draw_x = screen_x - frame_size // 2
        draw_y = screen_y - frame_size + int(frame_size * self.vertical_offset)
        
        # Применяем эффекты
        if alpha < 255 or tint_color:
            frame = frame.copy()
            
            # Прозрачность
            if alpha < 255:
                frame.set_alpha(alpha)
            
            # Оттенок (например, красный при уроне)
            if tint_color:
                frame.fill((*tint_color, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        screen.blit(frame, (draw_x, draw_y))
    
    def reset(self):
        """Сбрасывает состояние анимации"""
        self.is_walking = False
        self.is_attacking = False
        self.is_hurt = False
        self.is_dying = False
        self.current_state = 'idle'
        
        if self.animation:
            self.animation.current_animation = 'walk'
            self.animation.current_frame = 0
            self.animation.animation_time = 0.0
