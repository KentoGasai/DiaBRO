/**
 * DiaBRO Enemy Editor - Frontend Application
 */

// State
let enemyTypes = {};
let availableSprites = [];
let currentEnemyId = null;
let currentSpriteImage = null;
let playerSpriteImage = null;
let animationFrame = 0;
let animationDirection = 0;
let animationInterval = null;
let currentPreviewScale = 1.0;

// DOM Elements
const enemyList = document.getElementById('enemy-list');
const spriteList = document.getElementById('sprite-list');
const editorPanel = document.getElementById('editor-panel');
const welcomePanel = document.getElementById('welcome-panel');
const previewPanel = document.getElementById('preview-panel');
const animationPreview = document.getElementById('animation-preview');
const spritePreview = document.getElementById('sprite-preview');
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
        const response = await fetch('/api/enemy-types');
        const data = await response.json();
        
        enemyTypes = data.enemy_types || {};
        availableSprites = data.available_sprites || [];
        
        renderEnemyList();
        renderSpriteList();
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
    enemyList.innerHTML = '';
    
    Object.entries(enemyTypes).forEach(([id, enemy]) => {
        const item = document.createElement('div');
        item.className = `enemy-item ${id === currentEnemyId ? 'active' : ''}`;
        item.onclick = () => selectEnemy(id);
        
        const color = enemy.color || [200, 50, 50];
        
        item.innerHTML = `
            <div class="enemy-item-icon" style="background: rgb(${color.join(',')})">
                ${enemy.sprite_path ? '🎨' : '👾'}
            </div>
            <div class="enemy-item-info">
                <div class="enemy-item-name">${enemy.name || id}</div>
                <div class="enemy-item-id">${id}</div>
            </div>
        `;
        
        enemyList.appendChild(item);
    });
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

function updateSpriteSelects() {
    const spritePath = document.getElementById('sprite-path');
    const weaponPath = document.getElementById('weapon-path');
    const projectilePath = document.getElementById('projectile-path');
    
    const options = '<option value="">-- Без спрайта --</option>' +
        availableSprites.map(s => `<option value="game/images/enemy/${s}">${s}</option>`).join('');
    
    spritePath.innerHTML = options;
    weaponPath.innerHTML = options.replace('спрайта', 'оружия');
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
    updateAttackTypeUI();
    
    updateColorPreview();
    updatePreviewScale(1.0);
    
    document.getElementById('editor-title').textContent = 'Новый тип врага';
    
    showEditor();
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
    
    // Preview sprite if available
    if (enemy.sprite_path) {
        const filename = enemy.sprite_path.split('/').pop();
        previewSprite(filename);
    } else {
        closePreview();
    }
    
    showEditor();
    renderEnemyList();
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
            closePreview();
            await loadData();
        } else {
            showToast('Ошибка удаления', 'error');
        }
    } catch (error) {
        showToast('Ошибка удаления', 'error');
        console.error(error);
    }
}

function previewSprite(filename) {
    stopAnimation();
    
    // Загружаем спрайт игрока для сравнения
    loadPlayerSprite();
    
    const img = new Image();
    img.onload = () => {
        currentSpriteImage = img;
        animationFrame = 0;
        animationDirection = 0;
        
        // Получаем масштаб из формы
        const formScale = parseFloat(document.getElementById('sprite-scale').value) || 1.0;
        currentPreviewScale = formScale;
        updatePreviewScale(formScale);
        
        spritePreview.innerHTML = '';
        animationPreview.classList.remove('hidden');
        document.getElementById('close-preview-btn').classList.remove('hidden');
        
        startAnimation();
        updateDirectionLabel();
    };
    img.onerror = () => {
        showToast('Ошибка загрузки спрайта', 'error');
    };
    img.src = `/api/sprites/${filename}`;
}

function loadPlayerSprite() {
    if (playerSpriteImage) return; // Уже загружен
    
    const img = new Image();
    img.onload = () => {
        playerSpriteImage = img;
    };
    // Пытаемся загрузить спрайт игрока
    img.src = '/api/player-sprite';
}

function closePreview() {
    stopAnimation();
    animationPreview.classList.add('hidden');
    document.getElementById('close-preview-btn').classList.add('hidden');
    spritePreview.innerHTML = '<p class="placeholder">Выберите спрайт для предпросмотра</p>';
}

function updatePreviewScale(scale) {
    currentPreviewScale = scale;
    document.getElementById('preview-scale').value = scale;
    document.getElementById('preview-scale-value').textContent = scale.toFixed(1) + 'x';
    document.getElementById('enemy-scale-label').textContent = `Противник (${scale.toFixed(1)}x)`;
}

function applyScaleToForm() {
    document.getElementById('sprite-scale').value = currentPreviewScale.toFixed(1);
    showToast(`Масштаб ${currentPreviewScale.toFixed(1)}x применён к форме`, 'success');
}

function startAnimation() {
    const enemyCanvas = document.getElementById('animation-canvas');
    const playerCanvas = document.getElementById('player-canvas');
    const enemyCtx = enemyCanvas.getContext('2d');
    const playerCtx = playerCanvas.getContext('2d');
    
    const frameSize = 256;
    const baseCanvasSize = 256;
    
    function draw() {
        // Очистка
        enemyCtx.clearRect(0, 0, enemyCanvas.width, enemyCanvas.height);
        playerCtx.clearRect(0, 0, playerCanvas.width, playerCanvas.height);
        
        const sx = (animationFrame % 4) * frameSize;
        const sy = animationDirection * frameSize;
        
        // Отрисовка игрока (всегда 1.0x - полный размер канваса)
        if (playerSpriteImage) {
            playerCtx.drawImage(
                playerSpriteImage,
                sx, sy, frameSize, frameSize,
                0, 0, baseCanvasSize, baseCanvasSize
            );
        } else {
            // Плейсхолдер игрока
            playerCtx.fillStyle = '#3366aa';
            playerCtx.fillRect(28, 28, 200, 200);
            playerCtx.fillStyle = '#5588cc';
            playerCtx.fillRect(78, 78, 100, 100);
            playerCtx.fillStyle = '#ffffff';
            playerCtx.font = '16px sans-serif';
            playerCtx.textAlign = 'center';
            playerCtx.fillText('Игрок', 128, 135);
        }
        
        // Отрисовка противника с масштабом
        if (currentSpriteImage) {
            const scaledSize = baseCanvasSize * currentPreviewScale;
            const offset = (baseCanvasSize - scaledSize) / 2;
            
            enemyCtx.drawImage(
                currentSpriteImage,
                sx, sy, frameSize, frameSize,
                offset, offset, scaledSize, scaledSize
            );
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
    currentSpriteImage = null;
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
    const directions = ['Влево', 'Влево-вверх', 'Вверх', 'Вправо-вверх', 
                        'Вправо', 'Вправо-вниз', 'Вниз', 'Влево-вниз'];
    document.getElementById('direction-label').textContent = 
        `Направление: ${directions[animationDirection]}`;
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
    
    // Sprite select change - preview
    document.getElementById('sprite-path').addEventListener('change', (e) => {
        const value = e.target.value;
        if (value) {
            const filename = value.split('/').pop();
            previewSprite(filename);
        } else {
            closePreview();
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
}

