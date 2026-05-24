extends TileMapLayer
## TileMapLayer — полная сборка уровня один раз при загрузке.

const TEXTURES_DIR := "res://assets/sprites/textures/"
const TILE_W := 128
const TILE_H := 64
const CELLS_PER_FRAME := 2000

var level: LevelController
var _tile_lookup: Dictionary = {}


func _ready() -> void:
	_build_tileset()


func setup(p_level: LevelController) -> void:
	level = p_level
	await build_from_level()


func build_from_level() -> void:
	clear()
	if level == null or level.tiles.is_empty():
		return

	var order: Array = level.tiles.keys()
	order.sort_custom(func(a, b):
		var pa: Vector2i = a
		var pb: Vector2i = b
		if pa.x + pa.y != pb.x + pb.y:
			return pa.x + pa.y < pb.x + pb.y
		return pa.x < pb.x
	)

	var placed := 0
	for pos_variant in order:
		var pos: Vector2i = pos_variant
		_place_cell(pos, level.tiles[pos])
		placed += 1
		if placed % CELLS_PER_FRAME == 0:
			await get_tree().process_frame


func _place_cell(pos: Vector2i, data: Dictionary) -> void:
	var key := _tile_key(data)
	var info: Dictionary = _tile_lookup.get(key, {})
	if info.is_empty():
		return
	set_cell(pos, int(info["source_id"]), info["atlas"] as Vector2i)


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
			var tex_name := fn.get_basename()
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
						_tile_lookup["%s:%d" % [tex_name, row * cols + col]] = {
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
