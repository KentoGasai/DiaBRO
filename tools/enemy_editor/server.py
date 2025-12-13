"""
Веб-редактор типов врагов для DiaBRO
Запуск: python tools/enemy_editor/server.py
"""
import os
import sys
import json
import shutil
from pathlib import Path

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Конфигурация
ENEMY_SPRITES_DIR = PROJECT_ROOT / 'game' / 'images' / 'enemy'
ENEMY_CONFIG_FILE = PROJECT_ROOT / 'game' / 'enemy_types.json'
ALLOWED_EXTENSIONS = {'png'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Создаём директории если не существуют
ENEMY_SPRITES_DIR.mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    """Проверяет допустимое расширение файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_enemy_types():
    """Загружает конфигурацию типов врагов"""
    if ENEMY_CONFIG_FILE.exists():
        with open(ENEMY_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_enemy_types(data):
    """Сохраняет конфигурацию типов врагов"""
    with open(ENEMY_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_available_sprites():
    """Возвращает список доступных спрайтов"""
    sprites = []
    if ENEMY_SPRITES_DIR.exists():
        for file in ENEMY_SPRITES_DIR.glob('*.png'):
            sprites.append(file.name)
    return sorted(sprites)


@app.route('/')
def index():
    """Главная страница редактора"""
    return render_template('index.html')


@app.route('/api/enemy-types', methods=['GET'])
def get_enemy_types():
    """Получить все типы врагов"""
    enemy_types = load_enemy_types()
    sprites = get_available_sprites()
    return jsonify({
        'enemy_types': enemy_types,
        'available_sprites': sprites
    })


@app.route('/api/enemy-types/<enemy_id>', methods=['GET'])
def get_enemy_type(enemy_id):
    """Получить конкретный тип врага"""
    enemy_types = load_enemy_types()
    if enemy_id in enemy_types:
        return jsonify(enemy_types[enemy_id])
    return jsonify({'error': 'Тип врага не найден'}), 404


@app.route('/api/enemy-types', methods=['POST'])
def create_enemy_type():
    """Создать новый тип врага"""
    data = request.json
    
    if not data.get('id'):
        return jsonify({'error': 'ID обязателен'}), 400
    
    enemy_id = data['id'].lower().replace(' ', '_')
    
    enemy_types = load_enemy_types()
    
    attack_type = data.get('attack_type', 'melee')
    
    # sprite_scale: 1.0 = размер игрока (256px)
    # speed: 6.0 = немного медленнее игрока (8.0)
    enemy_types[enemy_id] = {
        'name': data.get('name', enemy_id),
        'sprite_path': data.get('sprite_path', ''),
        'weapon_path': data.get('weapon_path', ''),
        'projectile_path': data.get('projectile_path', ''),
        'sprite_scale': float(data.get('sprite_scale', 1.0)),
        'max_health': int(data.get('max_health', 30)),
        'damage': int(data.get('damage', 5)),
        'speed': float(data.get('speed', 6.0)),  # Немного медленнее игрока
        'attack_type': attack_type,  # 'melee' или 'ranged'
        'aggro_range': float(data.get('aggro_range', 150)),
        'attack_range': float(data.get('attack_range', 1.2 if attack_type == 'melee' else 8.0)),
        'attack_cooldown': float(data.get('attack_cooldown', 1.5)),
        'color': data.get('color', [200, 50, 50]),
    }
    
    save_enemy_types(enemy_types)
    return jsonify({'success': True, 'id': enemy_id})


@app.route('/api/enemy-types/<enemy_id>', methods=['PUT'])
def update_enemy_type(enemy_id):
    """Обновить тип врага"""
    data = request.json
    enemy_types = load_enemy_types()
    
    if enemy_id not in enemy_types:
        return jsonify({'error': 'Тип врага не найден'}), 404
    
    attack_type = data.get('attack_type', enemy_types[enemy_id].get('attack_type', 'melee'))
    
    enemy_types[enemy_id].update({
        'name': data.get('name', enemy_types[enemy_id].get('name', enemy_id)),
        'sprite_path': data.get('sprite_path', enemy_types[enemy_id].get('sprite_path', '')),
        'weapon_path': data.get('weapon_path', enemy_types[enemy_id].get('weapon_path', '')),
        'projectile_path': data.get('projectile_path', enemy_types[enemy_id].get('projectile_path', '')),
        'sprite_scale': float(data.get('sprite_scale', enemy_types[enemy_id].get('sprite_scale', 1.0))),
        'max_health': int(data.get('max_health', enemy_types[enemy_id].get('max_health', 30))),
        'damage': int(data.get('damage', enemy_types[enemy_id].get('damage', 5))),
        'speed': float(data.get('speed', enemy_types[enemy_id].get('speed', 6.0))),
        'attack_type': attack_type,
        'aggro_range': float(data.get('aggro_range', enemy_types[enemy_id].get('aggro_range', 150))),
        'attack_range': float(data.get('attack_range', enemy_types[enemy_id].get('attack_range', 1.2 if attack_type == 'melee' else 8.0))),
        'attack_cooldown': float(data.get('attack_cooldown', enemy_types[enemy_id].get('attack_cooldown', 1.5))),
        'color': data.get('color', enemy_types[enemy_id].get('color', [200, 50, 50])),
    })
    
    save_enemy_types(enemy_types)
    return jsonify({'success': True})


@app.route('/api/enemy-types/<enemy_id>', methods=['DELETE'])
def delete_enemy_type(enemy_id):
    """Удалить тип врага"""
    enemy_types = load_enemy_types()
    
    if enemy_id not in enemy_types:
        return jsonify({'error': 'Тип врага не найден'}), 404
    
    del enemy_types[enemy_id]
    save_enemy_types(enemy_types)
    return jsonify({'success': True})


@app.route('/api/upload-sprite', methods=['POST'])
def upload_sprite():
    """Загрузить спрайт врага"""
    if 'sprite' not in request.files:
        return jsonify({'error': 'Файл не выбран'}), 400
    
    file = request.files['sprite']
    
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Разрешены только PNG файлы'}), 400
    
    filename = secure_filename(file.filename)
    filepath = ENEMY_SPRITES_DIR / filename
    
    file.save(str(filepath))
    
    return jsonify({
        'success': True, 
        'filename': filename,
        'path': f'game/images/enemy/{filename}'
    })


@app.route('/api/sprites/<filename>')
def get_sprite(filename):
    """Получить спрайт для предпросмотра"""
    return send_from_directory(str(ENEMY_SPRITES_DIR), filename)


@app.route('/api/player-sprite')
def get_player_sprite():
    """Получить спрайт игрока для сравнения"""
    player_sprite_path = PROJECT_ROOT / 'game' / 'images' / 'character' / 'male_unarmored.png'
    
    if player_sprite_path.exists():
        return send_from_directory(
            str(player_sprite_path.parent), 
            player_sprite_path.name
        )
    
    # Возвращаем 404 если спрайт игрока не найден
    return jsonify({'error': 'Спрайт игрока не найден'}), 404


@app.route('/api/delete-sprite/<filename>', methods=['DELETE'])
def delete_sprite(filename):
    """Удалить спрайт"""
    filepath = ENEMY_SPRITES_DIR / secure_filename(filename)
    
    if filepath.exists():
        filepath.unlink()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Файл не найден'}), 404


@app.route('/api/export-code')
def export_code():
    """Экспортировать код для enemy.py"""
    enemy_types = load_enemy_types()
    
    code_lines = ["# Автогенерированный код типов врагов", 
                  "# Скопируйте в BUILTIN_ENEMY_TYPES в game/enemy.py", 
                  "# Или используйте через enemy_types.json (рекомендуется)",
                  "",
                  "ENEMY_TYPES = {"]
    
    for enemy_id, params in enemy_types.items():
        attack_type = params.get('attack_type', 'melee')
        code_lines.append(f"    '{enemy_id}': {{")
        code_lines.append(f"        'name': '{params.get('name', enemy_id)}',")
        code_lines.append(f"        'sprite_path': '{params.get('sprite_path', '')}' or None,")
        code_lines.append(f"        'weapon_path': '{params.get('weapon_path', '')}' or None,")
        code_lines.append(f"        'projectile_path': '{params.get('projectile_path', '')}' or None,")
        code_lines.append(f"        'sprite_scale': {params.get('sprite_scale', 1.0)},")
        code_lines.append(f"        'max_health': {params.get('max_health', 30)},")
        code_lines.append(f"        'damage': {params.get('damage', 5)},")
        code_lines.append(f"        'speed': {params.get('speed', 6.0)},")
        code_lines.append(f"        'attack_type': '{attack_type}',")
        code_lines.append(f"        'aggro_range': {params.get('aggro_range', 150)},")
        code_lines.append(f"        'attack_range': {params.get('attack_range', 1.2)},")
        code_lines.append(f"        'attack_cooldown_time': {params.get('attack_cooldown', 1.5)},")
        code_lines.append(f"        'color': {tuple(params.get('color', [200, 50, 50]))},")
        code_lines.append("    },")
    
    code_lines.append("}")
    
    return jsonify({'code': '\n'.join(code_lines)})


if __name__ == '__main__':
    print("=" * 50)
    print("🎮 DiaBRO Enemy Editor")
    print("=" * 50)
    print(f"📁 Спрайты: {ENEMY_SPRITES_DIR}")
    print(f"📄 Конфиг: {ENEMY_CONFIG_FILE}")
    print(f"🌐 Откройте в браузере: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)

