class_name LevelController
extends RefCounted
## Фиксированные уровни: JSON (tiles) или одноразовая генерация (generator).
## Задел RPG: structures, triggers, loot_tables — в JSON уровня.

const LEVELS_DIR := "res://data/levels/"

var name: String = "wilderness"
var width: int = 64
var height: int = 64
var tiles: Dictionary = {}
var spawn_points: Array = []
var structures: Array = []
var player_spawn: Vector2 = Vector2(32, 32)
var bounds_min: Vector2 = Vector2(0.5, 0.5)
var bounds_max: Vector2 = Vector2(62.5, 62.5)


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
	width = int(data.get("width", 64))
	height = int(data.get("height", 64))
	_apply_bounds()

	var src := str(data.get("source", "tiles"))
	if src == "generator":
		var gen_cfg: Dictionary = data.get("generator", {})
		var p_seed: int = int(gen_cfg.get("seed", 0))
		var preset: String = str(gen_cfg.get("preset", "overworld"))
		var generated := LevelGenerator.generate_level(width, height, p_seed, preset)
		tiles = generated.get("tiles", {})
		var gen_spawns: Array = generated.get("spawn_points", [])
		spawn_points.append_array(gen_spawns)
	else:
		_load_tiles_from_json(data.get("tiles", {}))

	if data.has("player_spawn"):
		var ps: Array = data["player_spawn"]
		if ps.size() >= 2:
			player_spawn = Vector2(float(ps[0]), float(ps[1]))

	if data.has("spawn_points"):
		for sp in data["spawn_points"]:
			if typeof(sp) == TYPE_DICTIONARY:
				spawn_points.append(sp)

	if data.has("structures"):
		structures = data["structures"]

	_filter_spawn_away_from_player()
	_compute_bounds_from_tiles()
	return true


func _load_tiles_from_json(raw: Variant) -> void:
	if typeof(raw) != TYPE_DICTIONARY:
		return
	for key in raw:
		var parts: PackedStringArray = str(key).split(",")
		if parts.size() >= 2:
			tiles[Vector2i(int(parts[0]), int(parts[1]))] = raw[key]


func _apply_bounds() -> void:
	bounds_min = Vector2(0.5, 0.5)
	bounds_max = Vector2(float(width) - 0.5, float(height) - 0.5)


func _compute_bounds_from_tiles() -> void:
	if tiles.is_empty():
		_apply_bounds()
		return
	var min_x := width
	var min_y := height
	var max_x := 0
	var max_y := 0
	for pos: Vector2i in tiles:
		min_x = mini(min_x, pos.x)
		min_y = mini(min_y, pos.y)
		max_x = maxi(max_x, pos.x)
		max_y = maxi(max_y, pos.y)
	bounds_min = Vector2(float(min_x) + 0.5, float(min_y) + 0.5)
	bounds_max = Vector2(float(max_x) + 0.5, float(max_y) + 0.5)


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
