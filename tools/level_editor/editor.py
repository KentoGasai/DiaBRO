"""
DiaBRO Level Editor - Изометрический редактор уровней
"""

import pygame
import json
import os
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Константы
TILE_WIDTH = 128
TILE_HEIGHT = 64
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900

# Размер сетки уровня
GRID_WIDTH = 20
GRID_HEIGHT = 20

# Цвета
COLOR_BG = (30, 35, 45)
COLOR_GRID = (60, 70, 90)
COLOR_GRID_HOVER = (100, 150, 255)
COLOR_PANEL_BG = (40, 45, 55)
COLOR_TEXT = (220, 220, 220)
COLOR_TEXT_DIM = (140, 140, 140)
COLOR_BUTTON = (70, 80, 100)
COLOR_BUTTON_HOVER = (90, 100, 130)
COLOR_ACCENT = (88, 166, 255)


class TileSheet:
    """Класс для работы со спрайтшитом тайлов"""
    
    def __init__(self, path, tile_width=TILE_WIDTH, tile_height=TILE_HEIGHT):
        self.path = path
        self.name = Path(path).stem
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.image = pygame.image.load(path).convert_alpha()
        self.sheet_width = self.image.get_width()
        self.sheet_height = self.image.get_height()
        
        # Вычисляем количество тайлов
        self.cols = self.sheet_width // tile_width
        self.rows = self.sheet_height // tile_height
        self.tile_count = self.cols * self.rows
        
        # Кэш тайлов
        self.tiles = []
        self._extract_tiles()
    
    def _extract_tiles(self):
        """Извлекает все тайлы из спрайтшита"""
        for row in range(self.rows):
            for col in range(self.cols):
                rect = pygame.Rect(
                    col * self.tile_width,
                    row * self.tile_height,
                    self.tile_width,
                    self.tile_height
                )
                tile = self.image.subsurface(rect).copy()
                self.tiles.append(tile)
    
    def get_tile(self, index):
        """Возвращает тайл по индексу"""
        if 0 <= index < len(self.tiles):
            return self.tiles[index]
        return None


