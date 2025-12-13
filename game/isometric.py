"""
Изометрические преобразования координат
"""
import math


class IsometricConverter:
    """Класс для преобразования между изометрическими и экранными координатами"""
    
    def __init__(self, tile_width=64, tile_height=32):
        """
        Args:
            tile_width: Ширина тайла в изометрической проекции
            tile_height: Высота тайла в изометрической проекции
        """
        self.tile_width = tile_width
        self.tile_height = tile_height
        
        # Угол изометрической проекции (обычно 30 градусов)
        self.angle = math.radians(30)
        self.cos_angle = math.cos(self.angle)
        self.sin_angle = math.sin(self.angle)
    
    def world_to_screen(self, x, y):
        """
        Преобразует мировые координаты в экранные (изометрические)
        
        Args:
            x, y: Мировые координаты (логические)
            
        Returns:
            tuple: (screen_x, screen_y) - экранные координаты
        """
        # Изометрическое преобразование
        screen_x = (x - y) * (self.tile_width / 2)
        screen_y = (x + y) * (self.tile_height / 2)
        return int(screen_x), int(screen_y)
    
    def screen_to_world(self, screen_x, screen_y):
        """
        Преобразует экранные координаты в мировые
        
        Args:
            screen_x, screen_y: Экранные координаты
            
        Returns:
            tuple: (world_x, world_y) - мировые координаты
        """
        # Обратное изометрическое преобразование
        world_x = (screen_x / (self.tile_width / 2) + screen_y / (self.tile_height / 2)) / 2
        world_y = (screen_y / (self.tile_height / 2) - screen_x / (self.tile_width / 2)) / 2
        return world_x, world_y
    
    def get_tile_size(self):
        """Возвращает размер тайла"""
        return self.tile_width, self.tile_height

