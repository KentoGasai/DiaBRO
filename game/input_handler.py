"""
Обработчик ввода (мышь, клавиатура, геймпад)
"""
import pygame


class InputHandler:
    """Класс для обработки всех видов ввода"""
    
    def __init__(self):
        self.mouse_pos = (0, 0)
        self.mouse_buttons = {
            'left': False,
            'right': False,
            'middle': False
        }
        self.mouse_buttons_pressed = {
            'left': False,
            'right': False,
            'middle': False
        }
        
        self.keys_pressed = {}
        self.keys_just_pressed = {}
        
        # Инициализация геймпада
        self.joysticks = []
        self.gamepad_connected = False
        self.gamepad_left_stick = (0.0, 0.0)
        self.gamepad_buttons = {}
        self.gamepad_buttons_pressed = {}
        
        self._init_gamepad()
    
    def _init_gamepad(self):
        """Инициализация геймпадов"""
        pygame.joystick.init()
        joystick_count = pygame.joystick.get_count()
        
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)
            self.gamepad_connected = True
            print(f"Геймпад подключен: {joystick.get_name()}")
    
    def update(self, events):
        """
        Обновляет состояние ввода
        
        Args:
            events: Список событий pygame
        """
        # Сброс состояний "только что нажато"
        self.mouse_buttons_pressed = {
            'left': False,
            'right': False,
            'middle': False
        }
        self.keys_just_pressed = {}
        self.gamepad_buttons_pressed = {}
        
        # Обработка событий
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка
                    self.mouse_buttons['left'] = True
                    self.mouse_buttons_pressed['left'] = True
                elif event.button == 2:  # Средняя кнопка
                    self.mouse_buttons['middle'] = True
                    self.mouse_buttons_pressed['middle'] = True
                elif event.button == 3:  # Правая кнопка
                    self.mouse_buttons['right'] = True
                    self.mouse_buttons_pressed['right'] = True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_buttons['left'] = False
                elif event.button == 2:
                    self.mouse_buttons['middle'] = False
                elif event.button == 3:
                    self.mouse_buttons['right'] = False
            
            elif event.type == pygame.KEYDOWN:
                self.keys_pressed[event.key] = True
                self.keys_just_pressed[event.key] = True
            
            elif event.type == pygame.KEYUP:
                self.keys_pressed[event.key] = False
            
            elif event.type == pygame.JOYBUTTONDOWN:
                self.gamepad_buttons[event.button] = True
                self.gamepad_buttons_pressed[event.button] = True
            
            elif event.type == pygame.JOYBUTTONUP:
                self.gamepad_buttons[event.button] = False
            
            elif event.type == pygame.JOYAXISMOTION:
                # Левый стик (обычно оси 0 и 1)
                if event.axis == 0:  # Горизонталь
                    self.gamepad_left_stick = (
                        event.value,
                        self.gamepad_left_stick[1]
                    )
                elif event.axis == 1:  # Вертикаль
                    self.gamepad_left_stick = (
                        self.gamepad_left_stick[0],
                        event.value
                    )
        
        # Обновление состояния клавиш (для проверки удержания)
        keys = pygame.key.get_pressed()
        for key in self.keys_pressed:
            if key not in keys:
                self.keys_pressed[key] = False
    
    def is_mouse_button_pressed(self, button='left'):
        """Проверяет, нажата ли кнопка мыши"""
        return self.mouse_buttons.get(button, False)
    
    def is_mouse_button_just_pressed(self, button='left'):
        """Проверяет, только что нажата ли кнопка мыши"""
        return self.mouse_buttons_pressed.get(button, False)
    
    def get_mouse_pos(self):
        """Возвращает позицию мыши"""
        return self.mouse_pos
    
    def is_key_pressed(self, key):
        """Проверяет, нажата ли клавиша"""
        # Используем pygame.key.get_pressed() для актуального состояния
        keys = pygame.key.get_pressed()
        return keys[key] if key < len(keys) else False
    
    def is_key_just_pressed(self, key):
        """Проверяет, только что нажата ли клавиша"""
        return self.keys_just_pressed.get(key, False)
    
    def get_gamepad_stick(self):
        """Возвращает позицию левого стика геймпада (x, y)"""
        return self.gamepad_left_stick
    
    def is_gamepad_button_pressed(self, button):
        """
        Проверяет, нажата ли кнопка геймпада
        
        Args:
            button: Номер кнопки (0 = квадрат на PS контроллере)
        """
        return self.gamepad_buttons.get(button, False)
    
    def is_gamepad_button_just_pressed(self, button):
        """Проверяет, только что нажата ли кнопка геймпада"""
        return self.gamepad_buttons_pressed.get(button, False)
    
    def is_gamepad_connected(self):
        """Проверяет, подключен ли геймпад"""
        return self.gamepad_connected

