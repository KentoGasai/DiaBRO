extends TileMapLayer
## TileMapLayer — Kenney isometric tiles, сборка уровня при загрузке.

const CELLS_PER_FRAME := 400

var level: LevelController
var _tile_lookup: Dictionary = {}


func _ready() -> void:
	pass


func setup(p_level: LevelController, on_progress: Callable = Callable()) -> void:
	level = p_level
	await build_from_level(on_progress)


func build_from_level(on_progress: Callable = Callable()) -> void:
	clear()
	_tile_lookup.clear()
	if level == null or level.tiles.is_empty():
		_report(on_progress, 1.0, "Нет данных уровня")
		return

	_report(on_progress, 0.0, "Подготовка тайлсета Kenney...")
	await get_tree().process_frame
	_build_tileset_from_level()
	await get_tree().process_frame

	var order: Array = level.tiles.keys()
	order.sort_custom(func(a, b):
		var pa: Vector2i = a
		var pb: Vector2i = b
		if pa.x + pa.y != pb.x + pb.y:
			return pa.x + pa.y < pb.x + pb.y
		return pa.x < pb.x
	)

	var total := order.size()
	var placed := 0
	var skipped := 0
	for i in range(total):
		var pos: Vector2i = order[i]
		if _place_cell(pos, level.tiles[pos]):
			placed += 1
		else:
			skipped += 1
		if (i + 1) % CELLS_PER_FRAME == 0 or i == total - 1:
			var ratio := float(i + 1) / float(total)
			_report(on_progress, ratio, "Сборка карты %d / %d" % [i + 1, total])
			await get_tree().process_frame

	if skipped > 0:
		push_warning("TileWorld: не размещено тайлов: %d из %d" % [skipped, total])

	_align_to_iso_space()
	_report(on_progress, 1.0, "Готово")


func _report(on_progress: Callable, ratio: float, message: String) -> void:
	if on_progress.is_valid():
		on_progress.call(ratio, message)


func _align_to_iso_space() -> void:
	position = Vector2.ZERO
	var cx := level.width / 2
	var cy := level.height / 2
	transform = IsoMath.fit_tilemap_to_iso(self, cx, cy)


func _place_cell(pos: Vector2i, data: Dictionary) -> bool:
	var key := KenneyTileCatalog.tile_key(data)
	var info: Dictionary = _tile_lookup.get(key, {})
	if info.is_empty():
		return false
	set_cell(pos, int(info["source_id"]), info["atlas"] as Vector2i)
	return true


func _build_tileset_from_level() -> void:
	var ts := TileSet.new()
	ts.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
	ts.tile_size = KenneyTileCatalog.TILE_SIZE
	ts.tile_layout = TileSet.TILE_LAYOUT_DIAMOND_RIGHT

	var keys: Dictionary = {}
	for pos_variant in level.tiles:
		var data: Dictionary = level.tiles[pos_variant]
		var key := KenneyTileCatalog.tile_key(data)
		if not key.is_empty():
			keys[key] = data

	var source_id := 0
	for key in keys:
		var data: Dictionary = keys[key]
		if _register_kenney_tile(ts, data, source_id):
			source_id += 1

	tile_set = ts


func _register_kenney_tile(ts: TileSet, data: Dictionary, source_id: int) -> bool:
	var pack := str(data.get("pack", ""))
	var base := str(data.get("base", ""))
	var facing := str(data.get("facing", "E"))
	var path := KenneyTileCatalog.texture_path(pack, base, facing)
	if not FileAccess.file_exists(path):
		push_warning("Kenney tile missing: %s" % path)
		return false

	var tex: Texture2D = load(path) as Texture2D
	if tex == null:
		return false

	var atlas := TileSetAtlasSource.new()
	atlas.texture = tex
	atlas.texture_region_size = KenneyTileCatalog.TEXTURE_SIZE
	var ac := Vector2i.ZERO
	if not atlas.has_tile(ac):
		atlas.create_tile(ac)
	var td := atlas.get_tile_data(ac, 0)
	if td:
		td.texture_origin = KenneyTileCatalog.TEXTURE_ORIGIN

	ts.add_source(atlas, source_id)
	var lookup_key := KenneyTileCatalog.tile_key(data)
	_tile_lookup[lookup_key] = {"source_id": source_id, "atlas": ac}
	return true
