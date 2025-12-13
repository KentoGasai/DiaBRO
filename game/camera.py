"""
Система камеры
"""
import pygame


class Camera:
    """Класс камеры для следования за персонажем"""
    
    def __init__(self, screen_width, screen_height):
        """
        Args:
            screen_width: Ширина экрана
            screen_height: Высота экрана
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        
        # Плавность следования
        self.follow_speed = 0.1
    
    def update(self, target_world_x, target_world_y, iso_converter):
        """
        Обновляет позицию камеры
        
        Args:
            target_world_x, target_world_y: Целевая позиция в мировых координатах
            iso_converter: Конвертер изометрических координат
        """
        # Преобразуем целевую позицию в экранные координаты
        target_screen_x, target_screen_y = iso_converter.world_to_screen(
            target_world_x, target_world_y
        )
        
        # Центрируем камеру на цели
        self.target_x = self.screen_width // 2 - target_screen_x
        self.target_y = self.screen_height // 2 - target_screen_y
        
        # Плавное следование
        self.x += (self.target_x - self.x) * self.follow_speed
        self.y += (self.target_y - self.y) * self.follow_speed
    
    def get_offset(self):
        """Возвращает смещение камеры"""
        return (int(self.x), int(self.y))
    
    def world_to_screen(self, world_x, world_y, iso_converter):
        """
        Преобразует мировые координаты в экранные с учетом камеры
        
        Args:
            world_x, world_y: Мировые координаты
            iso_converter: Конвертер изометрических координат
            
        Returns:
            tuple: (screen_x, screen_y)
        """
        screen_x, screen_y = iso_converter.world_to_screen(world_x, world_y)
        offset = self.get_offset()
        return screen_x + offset[0], screen_y + offset[1]
    
    def screen_to_world(self, screen_x, screen_y, iso_converter):
        """
        Преобразует экранные координаты в мировые с учетом камеры
        
        Args:
            screen_x, screen_y: Экранные координаты
            iso_converter: Конвертер изометрических координат
            
        Returns:
            tuple: (world_x, world_y)
        """
        offset = self.get_offset()
        adjusted_x = screen_x - offset[0]
        adjusted_y = screen_y - offset[1]
        return iso_converter.screen_to_world(adjusted_x, adjusted_y)

