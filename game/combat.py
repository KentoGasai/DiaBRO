"""
Система боя и атак
"""
import pygame
import math
import time
import random


class Attack:
    """Класс для представления атаки"""
    
    def __init__(self, x, y, angle, damage=10, range=100, speed=300, is_melee=False):
        """
        Args:
            x, y: Позиция начала атаки
            angle: Угол направления атаки
            damage: Урон
            range: Дальность атаки
            speed: Скорость атаки (пикселей в секунду)
            is_melee: Если True, это ближняя атака
        """
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.range = range
        self.speed = speed
        self.distance_traveled = 0
        self.active = True
        self.start_time = time.time()
        self.is_melee = is_melee
        self.hit_enemies = []  # Список врагов, по которым уже нанесен урон
        self.lifetime = 0.35 if is_melee else float('inf')  # Время жизни для ближней атаки
        self.age = 0.0
    
    def update(self, dt):
        """Обновляет позицию атаки"""
        if not self.active:
            return
        
        self.age += dt
        
        # Для ближнего боя - проверка времени жизни
        if self.is_melee:
            if self.age >= self.lifetime:
                self.active = False
            return
        
        # Движение атаки (только для дальних атак)
        move_distance = self.speed * dt
        self.x += math.cos(self.angle) * move_distance
        self.y += math.sin(self.angle) * move_distance
        self.distance_traveled += move_distance
        
        # Проверка дальности (только если прошло достаточно времени, чтобы избежать мгновенного удаления)
        # Увеличиваем задержку, чтобы атака успела отрисоваться
        if self.age > 0.05:  # Увеличенная задержка перед проверкой дальности
            distance_from_start = math.sqrt(
                (self.x - self.start_x) ** 2 + (self.y - self.start_y) ** 2
            )
            
            if distance_from_start >= self.range:
                self.active = False
    
    def draw(self, screen, iso_converter, camera_offset):
        """Отрисовывает атаку"""
        if not self.active:
            return
        
        if self.is_melee:
            # Ближняя атака - круговая волна от игрока
            screen_x, screen_y = iso_converter.world_to_screen(self.start_x, self.start_y)
            screen_x += camera_offset[0]
            screen_y += camera_offset[1]
            
            # Прогресс анимации (0 -> 1)
            progress = self.age / self.lifetime
            
            # Конвертируем радиус из мировых в экранные координаты
            # self.range содержит melee_range в мировых единицах
            # В изометрии: 1 мировая единица ≈ 35 экранных пикселей
            max_visual_radius = int(self.range * 35)
            current_radius = int(max_visual_radius * progress)
            
            # Толщина и прозрачность уменьшаются
            alpha = int(200 * (1 - progress))
            line_width = max(1, int(4 * (1 - progress)))
            
            # Круговая волна
            if current_radius > 0:
                wave_surface = pygame.Surface((current_radius * 2 + 10, current_radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(wave_surface, (255, 255, 100, alpha), 
                                 (current_radius + 5, current_radius + 5), current_radius, line_width)
                screen.blit(wave_surface, (screen_x - current_radius - 5, screen_y - current_radius - 5))
            
            # Дуга в направлении атаки
            arc_length = max_visual_radius * 0.8
            end_x = screen_x + math.cos(self.angle) * arc_length * (1 - progress * 0.5)
            end_y = screen_y + math.sin(self.angle) * arc_length * (1 - progress * 0.5)
            
            pygame.draw.line(screen, (255, 255, 150), 
                           (int(screen_x), int(screen_y)), 
                           (int(end_x), int(end_y)), max(2, int(5 * (1 - progress))))
        else:
            # Дальняя атака - отрисовываем от текущей позиции
            screen_x, screen_y = iso_converter.world_to_screen(self.x, self.y)
            screen_x += camera_offset[0]
            screen_y += camera_offset[1]
            
            # Дальняя атака - огненный снаряд
            # Анимация пламени (пульсация)
            flame_pulse = math.sin(self.age * 15) * 1.5
            base_flame_size = 8
            flame_size = int(base_flame_size + flame_pulse)
            
            # Внешнее пламя (темно-оранжевое/красное)
            pygame.draw.circle(screen, (200, 50, 0), (int(screen_x), int(screen_y)), flame_size + 2)
            # Среднее пламя (оранжевое)
            pygame.draw.circle(screen, (255, 100, 0), (int(screen_x), int(screen_y)), flame_size)
            # Внутреннее пламя (желтое)
            pygame.draw.circle(screen, (255, 200, 0), (int(screen_x), int(screen_y)), flame_size - 2)
            # Ядро пламени (белое/желтое)
            pygame.draw.circle(screen, (255, 255, 200), (int(screen_x), int(screen_y)), flame_size - 4)
            
            # Искры вокруг (используем время для анимации)
            # Используем детерминированную случайность на основе позиции и времени
            spark_seed = int((self.x + self.y + self.age * 10) * 100) % 1000
            for i in range(4):
                # Простая псевдослучайность для искр
                spark_offset_x = ((spark_seed + i * 137) % (flame_size * 2)) - flame_size
                spark_offset_y = ((spark_seed + i * 241) % (flame_size * 2)) - flame_size
                spark_x = screen_x + spark_offset_x
                spark_y = screen_y + spark_offset_y
                # Искры разного размера
                spark_size = 2 if i % 2 == 0 else 1
                pygame.draw.circle(screen, (255, 255, 100), (int(spark_x), int(spark_y)), spark_size)
            
            # Хвост пламени (в направлении движения)
            tail_length = 6
            tail_start_x = screen_x - math.cos(self.angle) * tail_length
            tail_start_y = screen_y - math.sin(self.angle) * tail_length
            # Градиент хвоста
            for i in range(3):
                tail_x = screen_x - math.cos(self.angle) * (tail_length * (i + 1) / 3)
                tail_y = screen_y - math.sin(self.angle) * (tail_length * (i + 1) / 3)
                tail_alpha = 150 - i * 50
                tail_color = (255, 150 - i * 30, 0)
                pygame.draw.circle(screen, tail_color, (int(tail_x), int(tail_y)), flame_size - i * 2)


class CombatSystem:
    """Система управления боем"""
    
    def __init__(self):
        self.attacks = []
        self.attack_cooldown = 0.0
        self.attack_cooldown_time = 0.3  # 0.3 секунды между атаками
        self.is_melee_mode = False  # Режим ближнего боя
    
    def update(self, dt):
        """Обновляет все атаки"""
        # Обновление кулдауна
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        # Обновление атак
        for attack in self.attacks[:]:
            if attack.active:
                attack.update(dt)
            # Удаляем неактивные атаки (после обновления или изначально неактивные)
            if not attack.active:
                self.attacks.remove(attack)
    
    def perform_attack(self, player_x, player_y, player_angle, target_x=None, target_y=None, enemies=None):
        """
        Выполняет атаку
        
        Args:
            player_x, player_y: Позиция игрока
            player_angle: Угол направления игрока
            target_x, target_y: Целевая позиция (опционально, для направленных атак)
            enemies: Список врагов для мгновенной проверки ближнего боя
        """
        if self.attack_cooldown > 0:
            return False
        
        # Определяем угол атаки
        if target_x is not None and target_y is not None:
            dx = target_x - player_x
            dy = target_y - player_y
            angle = math.atan2(dy, dx)
        else:
            angle = player_angle
        
        # Создаем атаку в зависимости от режима
        if self.is_melee_mode:
            # Ближний бой: урон 5-9 HP, мгновенная атака в области
            damage = random.randint(5, 9)
            
            # Радиус ближней атаки (в мировых координатах)
            # 1.5 мировых единиц ≈ 50 экранных пикселей в изометрии
            melee_range = 1.5
            
            # Создаем атаку для визуализации
            attack = Attack(player_x, player_y, angle, 
                          damage=damage, range=melee_range, speed=0, is_melee=True)
            attack.start_x = player_x
            attack.start_y = player_y
            
            # Проверяем попадания и наносим урон всем врагам в радиусе
            if enemies:
                for enemy in enemies:
                    if enemy.is_dead or enemy.dying:
                        continue
                    
                    ex, ey = enemy.get_position()
                    dx = player_x - ex
                    dy = player_y - ey
                    distance_from_player = math.sqrt(dx * dx + dy * dy)
                    
                    if distance_from_player <= melee_range:
                        enemy.take_damage(damage)
                        attack.hit_enemies.append(enemy)
        else:
            # Дальний бой: урон 1-5 HP, дальняя дистанция
            damage = random.randint(1, 5)
            # Создаем атаку от позиции игрока в направлении курсора
            # range и speed в мировых координатах (1 мировая ≈ 35 экранных)
            attack = Attack(player_x, player_y, angle, 
                          damage=damage, range=8, speed=12, is_melee=False)
            # Убеждаемся, что начальная позиция правильная и атака активна
            attack.x = player_x
            attack.y = player_y
            attack.start_x = player_x
            attack.start_y = player_y
            attack.active = True  # Явно устанавливаем активность
        
        # Всегда добавляем атаку в список (для дальнего боя всегда создается)
        self.attacks.append(attack)
        self.attack_cooldown = self.attack_cooldown_time
        
        return True
    
    def set_melee_mode(self, is_melee):
        """Переключает режим ближнего/дальнего боя"""
        self.is_melee_mode = is_melee
    
    def check_hits(self, enemies):
        """
        Проверяет попадания атак по врагам (только для дальних атак)
        
        Args:
            enemies: Список врагов
            
        Returns:
            Список кортежей (attack, enemy) для попаданий
        """
        hits = []
        for attack in self.attacks:
            if not attack.active:
                continue
            
            # Пропускаем ближние атаки - урон для них уже нанесен в perform_attack
            if attack.is_melee:
                continue
            
            # Проверяем попадания только если атака пролетела минимальное расстояние
            # Это предотвращает попадание сразу после создания (когда игрок рядом с врагом)
            distance_from_start = math.sqrt(
                (attack.x - attack.start_x) ** 2 + (attack.y - attack.start_y) ** 2
            )
            min_distance_before_hit = 0.5  # Минимальное расстояние перед проверкой попадания (мировые)
            
            if distance_from_start < min_distance_before_hit:
                continue  # Пропускаем проверку попадания, если атака слишком близко к началу
            
            for enemy in enemies:
                if enemy.is_dead or enemy in attack.hit_enemies:
                    continue
                
                # Проверка попадания для дальних атак - используем хитбокс врага
                ex, ey = enemy.get_position()
                dx = attack.x - ex
                dy = attack.y - ey
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Хитбокс для дальней атаки (в мировых координатах)
                # hover_radius = 1.0 мировых, хитбокс должен быть сопоставим
                enemy_hitbox_radius = 0.5  # Радиус хитбокса врага (~18 экранных)
                projectile_hitbox_radius = 0.3  # Радиус хитбокса снаряда (~10 экранных)
                hit_radius = enemy_hitbox_radius + projectile_hitbox_radius  # ~0.8 мировых
                
                if distance <= hit_radius:
                    attack.hit_enemies.append(enemy)
                    hits.append((attack, enemy))
                    attack.active = False  # Атака исчезает после попадания
                    break
        
        return hits
    
    def draw(self, screen, iso_converter, camera_offset):
        """Отрисовывает все активные атаки"""
        for attack in self.attacks:
            if attack.active:
                attack.draw(screen, iso_converter, camera_offset)
    
    def get_attacks(self):
        """Возвращает список активных атак"""
        return self.attacks

