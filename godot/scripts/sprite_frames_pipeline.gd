class_name SpriteFramesPipeline
extends RefCounted
## Сборка SpriteFrames из PNG и сохранение .tres для редактора Godot (SpriteFrames panel).

const FRAMES_DIR := "res://assets/sprites/frames/"
const ENEMY_FRAMES_DIR := FRAMES_DIR + "enemies/"
const PLAYER_FRAMES_PATH := FRAMES_DIR + "player.tres"

const PLAYER_CHAR := "res://assets/sprites/character/male_unarmored.png"
const PLAYER_WEAPON := "res://assets/sprites/weapon/male_longsword.png"
const ENEMY_TYPES_PATH := "res://data/enemy_types.json"


static func has_valid_frames(frames: SpriteFrames) -> bool:
	return frames != null and not frames.get_animation_names().is_empty()


static func save_frames(frames: SpriteFrames, resource_path: String) -> bool:
	if frames == null:
		return false
	var dir := resource_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	var err := ResourceSaver.save(frames, resource_path)
	if err != OK:
		push_error("SpriteFramesPipeline: не удалось сохранить %s (err %s)" % [resource_path, err])
		return false
	return true


static func enemy_frames_path(type_id: String) -> String:
	return ENEMY_FRAMES_DIR + type_id + ".tres"


static func build_player_frames() -> SpriteFrames:
	return SpriteSheetBuilder.build_frames(PLAYER_CHAR, PLAYER_WEAPON, 1.0)


static func build_enemy_frames(data: Dictionary) -> SpriteFrames:
	var sp := str(data.get("sprite_path", ""))
	var path := sp
	if path.is_empty() or not path.begins_with("res://"):
		path = SpriteSheetBuilder.resolve_asset_path(sp)
	var weapon := str(data.get("weapon_path", ""))
	if weapon != "" and not weapon.begins_with("res://"):
		weapon = SpriteSheetBuilder.resolve_asset_path(weapon)
	var scale := float(data.get("sprite_scale", 1.0))
	return SpriteSheetBuilder.build_frames(path, weapon, scale)


static func load_player_frames() -> SpriteFrames:
	if ResourceLoader.exists(PLAYER_FRAMES_PATH):
		var res: SpriteFrames = load(PLAYER_FRAMES_PATH) as SpriteFrames
		if has_valid_frames(res):
			return res
	return build_player_frames()


static func load_enemy_frames(type_id: String, data: Dictionary) -> SpriteFrames:
	var path := enemy_frames_path(type_id)
	if ResourceLoader.exists(path):
		var res: SpriteFrames = load(path) as SpriteFrames
		if has_valid_frames(res):
			return res
	return build_enemy_frames(data)


static func regenerate_player() -> void:
	var frames := build_player_frames()
	if save_frames(frames, PLAYER_FRAMES_PATH):
		print("SpriteFramesPipeline: %s" % PLAYER_FRAMES_PATH)


static func regenerate_enemy(type_id: String, data: Dictionary) -> void:
	var frames := build_enemy_frames(data)
	var path := enemy_frames_path(type_id)
	if save_frames(frames, path):
		print("SpriteFramesPipeline: %s" % path)


## Читает enemy_types.json напрямую (работает в @tool / EditorScript без autoload).
static func load_enemy_types_for_editor() -> Dictionary:
	var types: Dictionary = {}
	if FileAccess.file_exists(ENEMY_TYPES_PATH):
		var f := FileAccess.open(ENEMY_TYPES_PATH, FileAccess.READ)
		if f:
			var parsed = JSON.parse_string(f.get_as_text())
			if typeof(parsed) == TYPE_DICTIONARY:
				for id in parsed:
					types[id] = _normalize_enemy_entry(parsed[id])
	return types


static func _normalize_enemy_entry(data: Variant) -> Dictionary:
	if typeof(data) != TYPE_DICTIONARY:
		return {}
	var d: Dictionary = (data as Dictionary).duplicate(true)
	if d.get("color") is Array and d["color"].size() >= 3:
		d["color"] = Color(
			float(d["color"][0]) / 255.0,
			float(d["color"][1]) / 255.0,
			float(d["color"][2]) / 255.0
		)
	for key in ["sprite_path", "weapon_path", "projectile_path"]:
		var raw: String = str(d.get(key, ""))
		if not raw.is_empty():
			d[key] = SpriteSheetBuilder.resolve_asset_path(raw)
	return d


static func _enemy_sprite_resolved_path(data: Dictionary) -> String:
	var sp := str(data.get("sprite_path", ""))
	if sp.is_empty():
		return ""
	if sp.begins_with("res://"):
		return sp
	return SpriteSheetBuilder.resolve_asset_path(sp)


static func regenerate_all_enemies() -> void:
	var types := load_enemy_types_for_editor()
	for type_id in types:
		var data: Dictionary = types[type_id]
		var sprite_path := _enemy_sprite_resolved_path(data)
		if sprite_path.is_empty() or not ResourceLoader.exists(sprite_path):
			push_warning("SpriteFramesPipeline: пропуск '%s' — нет спрайта" % type_id)
			continue
		regenerate_enemy(type_id, data)


static func regenerate_all() -> void:
	DirAccess.make_dir_recursive_absolute(FRAMES_DIR)
	DirAccess.make_dir_recursive_absolute(ENEMY_FRAMES_DIR)
	regenerate_player()
	regenerate_all_enemies()
	print("SpriteFramesPipeline: готово. Откройте .tres в панели SpriteFrames.")
