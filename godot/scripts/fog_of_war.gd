extends Node2D
class_name FogOfWar
## Туман войны на фиксированной карте.

const VISION_RADIUS := 12.0
const EXPLORATION_RADIUS := 10.0
const TILE_W := 128.0
const TILE_H := 64.0

var explored_tiles: Dictionary = {}
var visible_tiles: Dictionary = {}
var last_player_pos: Vector2 = Vector2.ZERO
var camera_offset: Vector2 = Vector2.ZERO

var _last_fog_tile := Vector2i(-999999, -999999)


func reset() -> void:
	explored_tiles.clear()
	visible_tiles.clear()
	last_player_pos = Vector2.ZERO
	_last_fog_tile = Vector2i(-999999, -999999)
	queue_redraw()


func _draw() -> void:
	var vp := get_viewport_rect().size
	draw_fog_overlay(vp, camera_offset)


func update_fog(player_pos: Vector2, _delta: float = 0.0) -> void:
	visible_tiles.clear()
	last_player_pos = player_pos
	var ri := int(EXPLORATION_RADIUS) + 1
	var px := int(player_pos.x)
	var py := int(player_pos.y)
	for dx in range(-ri, ri + 1):
		for dy in range(-ri, ri + 1):
			var tx := px + dx
			var ty := py + dy
			var cx := float(tx) + 0.5
			var cy := float(ty) + 0.5
			if Vector2(cx, cy).distance_to(player_pos) <= EXPLORATION_RADIUS:
				var key := Vector2i(tx, ty)
				visible_tiles[key] = true
				explored_tiles[key] = true

	var tile_pos := Vector2i(px, py)
	if tile_pos != _last_fog_tile:
		_last_fog_tile = tile_pos
		queue_redraw()


func is_position_visible(world_pos: Vector2) -> bool:
	if last_player_pos == Vector2.ZERO and visible_tiles.is_empty():
		return true
	return last_player_pos.distance_to(world_pos) <= VISION_RADIUS


func is_tile_visible(tx: int, ty: int) -> bool:
	return visible_tiles.has(Vector2i(tx, ty))


func _layer_screen_offset() -> Vector2:
	var p := get_parent()
	return p.position if p else Vector2.ZERO


func draw_fog_overlay(screen_size: Vector2, _camera_offset: Vector2) -> void:
	if visible_tiles.is_empty():
		return
	var half_w := TILE_W / 2.0
	var half_h := TILE_H / 2.0
	var vis_r: float = IsoMath.visible_tile_radius(screen_size)
	var vis_r_sq: float = vis_r * vis_r
	var layer_off := _layer_screen_offset()
	var px := int(last_player_pos.x)
	var py := int(last_player_pos.y)
	var ri := int(vis_r) + 2
	for dx in range(-ri, ri + 1):
		for dy in range(-ri, ri + 1):
			if float(dx * dx + dy * dy) > vis_r_sq:
				continue
			var tx := px + dx
			var ty := py + dy
			var key := Vector2i(tx, ty)
			if visible_tiles.has(key):
				continue
			var sx: float = (tx - ty) * half_w
			var sy: float = (tx + ty) * half_h
			var screen_x: float = sx + layer_off.x
			var screen_y: float = sy + layer_off.y
			if screen_x < -TILE_W * 2 or screen_x > screen_size.x + TILE_W * 2:
				continue
			if screen_y < -TILE_H * 2 or screen_y > screen_size.y + TILE_H * 2:
				continue
			var alpha: int = 140 if explored_tiles.has(key) else 200
			var points := PackedVector2Array([
				Vector2(sx, sy - half_h),
				Vector2(sx + half_w, sy),
				Vector2(sx, sy + half_h),
				Vector2(sx - half_w, sy),
			])
			draw_colored_polygon(points, Color(0, 0, 0, alpha / 255.0))
