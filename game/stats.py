"""
Система характеристик персонажа (HP, Mana)
"""
import pygame


class Stats:
    """Класс для управления характеристиками"""
    
    def __init__(self, max_health=100, max_mana=100):
        """
        Args:
            max_health: Максимальное здоровье
            max_mana: Максимальная мана
        """
        self.max_health = max_health
        self.max_mana = max_mana
        self.health = max_health
        self.mana = max_mana
    
    def take_damage(self, damage):
        """Наносит урон"""
        self.health = max(0, self.health - damage)
        return self.health <= 0
    
    def heal(self, amount):
        """Восстанавливает здоровье"""
        self.health = min(self.max_health, self.health + amount)
    
    def use_mana(self, amount):
        """Использует ману"""
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False
    
    def restore_mana(self, amount):
        """Восстанавливает ману"""
        self.mana = min(self.max_mana, self.mana + amount)
    
    def get_health_percent(self):
        """Возвращает процент здоровья"""
        return self.health / self.max_health if self.max_health > 0 else 0
    
    def get_mana_percent(self):
        """Возвращает процент маны"""
        return self.mana / self.max_mana if self.max_mana > 0 else 0
    
    def is_dead(self):
        """Проверяет, мёртв ли персонаж"""
        return self.health <= 0


class StatusBar:
    """Базовый класс для отрисовки статус-баров"""
    
    # Кэш шрифтов для производительности
    _font_cache = {}
    
    def __init__(self, width=100, height=10, bar_color=(0, 200, 0), 
                 bg_color=(50, 50, 50), border_color=(255, 255, 255)):
        """
        Args:
            width: Ширина бара
            height: Высота бара
            bar_color: Цвет заполнения
            bg_color: Цвет фона
            border_color: Цвет рамки
        """
        self.width = width
        self.height = height
        self.bar_color = bar_color
        self.bg_color = bg_color
        self.border_color = border_color
    
    @classmethod
    def get_font(cls, size):
        """Возвращает кэшированный шрифт"""
        if size not in cls._font_cache:
            cls._font_cache[size] = pygame.font.Font(None, size)
        return cls._font_cache[size]
    
    def draw(self, screen, x, y, current_value, max_value, show_text=True):
        """
        Отрисовывает статус-бар
        
        Args:
            screen: Поверхность для отрисовки
            x, y: Позиция бара
            current_value: Текущее значение
            max_value: Максимальное значение
            show_text: Показывать ли текст
        """
        # Фон бара
        bg_rect = pygame.Rect(x, y, self.width, self.height)
        pygame.draw.rect(screen, self.bg_color, bg_rect)
        
        # Заполнение
        percent = current_value / max_value if max_value > 0 else 0
        fill_width = int(self.width * percent)
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y, fill_width, self.height)
            pygame.draw.rect(screen, self.bar_color, fill_rect)
        
        # Рамка
        pygame.draw.rect(screen, self.border_color, bg_rect, 1)
        
        # Текст
        if show_text:
            font = self.get_font(16)
            text = f"{int(current_value)}/{int(max_value)}"
            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(x + self.width // 2, y + self.height // 2))
            screen.blit(text_surface, text_rect)


class HealthBar(StatusBar):
    """Класс для отрисовки Health Bar"""
    
    def __init__(self, width=100, height=10):
        super().__init__(width, height, bar_color=(0, 200, 0))
        self.enemy_color = (200, 0, 0)
    
    def draw(self, screen, x, y, stats, is_enemy=False):
        """
        Отрисовывает Health Bar
        
        Args:
            screen: Поверхность для отрисовки
            x, y: Позиция бара
            stats: Объект Stats
            is_enemy: Если True, использует красный цвет для врагов
        """
        # Временно меняем цвет для врагов
        original_color = self.bar_color
        if is_enemy:
            self.bar_color = self.enemy_color
        
        super().draw(screen, x, y, stats.health, stats.max_health)
        
        # Восстанавливаем цвет
        self.bar_color = original_color


class ManaBar(StatusBar):
    """Класс для отрисовки Mana Bar"""
    
    def __init__(self, width=100, height=10):
        super().__init__(width, height, bar_color=(0, 100, 255))
    
    def draw(self, screen, x, y, stats):
        """
        Отрисовывает Mana Bar
        
        Args:
            screen: Поверхность для отрисовки
            x, y: Позиция бара
            stats: Объект Stats
        """
        super().draw(screen, x, y, stats.mana, stats.max_mana)
