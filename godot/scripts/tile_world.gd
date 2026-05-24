extends TileMapLayer
## TileMapLayer + потоковая подгрузка (бюджет кадра), кэш чанков в ProceduralGenerator

const TEXTURES_DIR := "res://assets/sprites/textures/"
const TILE_W := 128
const TILE_H := 64

const TILES_PER_FRAME := 120
const TILES_PER_FRAME_URGENT := 280
const RECOMPUTE_MOVE_SQ := 9.0  # ~3 тайла — чаще пересчёт, но без лагового пика
const URGENT_QUEUE := 600

var level: LevelController
var _tile_lookup: Dictionary = {}
var _active_cells: Dictionary = {}
var _wanted_center := Vector2(INF, INF)
var _pending_sets: Array = []
var _pending_erases: Array[Vector2i] = []


func _ready() -> void:
	_build_tileset()


func setup(p_level: LevelController) -> void:
	level = p_level
	reset_streaming()
	var vp := get_viewport_rect().size
	refresh_around(Vector2.ZERO, true, vp)


func reset_streaming() -> void:
	clear()
	_active_cells.clear()
	_wanted_center = Vector2(INF, INF)
	_pending_sets.clear()
	_pending_erases.clear()


func _process(_delta: float) -> void:
	_apply_stream_budget()


func refresh_around(center: Vector2, force: bool = false, screen_size: Vector2 = Vector2(1920, 1080)) -> void:
	if level == null:
		return
	var load_radius: float = IsoMath.visible_tile_radius(screen_size)
	if level.procedural:
		level.update_procedural(center, force, load_radius)

	var need_requeue := force
	if not need_requeue:
		need_requeue = center.distance_squared_to(_wanted_center) >= RECOMPUTE_MOVE_SQ
	var queue_idle := _pending_sets.is_empty() and _pending_erases.is_empty()
	if need_requeue or queue_idle:
		_requeue_diff(center, screen_size, force)


func _requeue_diff(center: Vector2, screen_size: Vector2, force: bool) -> void:
	_wanted_center = center
	if force:
		_pending_sets.clear()
		_pending_erases.clear()

	var load_radius: float = IsoMath.visible_tile_radius(screen_size)
	var wanted := _collect_wanted(center, load_radius, force)

	var erase_set: Dictionary = {}
	for e: Vector2i in _pending_erases:
		erase_set[e] = true
	var set_pos: Dictionary = {}
	for item: Dictionary in _pending_sets:
		set_pos[item["pos"]] = true

	for cell: Vector2i in _active_cells:
		if not wanted.has(cell) and not erase_set.has(cell):
			_pending_erases.append(cell)
			erase_set[cell] = true

	for pos_variant in wanted:
		var pos: Vector2i = pos_variant
		var data: Dictionary = wanted[pos]
		var key := _tile_key(data)
		if key.is_empty():
			continue
		if _active_cells.get(pos) == key:
			continue
		if set_pos.has(pos):
			continue
		_pending_sets.append({"pos": pos, "data": data})
		set_pos[pos] = true



func _collect_wanted(center: Vector2, load_radius: float, force: bool) -> Dictionary:
	var wanted: Dictionary = {}
	var radius_sq: float = load_radius * load_radius

	if level.procedural and level.procedural_generator:
		if force or level.tiles.is_empty():
			var generated := level.procedural_generator.get_tiles_in_radius(
				center.x, center.y, load_radius
			)
			for pos in generated:
				level.tiles[pos] = generated[pos]

	for pos_variant in level.tiles:
		var pos: Vector2i = pos_variant
		var dx: float = pos.x - center.x
		var dy: float = pos.y - center.y
		if dx * dx + dy * dy <= radius_sq:
			wanted[pos] = level.tiles[pos]

	# Край экрана: в кэше мало тайлов — догружаем чанки в level.tiles
	if level.procedural and level.procedural_generator:
		var expected_min := int(radius_sq * 0.12)
		if wanted.size() < expected_min:
			level.update_procedural(center, true, load_radius)
			for pos_variant in level.tiles:
				var pos: Vector2i = pos_variant
				var dx: float = pos.x - center.x
				var dy: float = pos.y - center.y
				if dx * dx + dy * dy <= radius_sq:
					wanted[pos] = level.tiles[pos]

	return wanted


func _apply_stream_budget() -> void:
	var queue_size := _pending_sets.size() + _pending_erases.size()
	var budget := TILES_PER_FRAME_URGENT if queue_size > URGENT_QUEUE else TILES_PER_FRAME

	while budget > 0 and not _pending_erases.is_empty():
		var cell: Vector2i = _pending_erases.pop_back()
		if _active_cells.has(cell):
			erase_cell(cell)
			_active_cells.erase(cell)
		budget -= 1

	while budget > 0 and not _pending_sets.is_empty():
		var item: Dictionary = _pending_sets.pop_back()
		var pos: Vector2i = item["pos"]
		var data: Dictionary = item["data"]
		var key := _tile_key(data)
		var info: Dictionary = _tile_lookup.get(key, {})
		if info.is_empty():
			budget -= 1
			continue
		set_cell(pos, int(info["source_id"]), info["atlas"] as Vector2i)
		_active_cells[pos] = key
		budget -= 1


func _build_tileset() -> void:
	_tile_lookup.clear()
	var ts := TileSet.new()
	ts.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
	ts.tile_size = Vector2i(TILE_W, TILE_H)
	ts.tile_layout = TileSet.TILE_LAYOUT_STACKED

	var dir := DirAccess.open(TEXTURES_DIR)
	if not dir:
		push_warning("Textures dir missing: %s" % TEXTURES_DIR)
		tile_set = ts
		return

	dir.list_dir_begin()
	var fn := dir.get_next()
	var source_id := 0
	while fn != "":
		if fn.ends_with(".png"):
			var name := fn.get_basename()
			var tex: Texture2D = load(TEXTURES_DIR + fn)
			if tex != null:
				var img := tex.get_image()
				var cols: int = maxi(1, img.get_width() / TILE_W)
				var rows: int = maxi(1, img.get_height() / TILE_H)
				var atlas := TileSetAtlasSource.new()
				atlas.texture = tex
				atlas.texture_region_size = Vector2i(TILE_W, TILE_H)
				for row in range(rows):
					for col in range(cols):
						var ac := Vector2i(col, row)
						if not atlas.has_tile(ac):
							atlas.create_tile(ac)
						_tile_lookup["%s:%d" % [name, row * cols + col]] = {
							"source_id": source_id,
							"atlas": ac,
						}
				ts.add_source(atlas, source_id)
				source_id += 1
		fn = dir.get_next()
	dir.list_dir_end()
	tile_set = ts


func _tile_key(data: Dictionary) -> String:
	var ts_name := str(data.get("tileset", ""))
	if ts_name.is_empty():
		return ""
	return "%s:%d" % [ts_name, int(data.get("tile", 0))]
