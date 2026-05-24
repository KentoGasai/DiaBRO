extends Control

enum MenuMode { MAIN, LEVELS, ENEMIES }

@onready var panel: Panel = $Panel
@onready var title_label: Label = $Panel/TitleLabel
@onready var items_list: VBoxContainer = $Panel/Scroll/ItemsList
@onready var hint_label: Label = $Panel/HintLabel

var _world: GameWorld
var _mode := MenuMode.MAIN
var _selected := 0
var _menu_items: Array = []
var _level_items: Array = []
var _enemy_items: Array = []
var _selected_sub := 0


func open_menu(world: GameWorld) -> void:
	_world = world
	_mode = MenuMode.MAIN
	_selected = 0
	_rebuild_main_menu()
	_update_display()


func close_menu() -> void:
	pass


func _rebuild_main_menu() -> void:
	_menu_items = [
		{"text": "Продолжить", "action": "resume"},
		{"text": "Уровни ▶", "action": "levels"},
		{"text": "Противники ▶", "action": "enemies"},
		{"text": _enemy_toggle_text(), "action": "toggle_enemies"},
	]
	if GameState.enemies_enabled:
		_menu_items.append({"text": "Частота спавна: %.1f сек" % GameState.enemy_spawn_frequency, "action": "freq", "setting": true})
		_menu_items.append({"text": "Макс. врагов: %d" % GameState.max_enemies, "action": "max", "setting": true})
	_menu_items.append_array([
		{"text": "Убить всех врагов", "action": "kill"},
		{"text": "Перезапуск", "action": "restart"},
		{"text": "Выход", "action": "quit"},
	])


func _enemy_toggle_text() -> String:
	return "Враги: ВКЛ" if GameState.enemies_enabled else "Враги: ВЫКЛ"


func _rebuild_level_menu() -> void:
	_level_items = []
	for name in LevelController.list_levels():
		var prefix := "● " if GameState.current_level_name == name else ""
		_level_items.append({"text": prefix + name, "name": name})
	_level_items.append({"text": "← Назад", "action": "back"})


func _rebuild_enemy_menu() -> void:
	_enemy_items = [{"text": "◀ Назад", "action": "back"}]
	for id in EnemyRegistry.get_type_ids():
		var data := EnemyRegistry.get_type(id)
		var n: String = data.get("name", id)
		_enemy_items.append({
			"text": "%s (HP:%s DMG:%s)" % [n, data.get("max_health", 30), data.get("damage", 5)],
			"id": id,
		})
	_enemy_items.append({"text": "🔄 Обновить список", "action": "reload"})


func _update_display() -> void:
	for c in items_list.get_children():
		c.queue_free()
	var items: Array = _menu_items
	var sel := _selected
	match _mode:
		MenuMode.LEVELS:
			items = _level_items
			sel = _selected_sub
			title_label.text = "УРОВНИ"
		MenuMode.ENEMIES:
			items = _enemy_items
			sel = _selected_sub
			title_label.text = "ПРОТИВНИКИ"
		_:
			title_label.text = "ПАУЗА"

	for i in range(items.size()):
		var item: Dictionary = items[i]
		var lbl := Label.new()
		var prefix := "> " if i == sel else "  "
		var suffix := " <" if i == sel else ""
		var t: String = item.get("text", "")
		if item.get("setting", false) and i == sel:
			t = "◄ " + t + " ►"
		lbl.text = prefix + t + suffix
		lbl.add_theme_font_size_override("font_size", 22)
		if i == sel:
			lbl.modulate = Color(1, 1, 0.4)
		else:
			lbl.modulate = Color(0.6, 0.6, 0.6)
		items_list.add_child(lbl)

	match _mode:
		MenuMode.MAIN:
			var cur: Dictionary = _menu_items[_selected] if _menu_items.size() > _selected else {}
			hint_label.text = "←/→ настройка | W/S выбор | Enter | ESC" if cur.get("setting") else "W/S | Enter | ESC"
		MenuMode.LEVELS:
			hint_label.text = "Enter загрузить | ← назад"
		MenuMode.ENEMIES:
			hint_label.text = "Enter спавн | ← назад"


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event.is_action_pressed("menu_up") or event.is_action_pressed("move_up"):
		_move_selection(-1)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("menu_down") or event.is_action_pressed("move_down"):
		_move_selection(1)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("menu_confirm"):
		_confirm()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("menu_back") or event.is_action_pressed("pause"):
		_back()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("move_left"):
		_adjust_setting(-1)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("move_right"):
		_adjust_setting(1)
		get_viewport().set_input_as_handled()


func _move_selection(dir: int) -> void:
	match _mode:
		MenuMode.MAIN:
			if _menu_items.is_empty():
				return
			_selected = (_selected + dir) % _menu_items.size()
		MenuMode.LEVELS:
			_selected_sub = (_selected_sub + dir) % _level_items.size()
		MenuMode.ENEMIES:
			_selected_sub = (_selected_sub + dir) % _enemy_items.size()
	_update_display()


func _confirm() -> void:
	match _mode:
		MenuMode.MAIN:
			_execute_main(_menu_items[_selected])
		MenuMode.LEVELS:
			var item: Dictionary = _level_items[_selected_sub]
			if item.get("action") == "back":
				_mode = MenuMode.MAIN
				_update_display()
			elif item.has("name"):
				await _world.load_level(item["name"])
				GameState.set_paused(false)
		MenuMode.ENEMIES:
			var item: Dictionary = _enemy_items[_selected_sub]
			if item.get("action") == "back":
				_mode = MenuMode.MAIN
				_rebuild_main_menu()
				_update_display()
			elif item.get("action") == "reload":
				EnemyRegistry.reload()
				_rebuild_enemy_menu()
				_update_display()
			elif item.has("id"):
				_world.spawn_enemy_type(item["id"], 1)


func _back() -> void:
	if _mode == MenuMode.MAIN:
		GameState.set_paused(false)
	else:
		_mode = MenuMode.MAIN
		_rebuild_main_menu()
		_update_display()


func _execute_main(item: Dictionary) -> void:
	match item.get("action"):
		"resume":
			GameState.set_paused(false)
		"levels":
			_mode = MenuMode.LEVELS
			_selected_sub = 0
			_rebuild_level_menu()
			_update_display()
		"enemies":
			_mode = MenuMode.ENEMIES
			_selected_sub = 0
			_rebuild_enemy_menu()
			_update_display()
		"toggle_enemies":
			GameState.toggle_enemies()
			if not GameState.enemies_enabled:
				_world.kill_all_enemies()
			_rebuild_main_menu()
			_update_display()
		"kill":
			_world.kill_all_enemies()
		"restart":
			GameState.set_paused(false)
			await _world.restart_run()
		"quit":
			get_tree().quit()


func _adjust_setting(dir: int) -> void:
	if _mode != MenuMode.MAIN:
		return
	var item: Dictionary = _menu_items[_selected]
	if not item.get("setting", false):
		return
	match item.get("action"):
		"freq":
			GameState.enemy_spawn_frequency = clampf(
				GameState.enemy_spawn_frequency + dir * -0.5, 0.5, 10.0
			)
		"max":
			GameState.max_enemies = clampi(GameState.max_enemies + dir * 2, 2, 50)
	_rebuild_main_menu()
	_update_display()
