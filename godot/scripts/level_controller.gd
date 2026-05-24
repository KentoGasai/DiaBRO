class_name LevelController
extends RefCounted
## Загрузка уровней: procedural + JSON (порт game/level.py)

const LEVELS_DIR := "res://data/levels/"
const TILE_W := 128
const TILE_H := 64
const MAX_CACHED_TILES := 1800
const PROC_LOAD_RADIUS := 22.0

var name: String = "procedural"
var procedural: bool = true
var procedural_generator: ProceduralGenerator = null
var tiles: Dictionary = {}
var _last_update_pos := Vector2(INF, INF)


func _init(level_name: String = "procedural") -> void:
	load_level(level_name)


func load_level(level_name: String) -> bool:
	tiles.clear()
	_last_update_pos = Vector2(INF, INF)
	name = level_name
	if level_name == "procedural":
		procedural = true
		procedural_generator = ProceduralGenerator.new()
		return true
	procedural = false
	procedural_generator = null
	var path := LEVELS_DIR + level_name + ".json"
	if not FileAccess.file_exists(path):
		push_warning("Level not found: %s" % path)
		return false
	var f := FileAccess.open(path, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if typeof(data) != TYPE_DICTIONARY:
		return false
	name = data.get("name", level_name)
	for key in data.get("tiles", {}):
		var parts: PackedStringArray = str(key).split(",")
		if parts.size() >= 2:
			tiles[Vector2i(int(parts[0]), int(parts[1]))] = data["tiles"][key]
	return true


static func list_levels() -> Array:
	var levels: Array = ["procedural"]
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
	return levels


func update_procedural(center: Vector2, force: bool = false, load_radius: float = -1.0) -> void:
	if not procedural or procedural_generator == null:
		return
	if not force:
		if center.distance_squared_to(_last_update_pos) < 4.0:
			return
	_last_update_pos = center
	var radius: float = load_radius if load_radius > 0.0 else PROC_LOAD_RADIUS
	var new_tiles := procedural_generator.get_tiles_in_radius(
		center.x, center.y, radius
	)
	for pos in new_tiles:
		tiles[pos] = new_tiles[pos]
	if tiles.size() > MAX_CACHED_TILES:
		_trim_tiles(center, radius + 18.0)
	procedural_generator.trim_chunks(center, 22)


func _trim_tiles(center: Vector2, keep_radius: float) -> void:
	var keep_sq: float = keep_radius * keep_radius
	var sorted: Array = []
	for pos: Vector2i in tiles:
		var dx: float = pos.x - center.x
		var dy: float = pos.y - center.y
		var d2: float = dx * dx + dy * dy
		if d2 <= keep_sq:
			continue
		sorted.append({"pos": pos, "d2": d2})
	if sorted.is_empty():
		return
	sorted.sort_custom(func(a, b): return a["d2"] > b["d2"])
	var remove_n: int = tiles.size() - MAX_CACHED_TILES
	for i in range(mini(remove_n, sorted.size())):
		tiles.erase(sorted[i]["pos"])


func get_tile_data(tx: int, ty: int) -> Dictionary:
	if procedural and procedural_generator:
		return procedural_generator.get_tile(tx, ty)
	return tiles.get(Vector2i(tx, ty), {})
