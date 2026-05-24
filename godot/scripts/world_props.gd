extends Node2D
## Спрайты окружения Kenney (лавки, стены, декор) поверх тайлмапа.

const PROPS_PER_FRAME := 80

var _tile_map: TileMapLayer


func setup(p_level: LevelController, tile_map: TileMapLayer, on_progress: Callable = Callable()) -> void:
	_tile_map = tile_map
	await build_props(p_level.props, on_progress)


func clear_props() -> void:
	for c in get_children():
		c.queue_free()


func build_props(props: Array, on_progress: Callable = Callable()) -> void:
	clear_props()
	if props.is_empty() or _tile_map == null:
		_report(on_progress, 1.0, "Окружение: нет объектов")
		return

	var total := props.size()
	for i in range(total):
		var data: Dictionary = props[i]
		_spawn_prop(data)
		if (i + 1) % PROPS_PER_FRAME == 0 or i == total - 1:
			_report(on_progress, float(i + 1) / float(total), "Окружение %d / %d" % [i + 1, total])
			await get_tree().process_frame

	_report(on_progress, 1.0, "Окружение готово")


func _spawn_prop(data: Dictionary) -> void:
	var pack := str(data.get("pack", ""))
	var base := str(data.get("base", ""))
	var facing := str(data.get("facing", "E"))
	var tx := int(data.get("x", 0))
	var ty := int(data.get("y", 0))

	var path := KenneyTileCatalog.texture_path(pack, base, facing)
	if not FileAccess.file_exists(path):
		return

	var tex: Texture2D = load(path) as Texture2D
	if tex == null:
		return

	var spr := Sprite2D.new()
	spr.texture = tex
	spr.centered = false
	spr.offset = Vector2(
		-KenneyTileCatalog.TEXTURE_ORIGIN.x,
		-KenneyTileCatalog.TEXTURE_ORIGIN.y
	)
	spr.position = IsoMath.tile_cell_screen_on_layer(_tile_map, tx, ty)
	spr.z_index = int(spr.position.y)
	add_child(spr)


func _report(on_progress: Callable, ratio: float, message: String) -> void:
	if on_progress.is_valid():
		on_progress.call(ratio, message)
