extends Control

const SIZE := 150
const RADIUS := 200.0
const TILE_PX := 5

var _world: GameWorld
var _refresh_accum := 0.0
const REFRESH_INTERVAL := 0.1


func _ready() -> void:
	custom_minimum_size = Vector2(SIZE, SIZE)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true


func set_world(world: GameWorld) -> void:
	_world = world


func refresh(world: GameWorld = null) -> void:
	if world:
		_world = world
	queue_redraw()


func _process(delta: float) -> void:
	if _world == null:
		return
	_refresh_accum += delta
	if _refresh_accum >= REFRESH_INTERVAL:
		_refresh_accum = 0.0
		queue_redraw()


func _draw() -> void:
	var world: GameWorld = _world
	if world == null or not is_instance_valid(world):
		return
	var player: GamePlayer = world.player
	if player == null:
		return

	draw_rect(Rect2(Vector2.ZERO, Vector2(SIZE, SIZE)), Color(0, 0, 0, 0.86))
	draw_rect(Rect2(Vector2.ZERO, Vector2(SIZE, SIZE)), Color.WHITE, false, 2.0)

	var center := Vector2(SIZE / 2.0, SIZE / 2.0)
	var pp: Vector2 = player.world_position
	var fog: FogOfWar = world.fog
	var level: LevelController = world.level
	var explored: Dictionary = fog.explored_tiles
	var visible: Dictionary = fog.visible_tiles
	var radius_sq: float = RADIUS * RADIUS

	# Как в Pygame: только кэш level.tiles рядом с игроком + explored
	var candidates: Array = []
	for pos_variant in level.tiles:
		var pos: Vector2i = pos_variant
		if not explored.has(pos):
			continue
		var dx: float = pos.x - pp.x
		var dy: float = pos.y - pp.y
		var d2: float = dx * dx + dy * dy
		if d2 > radius_sq:
			continue
		candidates.append({"pos": pos, "data": level.tiles[pos], "d2": d2})

	if candidates.size() > 500:
		candidates.sort_custom(func(a, b): return a["d2"] < b["d2"])
		candidates.resize(500)

	for item in candidates:
		var pos: Vector2i = item["pos"]
		var data: Dictionary = item["data"]
		var dx: float = pos.x - pp.x
		var dy: float = pos.y - pp.y
		var iso_x: float = (dx - dy) * TILE_PX / 2.0
		var iso_y: float = (dx + dy) * TILE_PX / 4.0
		var px: float = center.x + iso_x
		var py: float = center.y + iso_y
		if px < 0.0 or px >= SIZE or py < 0.0 or py >= SIZE:
			continue
		var base: Color = _tile_color(str(data.get("tileset", "")))
		if visible.has(pos):
			_draw_mini_tile(px, py, base, 1.0)
		else:
			_draw_mini_tile(px, py, base.darkened(0.5), 0.7)

	draw_circle(center, 4, Color(0.39, 0.7, 1.0))
	draw_arc(center, 4, 0, TAU, 16, Color.WHITE, 1.0)

	for e: GameEnemy in world.get_enemies():
		if not is_instance_valid(e) or e.is_dead:
			continue
		if not fog.is_position_visible(e.world_position):
			continue
		var ep: Vector2 = e.world_position
		var edx: float = ep.x - pp.x
		var edy: float = ep.y - pp.y
		if edx * edx + edy * edy > radius_sq:
			continue
		var ix: float = (edx - edy) * TILE_PX / 2.0
		var iy: float = (edx + edy) * TILE_PX / 4.0
		var ex: float = center.x + ix
		var ey: float = center.y + iy
		if ex < 0.0 or ex >= SIZE or ey < 0.0 or ey >= SIZE:
			continue
		draw_circle(Vector2(ex, ey), 3, Color.RED)


func _draw_mini_tile(px: float, py: float, color: Color, alpha_mul: float) -> void:
	var c := color
	c.a *= alpha_mul
	var half := TILE_PX / 2.0
	var quarter := TILE_PX / 4.0
	var points := PackedVector2Array([
		Vector2(px, py - quarter),
		Vector2(px + half, py),
		Vector2(px, py + quarter),
		Vector2(px - half, py),
	])
	draw_colored_polygon(points, c)


func _tile_color(tileset_name: String) -> Color:
	var n := tileset_name.to_lower()
	if "grass" in n and "dry" not in n and "medium" not in n:
		return Color(0.24, 0.47, 0.24)
	if "dirt" in n:
		return Color(0.47, 0.31, 0.2)
	if "sand" in n:
		return Color(0.71, 0.63, 0.39)
	if "stone" in n:
		return Color(0.39, 0.39, 0.43)
	if "forest" in n:
		return Color(0.16, 0.31, 0.16)
	return Color(0.31, 0.31, 0.31)
