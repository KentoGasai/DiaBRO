/**
 * DiaBRO Enemy Editor - Frontend Application
 */

// State
let enemyTypes = {};
let availableSprites = [];
let availableWeapons = [];
let availableTextures = [];
let currentEnemyId = null;
let currentSpriteImage = null;
let currentWeaponImage = null;
let playerSpriteImage = null;
let animationFrame = 0;
let animationDirection = 0;
let animationInterval = null;
let currentPreviewScale = 1.0;
let currentWeaponOffsetX = 0;
let currentWeaponOffsetY = 0;

// Состояние превью
let previewSidebarVisible = false;
let enemyListAnimations = {}; // Анимации для списка врагов
let editorPreviewAnimation = null; // Анимация в форме редактирования

// DOM Elements
const enemyList = document.getElementById('enemy-list');
const spriteList = document.getElementById('sprite-list');
const editorPanel = document.getElementById('editor-panel');
const welcomePanel = document.getElementById('welcome-panel');
const previewSidebar = document.getElementById('preview-sidebar');
const enemyForm = document.getElementById('enemy-form');
const uploadZone = document.getElementById('upload-zone');
const spriteUpload = document.getElementById('sprite-upload');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupEventListeners();
    setupColorPreview();
});

// ========================================
// Data Loading
// ========================================

async function loadData() {
    try {
        // Загружаем данные врагов
        const response = await fetch('/api/enemy-types');
        const data = await response.json();
        
        enemyTypes = data.enemy_types || {};
        availableSprites = data.available_sprites || [];
        availableWeapons = data.available_weapons || [];
        
        // Загружаем текстуры
        try {
            const texturesResponse = await fetch('/api/textures');
            const texturesData = await texturesResponse.json();
            availableTextures = texturesData.textures || [];
        } catch (e) {
            availableTextures = [];
        }
        
        renderEnemyList();
        renderSpriteList();
        renderTextureList();
        updateSpriteSelects();
    } catch (error) {
        showToast('Ошибка загрузки данных', 'error');
        console.error(error);
    }
}

// ========================================
// Rendering
// ========================================

function renderEnemyList() {
    // Останавливаем все анимации
    Object.values(enemyListAnimations).forEach(anim => {
        if (anim.interval) clearInterval(anim.interval);
    });
    enemyListAnimations = {};
    
    enemyList.innerHTML = '';
    
    Object.entries(enemyTypes).forEach(([id, enemy]) => {
        const item = document.createElement('div');
        item.className = `enemy-item ${id === currentEnemyId ? 'active' : ''}`;
        item.onclick = () => selectEnemy(id);
        
        const color = enemy.color || [200, 50, 50];
        const canvasId = `enemy-preview-${id}`;
        
        item.innerHTML = `
            <div class="enemy-item-preview">
                <canvas id="${canvasId}" width="64" height="64"></canvas>
            </div>
            <div class="enemy-item-text">
                <div class="enemy-item-name">${enemy.name || id}</div>
                <div class="enemy-item-id">${id}</div>
            </div>
        `;
        
        enemyList.appendChild(item);
        
        // Запускаем анимацию если есть спрайт
        if (enemy.sprite_path) {
            startEnemyListAnimation(id, enemy.sprite_path, canvasId, color);
        } else {
            // Рисуем цветной квадрат
            const canvas = document.getElementById(canvasId);
            if (canvas) {
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = `rgb(${color.join(',')})`;
                ctx.fillRect(12, 12, 40, 40);
            }
        }
    });
}

