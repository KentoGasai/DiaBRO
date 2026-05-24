class_name LevelController
extends RefCounted
## Фиксированные уровни: JSON (tiles) или одноразовая генерация (generator).

const LEVELS_DIR := "res://data/levels/"

var name: String = "wilderness"
var width: int = 64
var height: int = 64
var tiles: Dictionary = {}
var spawn_points: Array = []
var structures: Array = []
var player_spawn: Vector2 = Vector2(32, 32)
var bounds_min: Vector2 = Vector2(0.5, 0.5)
var bounds_max: Vector2 = Vector2(63.5, 63.5)


func _init(level_name: String = "wilderness") -> void:
	load_level(level_name)


func load_level(level_name: String) -> bool:
	tiles.clear()
	spawn_points.clear()
	structures.clear()
	name = level_name

	var path := LEVELS_DIR + level_name + ".json"
	if not FileAccess.file_exists(path):
		push_warning("Level not found: %s" % path)
		return false

	var f := FileAccess.open(path, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if typeof(data) != TYPE_DICTIONARY:
		return false

	name = str(data.get("name", level_name))
	width = maxi(1, int(data.get("width", 64)))
	height = maxi(1, int(data.get("height", 64)))
	_apply_bounds()

	var src := str(data.get("source", "tiles"))
	if src == "generator":
		var gen_cfg: Dictionary = data.get("generator", {})
		var p_seed: int = int(gen_cfg.get("seed", 0))
		var preset: String = str(gen_cfg.get("preset", "overworld"))
		var generated := LevelGenerator.generate_level(width, height, p_seed, preset)
		tiles = generated.get("tiles", {})
		spawn_points.append_array(generated.get("spawn_points", []))
	else:
		_load_tiles_from_json(data.get("tiles", {}))
		_fill_missing_tiles()

	player_spawn = Vector2(
		floorf(float(width) * 0.5),
		floorf(float(height) * 0.5)
	)
	if data.has("player_spawn"):
		var ps: Array = data["player_spawn"]
		if ps.size() >= 2:
			player_spawn = Vector2(float(ps[0]), float(ps[1]))
	player_spawn = get_spawn_position()

	if data.has("spawn_points"):
		for sp in data["spawn_points"]:
			if typeof(sp) == TYPE_DICTIONARY:
				spawn_points.append(sp)

	if data.has("structures"):
		structures = data["structures"]

	_filter_spawn_away_from_player()
	return true


func _load_tiles_from_json(raw: Variant) -> void:
	if typeof(raw) != TYPE_DICTIONARY:
		return
	for key in raw:
		var parts: PackedStringArray = str(key).split(",")
		if parts.size() >= 2:
			tiles[Vector2i(int(parts[0]), int(parts[1]))] = raw[key]


func _fill_missing_tiles() -> void:
	var default_tile := {"tileset": "grass_green_128x64", "tile": 0}
	for x in range(width):
		for y in range(height):
			var pos := Vector2i(x, y)
			if not tiles.has(pos):
				tiles[pos] = default_tile


func _apply_bounds() -> void:
	# Внутренний отступ от каменной кромки (генератор ставит stone на x=0/y=0/w-1/h-1)
	var margin := 2.0
	bounds_min = Vector2(margin, margin)
	bounds_max = Vector2(float(width) - 1.0 - margin, float(height) - 1.0 - margin)


func get_spawn_position() -> Vector2:
	return clamp_world_pos(player_spawn)


func _filter_spawn_away_from_player() -> void:
	var filtered: Array = []
	var px := player_spawn.x
	var py := player_spawn.y
	for sp in spawn_points:
		if typeof(sp) != TYPE_DICTIONARY:
			continue
		var sx: float = float(sp.get("x", 0))
		var sy: float = float(sp.get("y", 0))
		var dx := sx - px
		var dy := sy - py
		if dx * dx + dy * dy >= 64.0:
			filtered.append(sp)
	spawn_points = filtered


static func list_levels() -> Array:
	var levels: Array = []
	var dir := DirAccess.open(LEVELS_DIR)
	if dir:
		dir.list_dir_begin()
		var fn := dir.get_next()
		while fn != "":
			if fn.ends_with(".json"):
				levels.append(fn.get_basename())
			fn = dir.get_next()
		dir.list_dir_end()
	levels.sort()
	if "wilderness" in levels:
		levels.erase("wilderness")
		levels.insert(0, "wilderness")
	return levels


func get_tile_data(tx: int, ty: int) -> Dictionary:
	return tiles.get(Vector2i(tx, ty), {})


func clamp_world_pos(pos: Vector2) -> Vector2:
	return pos.clamp(bounds_min, bounds_max)
