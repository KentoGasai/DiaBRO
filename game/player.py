"""
Класс персонажа
"""
import pygame
import math
import os
from game.stats import Stats, HealthBar, ManaBar
from game.sprites import CharacterSprites, AnimationController


class Player:
    """Класс игрового персонажа"""
    
    def __init__(self, x, y, speed=150.0, max_health=100, max_mana=100):
        """
        Args:
            x, y: Начальная позиция в мировых координатах
            speed: Скорость движения (пикселей в секунду)
            max_health: Максимальное здоровье
            max_mana: Максимальная мана
        """
        self.world_x = x
        self.world_y = y
        self.target_x = x
        self.target_y = y
        self.speed = speed
        
        # Статистика персонажа
        self.stats = Stats(max_health=max_health, max_mana=max_mana)
        self.health_bar = HealthBar(width=200, height=20)
        self.mana_bar = ManaBar(width=200, height=20)
        
        # Плавность движения
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.acceleration = 50.0  # Ускорение (адаптировано под низкую скорость)
        self.deceleration = 80.0  # Замедление
        self.max_speed = speed
        
        # Загрузка спрайтов
        self.use_sprites = False
        self.sprites = None
        self.animation = None
        self._load_sprites()
        
        # Fallback визуальное представление (если нет спрайтов)
        self.size = 24
        self.color = (100, 150, 255)
        self.robe_color = (50, 100, 200)
        
        # Анимация (для fallback)
        self.animation_time = 0.0
        self.walking = False
        self.animation_speed = 6.0
        
        # Направление взгляда
        self.angle = 0  # Угол движения (мировые координаты)
        self.sprite_angle = 0  # Угол спрайта (экранные координаты)
        
        # Неуязвимость после получения урона
        self.invincibility_time = 0.0
        self.invincibility_duration = 0.5
        self.damage_flash_time = 0.0
        
        # Состояние атаки
        self.is_attacking = False
        self.attack_sprite_angle = 0  # Сохранённый угол атаки
    
    def _load_sprites(self):
        """Загружает спрайты персонажа"""
        # Определяем путь к спрайтам (поддержка PyInstaller)
        import sys
        if getattr(sys, 'frozen', False):
            # Запуск из exe (PyInstaller)
            base_path = os.path.join(sys._MEIPASS, 'game', 'images')
        else:
            # Запуск из исходников
            base_path = os.path.join(os.path.dirname(__file__), 'images')
        
        character_path = os.path.join(base_path, 'character', 'male_unarmored.png')
        weapon_path = os.path.join(base_path, 'weapon', 'male_longsword.png')
        
        if os.path.exists(character_path):
            try:
                self.sprites = CharacterSprites(
                    character_path,
                    weapon_path if os.path.exists(weapon_path) else None,
                    scale=1.0  # Оригинальный размер 256x256
                )
                self.animation = AnimationController(self.sprites)
                self.use_sprites = True
                print("Спрайты персонажа загружены успешно!")
            except Exception as e:
                print(f"Ошибка загрузки спрайтов: {e}")
                self.use_sprites = False
        else:
            print(f"Спрайты не найдены: {character_path}")
    
    def update(self, dt, keyboard_input=None):
        """
        Обновляет позицию персонажа с плавным движением
        
        Args:
            dt: Delta time (время с последнего кадра)
            keyboard_input: Кортеж (x, y) от клавиатуры (WASD)
        """
        # Обновление неуязвимости
        if self.invincibility_time > 0:
            self.invincibility_time -= dt
        if self.damage_flash_time > 0:
            self.damage_flash_time -= dt
        
        target_velocity_x = 0.0
        target_velocity_y = 0.0
        
        # Управление клавиатурой (WASD)
        if keyboard_input:
            kx, ky = keyboard_input
            if kx != 0 or ky != 0:
                # Нормализация вектора
                length = math.sqrt(kx * kx + ky * ky)
                if length > 0:
                    dir_x = kx / length
                    dir_y = ky / length
                    target_velocity_x = dir_x * self.max_speed
                    target_velocity_y = dir_y * self.max_speed
                    
                    # Преобразуем мировое направление в экранное для спрайта
                    # Изометрия: screen_x = (world_x - world_y), screen_y = (world_x + world_y)
                    # В pygame Y растёт вниз, поэтому инвертируем screen_dir_y
                    screen_dir_x = kx - ky  # Экранное направление X
                    screen_dir_y = -(kx + ky)  # Экранное направление Y (инвертировано)
                    self.angle = math.atan2(screen_dir_y, screen_dir_x)
                    
                    self.walking = True
                else:
                    self.walking = False
            else:
                self.walking = False
        else:
            self.walking = False
        
        # Плавное изменение скорости (ускорение/замедление)
        if target_velocity_x != 0 or target_velocity_y != 0:
            accel = self.acceleration * dt
            dx = target_velocity_x - self.velocity_x
            dy = target_velocity_y - self.velocity_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > accel:
                self.velocity_x += (dx / distance) * accel
                self.velocity_y += (dy / distance) * accel
            else:
                self.velocity_x = target_velocity_x
                self.velocity_y = target_velocity_y
        else:
            decel = self.deceleration * dt
            current_speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
            
            if current_speed > decel:
                factor = (current_speed - decel) / current_speed
                self.velocity_x *= factor
                self.velocity_y *= factor
            else:
                self.velocity_x = 0
                self.velocity_y = 0
        
        # Ограничение максимальной скорости
        current_speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
        if current_speed > self.max_speed:
            factor = self.max_speed / current_speed
            self.velocity_x *= factor
            self.velocity_y *= factor
        
        # Применение движения
        self.world_x += self.velocity_x * dt
        self.world_y += self.velocity_y * dt
        
        # Обновление анимации спрайтов
        if self.use_sprites and self.animation:
            # Выбор угла спрайта: при атаке используем угол атаки, иначе угол движения
            if self.is_attacking:
                self.animation.set_direction(self.attack_sprite_angle)
                self.animation.update(dt)
            else:
                # При движении обновляем угол спрайта
                if self.walking:
                    self.sprite_angle = self.angle
                
                self.animation.set_direction(self.sprite_angle)
                
                if self.walking:
                    self.animation.play('walk')
                    self.animation.update(dt)
                else:
                    # Idle = первый кадр walk (без обновления анимации)
                    self.animation.current_animation = 'walk'
                    self.animation.current_frame = 0
                    self.animation.animation_time = 0.0
        else:
            # Fallback анимация
            if self.walking:
                self.animation_time += dt * self.animation_speed
            else:
                self.animation_time = 0
    
    def play_attack_animation(self, is_melee=True, target_world_x=None, target_world_y=None):
        """
        Запускает анимацию атаки
        
        Args:
            is_melee: Ближняя атака или дальняя
            target_world_x, target_world_y: Мировые координаты цели (для поворота спрайта)
        """
        if self.use_sprites and self.animation:
            # Поворот спрайта в направлении атаки
            if target_world_x is not None and target_world_y is not None:
                # Вычисляем мировое направление к цели
                world_dir_x = target_world_x - self.world_x
                world_dir_y = target_world_y - self.world_y
                
                # Преобразуем в экранное направление (как при движении)
                screen_dir_x = world_dir_x - world_dir_y
                screen_dir_y = -(world_dir_x + world_dir_y)
                
                # Сохраняем угол атаки (для использования во время атаки)
                if screen_dir_x != 0 or screen_dir_y != 0:
                    self.attack_sprite_angle = math.atan2(screen_dir_y, screen_dir_x)
            else:
                # Если нет цели, используем текущий угол спрайта
                self.attack_sprite_angle = self.sprite_angle
            
            self.is_attacking = True
            anim_name = 'attack_melee' if is_melee else 'attack_ranged'
            self.animation.play(anim_name, loop=False, 
                              on_complete=self._on_attack_complete)
    
    def _on_attack_complete(self):
        """Callback по завершению анимации атаки"""
        self.is_attacking = False
    
    def take_damage(self, damage):
        """
        Наносит урон игроку
        
        Args:
            damage: Количество урона
            
        Returns:
            True если игрок умер
        """
        if self.invincibility_time > 0:
            return False
        
        is_dead = self.stats.take_damage(damage)
        self.invincibility_time = self.invincibility_duration
        self.damage_flash_time = 0.15
        
        # Анимация получения урона
        if self.use_sprites and self.animation:
            self.animation.play('hurt', loop=False, 
                              on_complete=lambda: self.animation.play('walk'))
        
        return is_dead
    
    def is_dead(self):
        """Проверяет, мёртв ли игрок"""
        return self.stats.is_dead()
    
    def heal(self, amount):
        """Восстанавливает здоровье"""
        self.stats.heal(amount)
    
    def use_mana(self, amount):
        """Использует ману"""
        return self.stats.use_mana(amount)
    
    def restore_mana(self, amount):
        """Восстанавливает ману"""
        self.stats.restore_mana(amount)
    
    def get_position(self):
        """Возвращает позицию в мировых координатах"""
        return self.world_x, self.world_y
    
    def draw(self, screen, iso_converter, camera_offset=(0, 0)):
        """
        Отрисовывает персонажа
        
        Args:
            screen: Поверхность для отрисовки
            iso_converter: Конвертер изометрических координат
            camera_offset: Смещение камеры
        """
        # Преобразование в экранные координаты
        screen_x, screen_y = iso_converter.world_to_screen(
            self.world_x, self.world_y
        )
        screen_x += camera_offset[0]
        screen_y += camera_offset[1]
        
        # Эффект неуязвимости (мерцание)
        if self.invincibility_time > 0 and int(self.invincibility_time * 10) % 2 == 0:
            return  # Пропускаем отрисовку для мерцания
        
        if self.use_sprites and self.animation:
            self._draw_sprite(screen, screen_x, screen_y)
        else:
            self._draw_fallback(screen, screen_x, screen_y)
    
    def _draw_sprite(self, screen, screen_x, screen_y):
        """Отрисовывает спрайт персонажа"""
        frame = self.animation.get_current_frame()
        frame_size = self.animation.get_frame_size()
        
        # Центрируем спрайт на позиции персонажа
        # Смещаем вверх, чтобы "ноги" персонажа были на позиции
        draw_x = screen_x - frame_size // 2
        draw_y = screen_y - frame_size + frame_size // 4  # Смещение для изометрии
        
        # Эффект урона (красный оттенок)
        if self.damage_flash_time > 0:
            # Создаём копию с красным оттенком
            tinted = frame.copy()
            tinted.fill((255, 100, 100, 0), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(tinted, (draw_x, draw_y))
        else:
            screen.blit(frame, (draw_x, draw_y))
    
    def _draw_fallback(self, screen, screen_x, screen_y):
        """Отрисовывает fallback (если нет спрайтов)"""
        # Анимация покачивания при ходьбе
        anim_offset = 0
        if self.walking:
            anim_offset = math.sin(self.animation_time) * 2
        
        center_x = int(screen_x)
        center_y = int(screen_y + anim_offset)
        
        # Цвета
        if self.damage_flash_time > 0:
            robe_color = (255, 100, 100)
            head_color = (255, 180, 180)
        else:
            robe_color = self.robe_color
            head_color = (255, 220, 180)
        
        # Тело (мантия)
        body_rect = pygame.Rect(
            center_x - self.size // 2,
            center_y - self.size // 2 + 4,
            self.size,
            self.size - 4
        )
        pygame.draw.ellipse(screen, robe_color, body_rect)
        
        # Голова
        head_radius = self.size // 3
        pygame.draw.circle(screen, head_color, (center_x, center_y - self.size // 3), head_radius)
        
        # Шляпа
        hat_points = [
            (center_x, center_y - self.size // 2 - 8),
            (center_x - head_radius, center_y - self.size // 3),
            (center_x + head_radius, center_y - self.size // 3)
        ]
        pygame.draw.polygon(screen, (50, 50, 50), hat_points)
        
        # Посох
        staff_length = self.size + 8
        staff_end_x = center_x + math.cos(self.angle) * staff_length
        staff_end_y = center_y + math.sin(self.angle) * staff_length
        pygame.draw.line(screen, (139, 69, 19), (center_x, center_y), 
                        (staff_end_x, staff_end_y), 3)
        
        # Кристалл
        pygame.draw.circle(screen, (150, 200, 255), 
                          (int(staff_end_x), int(staff_end_y)), 4)
    
    def draw_ui(self, screen, x, y):
        """
        Отрисовывает UI игрока (HP и Mana бары)
        
        Args:
            screen: Поверхность для отрисовки
            x, y: Позиция для отрисовки
        """
        self.health_bar.draw(screen, x, y, self.stats)
        self.mana_bar.draw(screen, x, y + 25, self.stats)