function startEnemyListAnimation(id, spritePath, canvasId, color) {
    const img = new Image();
    img.onload = () => {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const frameSize = 256;
        let frame = 0;
        let direction = 0;
        const directions = [0, 1, 2, 3, 4, 5, 6, 7]; // Все 8 направлений
        
        function draw() {
            ctx.clearRect(0, 0, 64, 64);
            const sx = (frame % 4) * frameSize;
            const sy = direction * frameSize;
            ctx.drawImage(img, sx, sy, frameSize, frameSize, 0, 0, 64, 64);
        }
        
        draw();
        
        const interval = setInterval(() => {
            frame = (frame + 1) % 4;
            if (frame === 0) {
                // Переключаем направление по кругу
                direction = (direction + 1) % 8;
            }
            draw();
        }, 200);
        
        enemyListAnimations[id] = { interval, img };
    };
    img.onerror = () => {
        // Рисуем цветной квадрат при ошибке
        const canvas = document.getElementById(canvasId);
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = `rgb(${color.join(',')})`;
            ctx.fillRect(12, 12, 40, 40);
        }
    };
    
    const filename = spritePath.split('/').pop();
    img.src = `/api/sprites/${filename}`;
}

function renderSpriteList() {
    spriteList.innerHTML = '';
    
    availableSprites.forEach(filename => {
        const item = document.createElement('div');
        item.className = 'sprite-item';
        item.onclick = () => previewSprite(filename);
        
        item.innerHTML = `
            <div class="sprite-item-preview">
                <img src="/api/sprites/${filename}" alt="${filename}">
            </div>
            <span class="sprite-item-name">${filename}</span>
            <span class="sprite-item-delete" onclick="deleteSprite('${filename}', event)">🗑️</span>
        `;
        
        spriteList.appendChild(item);
    });
}

function renderTextureList() {
    const textureList = document.getElementById('texture-list');
    if (!textureList) return;
    
    textureList.innerHTML = '';
    
    availableTextures.forEach(filename => {
        const item = document.createElement('div');
        item.className = 'sprite-item';
        
        item.innerHTML = `
            <div class="sprite-item-preview texture-preview">
                <img src="/api/textures/${filename}" alt="${filename}">
            </div>
            <span class="sprite-item-name">${filename.replace('.png', '')}</span>
            <span class="sprite-item-delete" onclick="deleteTexture('${filename}', event)">🗑️</span>
        `;
        
        textureList.appendChild(item);
    });
}

