extends TileMapLayer
## TileMapLayer: синхронизация видимой зоны без «хвоста» от кадровой очереди.
## Чанки кэшируются в ProceduralGenerator; на карте — гистерезис (не стираем сразу).

const TEXTURES_DIR := "res://assets/sprites/textures/"
const TILE_W := 128
const TILE_H := 64

const LOAD_MARGIN := 8.0
const KEEP_EXTRA := 20.0
const MAX_LOAD_RADIUS := 34.0
const UPDATE_MOVE_SQ := 4.0
const PREFETCH_DIST := 7.0

var level: LevelController
var _tile_lookup: Dictionary = {}
var _active_cells: Dictionary = {}
var _last_sync_center := Vector2(INF, INF)


func _ready() -> void:
	_build_tileset()


func setup(p_level: LevelController) -> void:
	level = p_level
	reset_streaming()
	refresh_around(Vector2.ZERO, true, Vector2(1920, 1080))


func reset_streaming() -> void:
	clear()
	_active_cells.clear()
	_last_sync_center = Vector2(INF, INF)


func refresh_around(
	center: Vector2,
	force: bool = false,
	screen_size: Vector2 = Vector2(1920, 1080),
	velocity: Vector2 = Vector2.ZERO
) -> void:
	if level == null:
		return

	var vis_r: float = IsoMath.visible_tile_radius(screen_size)
	var load_r: float = minf(vis_r + LOAD_MARGIN, MAX_LOAD_RADIUS)
	var keep_r: float = load_r + KEEP_EXTRA

	var sample_center := center
	if velocity.length_squared() > 0.5:
		sample_center = center + velocity.normalized() * minf(velocity.length() * 0.4, PREFETCH_DIST)

	if level.procedural:
		level.update_procedural(sample_center, force, load_r)

	if force or center.distance_squared_to(_last_sync_center) >= UPDATE_MOVE_SQ:
		_last_sync_center = center
		_sync_tiles(center, sample_center, load_r, keep_r, force)


func _sync_tiles(center: Vector2, sample_center: Vector2, load_r: float, keep_r: float, force: bool) -> void:
	var wanted := _build_wanted(sample_center, load_r, force)
	var keep_sq: float = keep_r * keep_r
	var load_sq: float = load_r * load_r

	var to_erase: Array[Vector2i] = []
	for cell: Vector2i in _active_cells:
		var dx: float = float(cell.x) - center.x
		var dy: float = float(cell.y) - center.y
		if dx * dx + dy * dy > keep_sq:
			to_erase.append(cell)
	for cell in to_erase:
		erase_cell(cell)
		_active_cells.erase(cell)

	var to_place: Array = []
	for pos_variant in wanted:
		var pos: Vector2i = pos_variant
		var dx: float = float(pos.x) - center.x
		var dy: float = float(pos.y) - center.y
		var d2: float = dx * dx + dy * dy
		if d2 > load_sq:
			continue
		var data: Dictionary = wanted[pos]
		var key := _tile_key(data)
		if key.is_empty():
			continue
		if _active_cells.get(pos) == key:
			continue
		to_place.append({"pos": pos, "data": data, "d2": d2})

	to_place.sort_custom(func(a, b): return a["d2"] < b["d2"])
	for item in to_place:
		_place_cell(item["pos"], item["data"])


func _build_wanted(sample_center: Vector2, load_r: float, force: bool) -> Dictionary:
	var wanted: Dictionary = {}
	var radius_sq: float = load_r * load_r

	if level.procedural and level.procedural_generator:
		if force or level.tiles.is_empty():
			_merge_generated(sample_center, load_r, wanted)
		else:
			_fill_from_level_cache(sample_center, radius_sq, wanted)
			if wanted.size() < int(radius_sq * 0.2):
				_merge_generated(sample_center, load_r, wanted)
	else:
		_fill_from_level_cache(sample_center, radius_sq, wanted)

	return wanted


func _fill_from_level_cache(sample_center: Vector2, radius_sq: float, wanted: Dictionary) -> void:
	for pos_variant in level.tiles:
		var pos: Vector2i = pos_variant
		var dx: float = pos.x - sample_center.x
		var dy: float = pos.y - sample_center.y
		if dx * dx + dy * dy <= radius_sq:
			wanted[pos] = level.tiles[pos]


func _merge_generated(sample_center: Vector2, load_r: float, wanted: Dictionary) -> void:
	var generated: Dictionary = level.procedural_generator.get_tiles_in_radius(
		sample_center.x, sample_center.y, load_r
	)
	for pos in generated:
		level.tiles[pos] = generated[pos]
		wanted[pos] = generated[pos]


func _place_cell(pos: Vector2i, data: Dictionary) -> void:
	var key := _tile_key(data)
	var info: Dictionary = _tile_lookup.get(key, {})
	if info.is_empty():
		return
	set_cell(pos, int(info["source_id"]), info["atlas"] as Vector2i)
	_active_cells[pos] = key


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