class LevelEditor:
    """Главный класс редактора уровней"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("DiaBRO Level Editor")
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Шрифты
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        self.font_large = pygame.font.Font(None, 32)
        
        # Загрузка тайлсетов
        self.tilesets = []
        self.current_tileset_index = 0
        self.current_tile_index = 0
        self._load_tilesets()
        
        # Данные уровня
        self.level_data = {}  # {(x, y): {'tileset': name, 'tile': index}}
        self.level_name = "new_level"
        
        # Камера
        self.camera_x = SCREEN_WIDTH // 2 - 200
        self.camera_y = 100
        self.camera_zoom = 1.0  # Масштаб камеры
        self.dragging = False
        self.drag_start = (0, 0)
        self.camera_start = (0, 0)
        
        # Hover
        self.hover_tile = None
        
        # UI
        self.panel_width = 300
        self.tile_selector_scroll = 0
        
        # Режимы
        self.show_grid = True
        self.eraser_mode = False
        
        # Рисование при зажатой кнопке
        self.mouse_drawing = False
        self.mouse_erasing = False
    
    def _load_tilesets(self):
        """Загружает все тайлсеты из папки textures"""
        textures_path = Path(__file__).parent.parent.parent / "game" / "images" / "textures"
        
        if textures_path.exists():
            for file in sorted(textures_path.glob("*.png")):
                try:
                    tileset = TileSheet(str(file))
                    self.tilesets.append(tileset)
                    print(f"Loaded: {file.name} ({tileset.tile_count} tiles)")
                except Exception as e:
                    print(f"Error loading {file}: {e}")
        
        if not self.tilesets:
            print("Warning: No tilesets found in game/images/textures/")
    
    def screen_to_iso(self, screen_x, screen_y):
        """Конвертирует экранные координаты в изометрические (сетка)"""
        # Учитываем камеру и zoom
        x = (screen_x - self.camera_x) / self.camera_zoom
        y = (screen_y - self.camera_y) / self.camera_zoom
        
        # Изометрическое преобразование
        tile_x = (x / (TILE_WIDTH / 2) + y / (TILE_HEIGHT / 2)) / 2
        tile_y = (y / (TILE_HEIGHT / 2) - x / (TILE_WIDTH / 2)) / 2
        
        return int(tile_x), int(tile_y)
    
    def iso_to_screen(self, tile_x, tile_y):
        """Конвертирует изометрические координаты в экранные"""
        screen_x = (tile_x - tile_y) * (TILE_WIDTH // 2) * self.camera_zoom + self.camera_x
        screen_y = (tile_x + tile_y) * (TILE_HEIGHT // 2) * self.camera_zoom + self.camera_y
        return screen_x, screen_y
    
    def run(self):
        """Главный цикл редактора"""
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
    
    def _handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mousedown(event)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self._handle_mouseup(event)
            
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mousemotion(event)
            
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mousewheel(event)
    
    def _handle_keydown(self, event):
        """Обработка нажатий клавиш"""
        if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._save_level()
        elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._load_level_dialog()
        elif event.key == pygame.K_g:
            self.show_grid = not self.show_grid
        elif event.key == pygame.K_e:
            self.eraser_mode = not self.eraser_mode
        elif event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_LEFT:
            self.current_tileset_index = (self.current_tileset_index - 1) % len(self.tilesets) if self.tilesets else 0
            self.current_tile_index = 0
        elif event.key == pygame.K_RIGHT:
            self.current_tileset_index = (self.current_tileset_index + 1) % len(self.tilesets) if self.tilesets else 0
            self.current_tile_index = 0
    
    def _handle_mousedown(self, event):
        """Обработка нажатия мыши"""
        x, y = event.pos
        
        # Проверяем клик в панели
        if x > SCREEN_WIDTH - self.panel_width:
            self._handle_panel_click(x, y, event.button)
            return
        
        if event.button == 1:  # ЛКМ - начало рисования
            self.mouse_drawing = True
            self._place_tile_at_hover()
        
        elif event.button == 2:  # СКМ - начало перетаскивания камеры
            self.dragging = True
            self.drag_start = (x, y)
            self.camera_start = (self.camera_x, self.camera_y)
        
        elif event.button == 3:  # ПКМ - начало стирания
            self.mouse_erasing = True
            self._erase_tile_at_hover()
    
    def _handle_mouseup(self, event):
        """Обработка отпускания мыши"""
        if event.button == 1:
            self.mouse_drawing = False
        elif event.button == 2:
            self.dragging = False
        elif event.button == 3:
            self.mouse_erasing = False
    
    def _place_tile_at_hover(self):
        """Ставит тайл в текущей позиции hover"""
        if not self.hover_tile:
            return
        if not (0 <= self.hover_tile[0] < GRID_WIDTH and 0 <= self.hover_tile[1] < GRID_HEIGHT):
            return
        
        if self.eraser_mode:
            self._erase_tile_at_hover()
        elif self.tilesets:
            tileset = self.tilesets[self.current_tileset_index]
            self.level_data[(self.hover_tile[0], self.hover_tile[1])] = {
                'tileset': tileset.name,
                'tile': self.current_tile_index
            }
    
    def _erase_tile_at_hover(self):
        """Удаляет тайл в текущей позиции hover"""
        if not self.hover_tile:
            return
        key = (self.hover_tile[0], self.hover_tile[1])
        if key in self.level_data:
            del self.level_data[key]
    
    def _handle_mousemotion(self, event):
        """Обработка движения мыши"""
        x, y = event.pos
        
        if self.dragging:
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]
            self.camera_x = self.camera_start[0] + dx
            self.camera_y = self.camera_start[1] + dy
        
        # Обновляем hover только для области карты
        if x < SCREEN_WIDTH - self.panel_width:
            self.hover_tile = self.screen_to_iso(x, y)
            
            # Рисуем при зажатой ЛКМ
            if self.mouse_drawing:
                self._place_tile_at_hover()
            
            # Стираем при зажатой ПКМ
            if self.mouse_erasing:
                self._erase_tile_at_hover()
        else:
            self.hover_tile = None
    
    def _handle_mousewheel(self, event):
        """Обработка колеса мыши"""
        x, y = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()
        
        # Скролл в панели - прокрутка тайлов
        if x > SCREEN_WIDTH - self.panel_width:
            self.tile_selector_scroll -= event.y * 30
            self.tile_selector_scroll = max(0, self.tile_selector_scroll)
        else:
            # Ctrl + колесо = zoom
            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                old_zoom = self.camera_zoom
                self.camera_zoom += event.y * 0.1
                self.camera_zoom = max(0.25, min(2.0, self.camera_zoom))
                
                # Центрируем zoom на позиции мыши
                if old_zoom != self.camera_zoom:
                    zoom_factor = self.camera_zoom / old_zoom
                    self.camera_x = x - (x - self.camera_x) * zoom_factor
                    self.camera_y = y - (y - self.camera_y) * zoom_factor
            else:
                # Скролл на карте - смена тайла
                if self.tilesets:
                    tileset = self.tilesets[self.current_tileset_index]
                    self.current_tile_index = (self.current_tile_index + event.y) % tileset.tile_count
    
    def _handle_panel_click(self, x, y, button):
        """Обработка клика в панели"""
        if button != 1:
            return
        
        panel_x = x - (SCREEN_WIDTH - self.panel_width)
        
        # Клик на тайлсете (верхняя часть)
        if 50 <= y <= 80:
            if panel_x < self.panel_width // 2:
                self.current_tileset_index = (self.current_tileset_index - 1) % len(self.tilesets) if self.tilesets else 0
                self.current_tile_index = 0
            else:
                self.current_tileset_index = (self.current_tileset_index + 1) % len(self.tilesets) if self.tilesets else 0
                self.current_tile_index = 0
        
        # Клик на тайле в сетке
        elif y >= 150:
            tile_area_y = y - 150 + self.tile_selector_scroll
            cols = 4
            tile_preview_size = 60
            padding = 5
            
            col = panel_x // (tile_preview_size + padding)
            row = tile_area_y // (tile_preview_size + padding)
            
            if 0 <= col < cols and self.tilesets:
                tile_index = row * cols + col
                tileset = self.tilesets[self.current_tileset_index]
                if tile_index < tileset.tile_count:
                    self.current_tile_index = tile_index
        
        # Кнопки
        if 100 <= y <= 130:
            if 10 <= panel_x <= 90:
                self._save_level()
            elif 100 <= panel_x <= 180:
                self._load_level_dialog()
            elif 190 <= panel_x <= 270:
                self.eraser_mode = not self.eraser_mode
    
    def _update(self):
        """Обновление логики"""
        pass
    
    def _draw(self):
        """Отрисовка"""
        self.screen.fill(COLOR_BG)
        
        # Рисуем уровень
        self._draw_level()
        
        # Рисуем сетку
        if self.show_grid:
            self._draw_grid()
        
        # Рисуем hover
        self._draw_hover()
        
        # Рисуем панель
        self._draw_panel()
        
        # Рисуем подсказки
        self._draw_help()
    
    def _draw_level(self):
        """Отрисовка уровня"""
        # Сортируем тайлы для правильного порядка отрисовки
        sorted_tiles = sorted(self.level_data.items(), key=lambda x: (x[0][0] + x[0][1], x[0][0]))
        
        # Размер тайла с учётом zoom
        scaled_width = int(TILE_WIDTH * self.camera_zoom)
        scaled_height = int(TILE_HEIGHT * self.camera_zoom)
        
        for (tx, ty), data in sorted_tiles:
            screen_x, screen_y = self.iso_to_screen(tx, ty)
            
            # Пропускаем тайлы за пределами экрана
            if screen_x < -scaled_width or screen_x > SCREEN_WIDTH:
                continue
            if screen_y < -scaled_height or screen_y > SCREEN_HEIGHT:
                continue
            
            # Находим тайлсет
            tileset = None
            for ts in self.tilesets:
                if ts.name == data['tileset']:
                    tileset = ts
                    break
            
            if tileset:
                tile = tileset.get_tile(data['tile'])
                if tile:
                    if self.camera_zoom != 1.0:
                        scaled_tile = pygame.transform.scale(tile, (scaled_width, scaled_height))
                        self.screen.blit(scaled_tile, (screen_x, screen_y))
                    else:
                        self.screen.blit(tile, (screen_x, screen_y))
    
    def _draw_grid(self):
        """Отрисовка сетки"""
        tw = int(TILE_WIDTH * self.camera_zoom)
        th = int(TILE_HEIGHT * self.camera_zoom)
        
        for y in range(GRID_HEIGHT + 1):
            for x in range(GRID_WIDTH + 1):
                # Рисуем ромб
                sx, sy = self.iso_to_screen(x, y)
                
                # Пропускаем за пределами экрана
                if sx < -tw or sx > SCREEN_WIDTH + tw:
                    continue
                if sy < -th or sy > SCREEN_HEIGHT + th:
                    continue
                
                if x < GRID_WIDTH and y < GRID_HEIGHT:
                    points = [
                        (sx + tw // 2, sy),
                        (sx + tw, sy + th // 2),
                        (sx + tw // 2, sy + th),
                        (sx, sy + th // 2)
                    ]
                    pygame.draw.polygon(self.screen, COLOR_GRID, points, 1)
    
    def _draw_hover(self):
        """Отрисовка подсветки под курсором"""
        if self.hover_tile and 0 <= self.hover_tile[0] < GRID_WIDTH and 0 <= self.hover_tile[1] < GRID_HEIGHT:
            sx, sy = self.iso_to_screen(self.hover_tile[0], self.hover_tile[1])
            tw = int(TILE_WIDTH * self.camera_zoom)
            th = int(TILE_HEIGHT * self.camera_zoom)
            
            points = [
                (sx + tw // 2, sy),
                (sx + tw, sy + th // 2),
                (sx + tw // 2, sy + th),
                (sx, sy + th // 2)
            ]
            
            color = (255, 100, 100) if self.eraser_mode else COLOR_GRID_HOVER
            pygame.draw.polygon(self.screen, color, points, 2)
            
            # Показываем превью тайла
            if not self.eraser_mode and self.tilesets:
                tileset = self.tilesets[self.current_tileset_index]
                tile = tileset.get_tile(self.current_tile_index)
                if tile:
                    preview = tile.copy()
                    preview.set_alpha(150)
                    if self.camera_zoom != 1.0:
                        preview = pygame.transform.scale(preview, (tw, th))
                    self.screen.blit(preview, (sx, sy))
    
    def _draw_panel(self):
        """Отрисовка боковой панели"""
        panel_rect = pygame.Rect(SCREEN_WIDTH - self.panel_width, 0, self.panel_width, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, COLOR_GRID, (panel_rect.x, 0), (panel_rect.x, SCREEN_HEIGHT), 2)
        
        x = SCREEN_WIDTH - self.panel_width + 10
        y = 10
        
        # Заголовок
        title = self.font_large.render("Level Editor", True, COLOR_ACCENT)
        self.screen.blit(title, (x, y))
        y += 40
        
        # Текущий тайлсет
        if self.tilesets:
            tileset = self.tilesets[self.current_tileset_index]
            
            # Стрелки навигации
            arrow_left = self.font.render("◀", True, COLOR_TEXT)
            arrow_right = self.font.render("▶", True, COLOR_TEXT)
            self.screen.blit(arrow_left, (x, y))
            
            ts_name = self.font.render(tileset.name, True, COLOR_TEXT)
            name_x = x + (self.panel_width - 20 - ts_name.get_width()) // 2
            self.screen.blit(ts_name, (name_x, y))
            
            self.screen.blit(arrow_right, (x + self.panel_width - 30, y))
            y += 30
            
            # Текущий тайл
            tile_info = self.font_small.render(f"Tile: {self.current_tile_index + 1}/{tileset.tile_count}", True, COLOR_TEXT_DIM)
            self.screen.blit(tile_info, (x, y))
            y += 25
        
        # Кнопки
        y = 100
        buttons = [
            ("Save", 10, 80),
            ("Load", 100, 80),
            ("Eraser" if not self.eraser_mode else "ERASER!", 190, 80)
        ]
        
        for text, bx, bw in buttons:
            btn_rect = pygame.Rect(SCREEN_WIDTH - self.panel_width + bx, y, bw, 28)
            color = COLOR_ACCENT if text == "ERASER!" else COLOR_BUTTON
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=4)
            btn_text = self.font_small.render(text, True, COLOR_TEXT)
            self.screen.blit(btn_text, (btn_rect.x + (bw - btn_text.get_width()) // 2, btn_rect.y + 6))
        
        y = 150
        
        # Сетка тайлов
        if self.tilesets:
            tileset = self.tilesets[self.current_tileset_index]
            cols = 4
            tile_preview_size = 60
            padding = 5
            
            # Область отсечения
            clip_rect = pygame.Rect(SCREEN_WIDTH - self.panel_width, y, self.panel_width, SCREEN_HEIGHT - y)
            self.screen.set_clip(clip_rect)
            
            for i, tile in enumerate(tileset.tiles):
                col = i % cols
                row = i // cols
                
                tx = x + col * (tile_preview_size + padding)
                ty = y + row * (tile_preview_size + padding) - self.tile_selector_scroll
                
                if ty + tile_preview_size < y or ty > SCREEN_HEIGHT:
                    continue
                
                # Фон тайла
                tile_rect = pygame.Rect(tx, ty, tile_preview_size, tile_preview_size)
                bg_color = COLOR_ACCENT if i == self.current_tile_index else COLOR_BUTTON
                pygame.draw.rect(self.screen, bg_color, tile_rect, border_radius=4)
                
                # Тайл (масштабированный)
                scaled = pygame.transform.scale(tile, (tile_preview_size - 4, (tile_preview_size - 4) // 2))
                self.screen.blit(scaled, (tx + 2, ty + tile_preview_size // 4))
            
            self.screen.set_clip(None)
    
    def _draw_help(self):
        """Отрисовка подсказок"""
        help_texts = [
            "LMB: Draw tiles | RMB: Erase | MMB: Pan camera",
            "Scroll: Change tile | Ctrl+Scroll: Zoom | G: Grid | E: Eraser",
            f"Level: {self.level_name} | Tiles: {len(self.level_data)} | Zoom: {self.camera_zoom:.1f}x"
        ]
        
        y = SCREEN_HEIGHT - 60
        for text in help_texts:
            surface = self.font_small.render(text, True, COLOR_TEXT_DIM)
            self.screen.blit(surface, (10, y))
            y += 18
    
    def _save_level(self):
        """Сохранение уровня"""
        levels_path = Path(__file__).parent.parent.parent / "game" / "levels"
        levels_path.mkdir(exist_ok=True)
        
        level_file = levels_path / f"{self.level_name}.json"
        
        # Конвертируем ключи в строки для JSON
        save_data = {
            'name': self.level_name,
            'width': GRID_WIDTH,
            'height': GRID_HEIGHT,
            'tiles': {f"{k[0]},{k[1]}": v for k, v in self.level_data.items()}
        }
        
        with open(level_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"Level saved: {level_file}")
    
    def _load_level_dialog(self):
        """Загрузка уровня (простой выбор)"""
        levels_path = Path(__file__).parent.parent.parent / "game" / "levels"
        
        if levels_path.exists():
            levels = list(levels_path.glob("*.json"))
            if levels:
                # Загружаем первый найденный уровень
                self._load_level(levels[0])
    
    def _load_level(self, filepath):
        """Загрузка уровня из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.level_name = data.get('name', Path(filepath).stem)
            self.level_data = {}
            
            for key, value in data.get('tiles', {}).items():
                x, y = map(int, key.split(','))
                self.level_data[(x, y)] = value
            
            print(f"Level loaded: {filepath}")
        except Exception as e:
            print(f"Error loading level: {e}")


def main():
    """Точка входа"""
    editor = LevelEditor()
    editor.run()


if __name__ == "__main__":
    main()