async function deleteTexture(filename, event) {
    event.stopPropagation();
    
    if (!confirm(`Удалить текстуру ${filename}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/textures/${filename}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Текстура удалена', 'success');
            await loadData();
        } else {
            showToast('Ошибка удаления', 'error');
        }
    } catch (error) {
        showToast('Ошибка удаления', 'error');
        console.error(error);
    }
}

function updateSpriteSelects() {
    const spritePath = document.getElementById('sprite-path');
    const weaponPath = document.getElementById('weapon-path');
    const projectilePath = document.getElementById('projectile-path');
    
    // Спрайты персонажей врагов
    const enemyOptions = '<option value="">-- Без спрайта --</option>' +
        availableSprites.map(s => `<option value="game/images/enemy/${s}">${s}</option>`).join('');
    
    // Спрайты оружия (из папки weapon + enemy)
    const weaponOptions = '<option value="">-- Без оружия --</option>' +
        '<optgroup label="📁 Оружие (weapon/)">' +
        availableWeapons.map(s => `<option value="game/images/weapon/${s}">🗡️ ${s}</option>`).join('') +
        '</optgroup>' +
        '<optgroup label="📁 Враги (enemy/)">' +
        availableSprites.map(s => `<option value="game/images/enemy/${s}">${s}</option>`).join('') +
        '</optgroup>';
    
    spritePath.innerHTML = enemyOptions;
    weaponPath.innerHTML = weaponOptions;
    projectilePath.innerHTML = '<option value="">-- Стандартный (как у игрока) --</option>' +
        availableSprites.map(s => `<option value="game/images/enemy/${s}">${s}</option>`).join('');
}

// ========================================
// Enemy Operations
// ========================================

function createNewEnemy() {
    currentEnemyId = null;
    
    document.getElementById('enemy-id').value = '';
    document.getElementById('enemy-id-input').value = '';
    document.getElementById('enemy-id-input').disabled = false;
    document.getElementById('enemy-name').value = '';
    document.getElementById('sprite-path').value = '';
    document.getElementById('weapon-path').value = '';
    document.getElementById('sprite-scale').value = '1.0';
    document.getElementById('max-health').value = '30';
    document.getElementById('damage').value = '5';
    document.getElementById('speed').value = '6.0';  // Немного медленнее игрока (8.0)
    document.getElementById('aggro-range').value = '150';
    document.getElementById('attack-range').value = '1.2';
    document.getElementById('attack-cooldown').value = '1.5';
    document.getElementById('color-r').value = '200';
    document.getElementById('color-g').value = '50';
    document.getElementById('color-b').value = '50';
    
    // Тип атаки
    document.querySelector('input[name="attack-type"][value="melee"]').checked = true;
    document.getElementById('projectile-path').value = '';
    
    // Смещение оружия
    document.getElementById('weapon-offset-x').value = '0';
    document.getElementById('weapon-offset-y').value = '0';
    currentWeaponOffsetX = 0;
    currentWeaponOffsetY = 0;
    currentWeaponImage = null;
    
    updateAttackTypeUI();
    updateWeaponOffsetUI();
    
    updateColorPreview();
    updatePreviewScale(1.0);
    
    document.getElementById('editor-title').textContent = 'Новый тип врага';
    
    showEditor();
    startEditorPreview();
}

function selectEnemy(id) {
    currentEnemyId = id;
    const enemy = enemyTypes[id];
    
    if (!enemy) return;
    
    document.getElementById('enemy-id').value = id;
    document.getElementById('enemy-id-input').value = id;
    document.getElementById('enemy-id-input').disabled = true;
    document.getElementById('enemy-name').value = enemy.name || id;
    document.getElementById('sprite-path').value = enemy.sprite_path || '';
    document.getElementById('weapon-path').value = enemy.weapon_path || '';
    document.getElementById('sprite-scale').value = enemy.sprite_scale || 1.0;
    document.getElementById('max-health').value = enemy.max_health || 30;
    document.getElementById('damage').value = enemy.damage || 5;
    document.getElementById('speed').value = enemy.speed || 6.0;
    document.getElementById('aggro-range').value = enemy.aggro_range || 150;
    document.getElementById('attack-range').value = enemy.attack_range || 1.2;
    document.getElementById('attack-cooldown').value = enemy.attack_cooldown || 1.5;
    
    // Тип атаки
    const attackType = enemy.attack_type || 'melee';
    document.querySelector(`input[name="attack-type"][value="${attackType}"]`).checked = true;
    document.getElementById('projectile-path').value = enemy.projectile_path || '';
    
    // Смещение оружия
    const weaponOffset = enemy.weapon_offset || [0, 0];
    document.getElementById('weapon-offset-x').value = weaponOffset[0] || 0;
    document.getElementById('weapon-offset-y').value = weaponOffset[1] || 0;
    currentWeaponOffsetX = weaponOffset[0] || 0;
    currentWeaponOffsetY = weaponOffset[1] || 0;
    
    updateAttackTypeUI();
    
    const color = enemy.color || [200, 50, 50];
    document.getElementById('color-r').value = color[0];
    document.getElementById('color-g').value = color[1];
    document.getElementById('color-b').value = color[2];
    
    updateColorPreview();
    
    // Обновляем превью масштаба
    const scale = enemy.sprite_scale || 1.0;
    updatePreviewScale(scale);
    
    document.getElementById('editor-title').textContent = `Редактирование: ${enemy.name || id}`;
    
    // Предзагружаем спрайты для превью
    if (enemy.sprite_path) {
        const filename = enemy.sprite_path.split('/').pop();
        previewSprite(filename);
    }
    
    if (enemy.weapon_path) {
        loadWeaponSprite(enemy.weapon_path);
    }
    
    updateWeaponOffsetUI();
    
    // Закрываем превью при смене врага
    if (previewSidebarVisible) {
        previewSidebarVisible = false;
        previewSidebar.classList.add('hidden');
        stopAnimation();
    }
    
    showEditor();
    renderEnemyList();
    
    // Запускаем анимацию в форме (с задержкой для загрузки спрайтов)
    setTimeout(() => {
        startEditorPreview();
    }, 150);
}

function updateAttackTypeUI() {
    const attackType = document.querySelector('input[name="attack-type"]:checked').value;
    const projectileRow = document.getElementById('projectile-row');
    const attackRangeInput = document.getElementById('attack-range');
    
    if (attackType === 'ranged') {
        projectileRow.style.display = 'flex';
        // Автоматически увеличиваем дистанцию атаки для дальнего боя
        if (parseFloat(attackRangeInput.value) < 5) {
            attackRangeInput.value = '8.0';
        }
    } else {
        projectileRow.style.display = 'none';
        // Возвращаем дистанцию для ближнего боя
        if (parseFloat(attackRangeInput.value) > 3) {
            attackRangeInput.value = '1.2';
        }
    }
}

function updateWeaponOffsetUI() {
    const weaponPath = document.getElementById('weapon-path').value;
    const weaponOffsetRow = document.getElementById('weapon-offset-row');
    const weaponSection = document.getElementById('weapon-section');
    
    if (weaponPath) {
        if (weaponOffsetRow) weaponOffsetRow.style.display = 'flex';
        if (weaponSection) weaponSection.style.display = 'block';
        loadWeaponSprite(weaponPath);
    } else {
        if (weaponOffsetRow) weaponOffsetRow.style.display = 'none';
        if (weaponSection) weaponSection.style.display = 'none';
        currentWeaponImage = null;
    }
}

function loadWeaponSprite(weaponPath) {
    if (!weaponPath) {
        currentWeaponImage = null;
        return;
    }
    
    const img = new Image();
    img.onload = () => {
        currentWeaponImage = img;
        console.log('Weapon loaded:', weaponPath);
    };
    img.onerror = () => {
        currentWeaponImage = null;
        console.error('Failed to load weapon:', weaponPath);
    };
    
    // Определяем URL для загрузки
    const filename = weaponPath.split('/').pop();
    if (weaponPath.includes('weapon')) {
        img.src = `/api/weapons/${filename}`;
    } else {
        img.src = `/api/sprites/${filename}`;
    }
}

function updateWeaponOffset() {
    currentWeaponOffsetX = parseInt(document.getElementById('weapon-offset-x').value) || 0;
    currentWeaponOffsetY = parseInt(document.getElementById('weapon-offset-y').value) || 0;
}

async function saveEnemy(event) {
    event.preventDefault();
    
    const id = document.getElementById('enemy-id').value || 
               document.getElementById('enemy-id-input').value;
    
    if (!id) {
        showToast('Введите ID врага', 'error');
        return;
    }
    
    const attackType = document.querySelector('input[name="attack-type"]:checked').value;
    
    const data = {
        id: id,
        name: document.getElementById('enemy-name').value || id,
        sprite_path: document.getElementById('sprite-path').value,
        weapon_path: document.getElementById('weapon-path').value,
        weapon_offset: [
            parseInt(document.getElementById('weapon-offset-x').value) || 0,
            parseInt(document.getElementById('weapon-offset-y').value) || 0
        ],
        projectile_path: document.getElementById('projectile-path').value,
        sprite_scale: parseFloat(document.getElementById('sprite-scale').value),
        max_health: parseInt(document.getElementById('max-health').value),
        damage: parseInt(document.getElementById('damage').value),
        speed: parseFloat(document.getElementById('speed').value),
        attack_type: attackType,
        aggro_range: parseFloat(document.getElementById('aggro-range').value),
        attack_range: parseFloat(document.getElementById('attack-range').value),
        attack_cooldown: parseFloat(document.getElementById('attack-cooldown').value),
        color: [
            parseInt(document.getElementById('color-r').value),
            parseInt(document.getElementById('color-g').value),
            parseInt(document.getElementById('color-b').value)
        ]
    };
    
    try {
        const isNew = !currentEnemyId;
        const url = isNew ? '/api/enemy-types' : `/api/enemy-types/${currentEnemyId}`;
        const method = isNew ? 'POST' : 'PUT';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Враг сохранён!', 'success');
            await loadData();
            
            if (isNew) {
                currentEnemyId = data.id.toLowerCase().replace(' ', '_');
            }
            
            renderEnemyList();
        } else {
            const error = await response.json();
            showToast(error.error || 'Ошибка сохранения', 'error');
        }
    } catch (error) {
        showToast('Ошибка сохранения', 'error');
        console.error(error);
    }
}

async function deleteEnemy() {
    if (!currentEnemyId) return;
    
    if (!confirm(`Удалить тип врага "${currentEnemyId}"?`)) return;
    
    try {
        const response = await fetch(`/api/enemy-types/${currentEnemyId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Враг удалён', 'success');
            currentEnemyId = null;
            hideEditor();
            await loadData();
        } else {
            showToast('Ошибка удаления', 'error');
        }
    } catch (error) {
        showToast('Ошибка удаления', 'error');
        console.error(error);
    }
}

function cancelEdit() {
    currentEnemyId = null;
    hideEditor();
    renderEnemyList();
}

// ========================================
// Sprite Operations
// ========================================

async function uploadSprite(file) {
    const formData = new FormData();
    formData.append('sprite', file);
    
    try {
        const response = await fetch('/api/upload-sprite', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Спрайт "${data.filename}" загружен!`, 'success');
            await loadData();
            previewSprite(data.filename);
        } else {
            const error = await response.json();
            showToast(error.error || 'Ошибка загрузки', 'error');
        }
    } catch (error) {
        showToast('Ошибка загрузки', 'error');
        console.error(error);
    }
}

async function deleteSprite(filename, event) {
    event.stopPropagation();
    
    if (!confirm(`Удалить спрайт "${filename}"?`)) return;
    
    try {
        const response = await fetch(`/api/delete-sprite/${filename}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Спрайт удалён', 'success');
            currentSpriteImage = null;
            if (previewSidebarVisible) {
                togglePreviewPanel();
            }
            await loadData();
        } else {
            showToast('Ошибка удаления', 'error');
        }
    } catch (error) {
        showToast('Ошибка удаления', 'error');
        console.error(error);
    }
}

// ========================================
// Preview Sidebar
// ========================================

function togglePreviewPanel() {
    previewSidebarVisible = !previewSidebarVisible;
    
    if (previewSidebarVisible) {
        previewSidebar.classList.remove('hidden');
        loadPlayerSprite();
        loadCurrentSprites();
        startAnimation();
    } else {
        previewSidebar.classList.add('hidden');
        stopAnimation();
    }
}

function loadCurrentSprites() {
    const spritePath = document.getElementById('sprite-path').value;
    const weaponPath = document.getElementById('weapon-path').value;
    
    // Загружаем спрайт персонажа
    if (spritePath) {
        const filename = spritePath.split('/').pop();
        const img = new Image();
        img.onload = () => {
            currentSpriteImage = img;
        };
        img.src = `/api/sprites/${filename}`;
    }
    
    // Загружаем оружие
    if (weaponPath) {
        loadWeaponSprite(weaponPath);
        document.getElementById('weapon-section').style.display = 'block';
    } else {
        document.getElementById('weapon-section').style.display = 'none';
        currentWeaponImage = null;
    }
    
    // Обновляем отображение смещения
    currentWeaponOffsetX = parseInt(document.getElementById('weapon-offset-x').value) || 0;
    currentWeaponOffsetY = parseInt(document.getElementById('weapon-offset-y').value) || 0;
    updateOffsetDisplay();
    
    // Масштаб
    const scale = parseFloat(document.getElementById('sprite-scale').value) || 1.0;
    currentPreviewScale = scale;
    updatePreviewScale(scale);
}

function previewSprite(filename) {
    const img = new Image();
    img.onload = () => {
        currentSpriteImage = img;
    };
    img.src = `/api/sprites/${filename}`;
}

function loadPlayerSprite() {
    if (playerSpriteImage) return;
    
    const img = new Image();
    img.onload = () => {
        playerSpriteImage = img;
    };
    img.src = '/api/player-sprite';
}

function updatePreviewScale(scale) {
    currentPreviewScale = scale;
    const scaleSlider = document.getElementById('preview-scale');
    const scaleValue = document.getElementById('preview-scale-value');
    const scaleLabel = document.getElementById('enemy-scale-label');
    
    if (scaleSlider) scaleSlider.value = scale;
    if (scaleValue) scaleValue.textContent = scale.toFixed(1) + 'x';
    if (scaleLabel) scaleLabel.textContent = `Противник (${scale.toFixed(1)}x)`;
}

function applyScaleToForm() {
    document.getElementById('sprite-scale').value = currentPreviewScale.toFixed(1);
    showToast(`Масштаб ${currentPreviewScale.toFixed(1)}x применён`, 'success');
}

function updateOffsetDisplay() {
    const offsetX = document.getElementById('offset-x-display');
    const offsetY = document.getElementById('offset-y-display');
    if (offsetX) offsetX.textContent = currentWeaponOffsetX;
    if (offsetY) offsetY.textContent = currentWeaponOffsetY;
}

function adjustWeaponOffset(dx, dy) {
    currentWeaponOffsetX += dx;
    currentWeaponOffsetY += dy;
    updateOffsetDisplay();
}

function applyWeaponOffsetToForm() {
    document.getElementById('weapon-offset-x').value = currentWeaponOffsetX;
    document.getElementById('weapon-offset-y').value = currentWeaponOffsetY;
    showToast(`Смещение (${currentWeaponOffsetX}, ${currentWeaponOffsetY}) применено`, 'success');
}

function startAnimation() {
    stopAnimation();
    
    const enemyCanvas = document.getElementById('enemy-canvas');
    const playerCanvas = document.getElementById('player-canvas');
    const weaponCanvas = document.getElementById('weapon-preview-canvas');
    
    if (!enemyCanvas || !playerCanvas) return;
    
    const enemyCtx = enemyCanvas.getContext('2d');
    const playerCtx = playerCanvas.getContext('2d');
    const weaponCtx = weaponCanvas ? weaponCanvas.getContext('2d') : null;
    
    const frameSize = 256;
    
    function draw() {
        // Очистка
        enemyCtx.clearRect(0, 0, 128, 128);
        playerCtx.clearRect(0, 0, 128, 128);
        if (weaponCtx) weaponCtx.clearRect(0, 0, 160, 160);
        
        const sx = (animationFrame % 4) * frameSize;
        const sy = animationDirection * frameSize;
        
        // Игрок (всегда масштаб 1.0)
        if (playerSpriteImage) {
            playerCtx.drawImage(playerSpriteImage, sx, sy, frameSize, frameSize, 0, 0, 128, 128);
        } else {
            playerCtx.fillStyle = '#3366aa';
            playerCtx.fillRect(14, 14, 100, 100);
            playerCtx.fillStyle = '#fff';
            playerCtx.font = '12px sans-serif';
            playerCtx.textAlign = 'center';
            playerCtx.fillText('Игрок', 64, 68);
        }
        
        // Противник с масштабом
        if (currentSpriteImage) {
            const scaledSize = 128 * currentPreviewScale;
            const offset = (128 - scaledSize) / 2;
            enemyCtx.drawImage(currentSpriteImage, sx, sy, frameSize, frameSize, offset, offset, scaledSize, scaledSize);
        }
        
        // Превью оружия (большое для настройки)
        if (weaponCtx && currentSpriteImage) {
            // Рисуем персонажа
            weaponCtx.drawImage(currentSpriteImage, sx, sy, frameSize, frameSize, 0, 0, 160, 160);
            
            // Накладываем оружие с тем же кадром анимации
            if (currentWeaponImage) {
                // Смещение масштабируется пропорционально (160/256)
                const scale = 160 / frameSize;
                const weaponOffsetX = currentWeaponOffsetX * scale;
                const weaponOffsetY = currentWeaponOffsetY * scale;
                weaponCtx.drawImage(currentWeaponImage, sx, sy, frameSize, frameSize, weaponOffsetX, weaponOffsetY, 160, 160);
            }
        }
    }
    
    draw();
    
    animationInterval = setInterval(() => {
        animationFrame = (animationFrame + 1) % 4;
        draw();
    }, 150);
}

function stopAnimation() {
    if (animationInterval) {
        clearInterval(animationInterval);
        animationInterval = null;
    }
}

function prevDirection() {
    animationDirection = (animationDirection - 1 + 8) % 8;
    updateDirectionLabel();
}

function nextDirection() {
    animationDirection = (animationDirection + 1) % 8;
    updateDirectionLabel();
}

function updateDirectionLabel() {
    const directions = ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'];
    const dirLabel = document.getElementById('direction-label');
    if (dirLabel) {
        dirLabel.textContent = directions[animationDirection];
    }
}

// ========================================
// Editor Preview Animation (в форме)
// ========================================

function startEditorPreview() {
    stopEditorPreview();
    
    const canvas = document.getElementById('editor-preview-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const canvasSize = 500;
    const frameSize = 256;
    let frame = 0;
    let direction = 0;
    
    function draw() {
        ctx.clearRect(0, 0, canvasSize, canvasSize);
        
        if (currentSpriteImage) {
            const sx = (frame % 4) * frameSize;
            const sy = direction * frameSize;
            
            // Рисуем персонажа
            ctx.drawImage(currentSpriteImage, sx, sy, frameSize, frameSize, 0, 0, canvasSize, canvasSize);
            
            // Накладываем оружие
            if (currentWeaponImage) {
                const scale = canvasSize / frameSize;
                const offsetX = currentWeaponOffsetX * scale;
                const offsetY = currentWeaponOffsetY * scale;
                ctx.drawImage(currentWeaponImage, sx, sy, frameSize, frameSize, offsetX, offsetY, canvasSize, canvasSize);
            }
        } else {
            // Плейсхолдер
            ctx.fillStyle = '#333';
            ctx.fillRect(0, 0, canvasSize, canvasSize);
            ctx.fillStyle = '#666';
            ctx.font = '14px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Нет спрайта', canvasSize / 2, canvasSize / 2 + 5);
        }
    }
    
    draw();
    
    editorPreviewAnimation = setInterval(() => {
        frame = (frame + 1) % 4;
        if (frame === 0) {
            direction = (direction + 1) % 8;
        }
        draw();
    }, 200);
}

function stopEditorPreview() {
    if (editorPreviewAnimation) {
        clearInterval(editorPreviewAnimation);
        editorPreviewAnimation = null;
    }
}

// ========================================
// Export
// ========================================

async function exportCode() {
    try {
        const response = await fetch('/api/export-code');
        const data = await response.json();
        
        document.getElementById('export-code').value = data.code;
        document.getElementById('export-modal').classList.remove('hidden');
    } catch (error) {
        showToast('Ошибка экспорта', 'error');
        console.error(error);
    }
}

function closeExportModal() {
    document.getElementById('export-modal').classList.add('hidden');
}

function copyCode() {
    const textarea = document.getElementById('export-code');
    textarea.select();
    document.execCommand('copy');
    showToast('Код скопирован!', 'success');
}

// ========================================
// UI Helpers
// ========================================

function showEditor() {
    editorPanel.classList.remove('hidden');
    welcomePanel.classList.add('hidden');
}

function hideEditor() {
    editorPanel.classList.add('hidden');
    welcomePanel.classList.remove('hidden');
}

function setupColorPreview() {
    ['color-r', 'color-g', 'color-b'].forEach(id => {
        document.getElementById(id).addEventListener('input', updateColorPreview);
    });
}

function updateColorPreview() {
    const r = document.getElementById('color-r').value;
    const g = document.getElementById('color-g').value;
    const b = document.getElementById('color-b').value;
    document.getElementById('color-preview').style.background = `rgb(${r}, ${g}, ${b})`;
}

function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ========================================
// Event Listeners
// ========================================

function setupEventListeners() {
    // Form submit
    enemyForm.addEventListener('submit', saveEnemy);
    
    // Upload zone
    uploadZone.addEventListener('click', () => spriteUpload.click());
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadSprite(files[0]);
        }
    });
    
    spriteUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadSprite(e.target.files[0]);
        }
    });
    
    // Sprite select change - preload
    document.getElementById('sprite-path').addEventListener('change', (e) => {
        const value = e.target.value;
        if (value) {
            const filename = value.split('/').pop();
            previewSprite(filename);
            
            // Если выбрано оружие — загружаем и его
            const weaponPath = document.getElementById('weapon-path').value;
            if (weaponPath) {
                loadWeaponSprite(weaponPath);
            }
            
            // Обновляем превью в форме
            setTimeout(() => startEditorPreview(), 150);
        } else {
            currentSpriteImage = null;
            startEditorPreview(); // Покажет плейсхолдер
        }
    });
    
    // Scale slider
    document.getElementById('preview-scale').addEventListener('input', (e) => {
        const scale = parseFloat(e.target.value);
        currentPreviewScale = scale;
        document.getElementById('preview-scale-value').textContent = scale.toFixed(1) + 'x';
        document.getElementById('enemy-scale-label').textContent = `Противник (${scale.toFixed(1)}x)`;
    });
    
    // Sync form scale to preview
    document.getElementById('sprite-scale').addEventListener('change', (e) => {
        const scale = parseFloat(e.target.value) || 1.0;
        if (currentSpriteImage) {
            updatePreviewScale(scale);
        }
    });
    
    // Attack type radio buttons
    document.querySelectorAll('input[name="attack-type"]').forEach(radio => {
        radio.addEventListener('change', updateAttackTypeUI);
    });
    
    // Weapon path change - show/hide offset controls and load weapon
    document.getElementById('weapon-path').addEventListener('change', () => {
        updateWeaponOffsetUI();
        // Обновляем превью в форме
        setTimeout(() => startEditorPreview(), 150);
    });
    
    // Weapon offset - real-time preview
    document.getElementById('weapon-offset-x').addEventListener('input', updateWeaponOffset);
    document.getElementById('weapon-offset-y').addEventListener('input', updateWeaponOffset);
    
    // Close modal on outside click
    document.getElementById('export-modal').addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeExportModal();
        }
    });
    
    // Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeExportModal();
        }
    });
    
    // Texture upload
    const textureUploadZone = document.getElementById('texture-upload-zone');
    const textureUpload = document.getElementById('texture-upload');
    
    if (textureUploadZone && textureUpload) {
        textureUploadZone.addEventListener('click', () => textureUpload.click());
        
        textureUploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            textureUploadZone.classList.add('dragover');
        });
        
        textureUploadZone.addEventListener('dragleave', () => {
            textureUploadZone.classList.remove('dragover');
        });
        
        textureUploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            textureUploadZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                uploadTexture(files[0]);
            }
        });
        
        textureUpload.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadTexture(e.target.files[0]);
            }
        });
    }
}

async function uploadTexture(file) {
    if (!file.name.endsWith('.png')) {
        showToast('Разрешены только PNG файлы', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('texture', file);
    
    try {
        const response = await fetch('/api/textures', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showToast(`Текстура ${file.name} загружена!`, 'success');
            await loadData();
        } else {
            const error = await response.json();
            showToast(error.error || 'Ошибка загрузки', 'error');
        }
    } catch (error) {
        showToast('Ошибка загрузки', 'error');
        console.error(error);
    }
}

