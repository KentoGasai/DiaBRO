extends Node
## Изометрические преобразования (как game/isometric.py + main.py WASD).

## Kenney isometric: ромб 256×128 (см. knowledge base Kenney).
const TILE_WIDTH := 256.0
const TILE_HEIGHT := 128.0

const HALF_W := TILE_WIDTH / 2.0
const HALF_H := TILE_HEIGHT / 2.0


func world_to_screen(world_x: float, world_y: float) -> Vector2:
	var sx := (world_x - world_y) * HALF_W
	var sy := (world_x + world_y) * HALF_H
	return Vector2(sx, sy)


func screen_to_world(screen_x: float, screen_y: float) -> Vector2:
	var wx := (screen_x / HALF_W + screen_y / HALF_H) / 2.0
	var wy := (screen_y / HALF_H - screen_x / HALF_W) / 2.0
	return Vector2(wx, wy)


func screen_to_world_on_layer(
	_tile_map: TileMapLayer,
	screen_pos: Vector2,
	camera_layer_pos: Vector2
) -> Vector2:
	if camera_layer_pos.length_squared() > 0.0001:
		return screen_to_world(screen_pos.x - camera_layer_pos.x, screen_pos.y - camera_layer_pos.y)
	var cam := _get_active_camera()
	if cam:
		return cam.get_global_transform().affine_inverse() * screen_pos
	return screen_to_world(screen_pos.x, screen_pos.y)


func _get_active_camera() -> Camera2D:
	var tree := Engine.get_main_loop()
	if tree is SceneTree:
		return (tree as SceneTree).root.get_viewport().get_camera_2d()
	return null


func world_to_global_on_layer(
	_tile_map: TileMapLayer,
	world_pos: Vector2,
	camera_layer_pos: Vector2
) -> Vector2:
	return world_to_screen(world_pos.x, world_pos.y) + camera_layer_pos


func global_to_world_on_layer(
	tile_map: TileMapLayer,
	screen_pos: Vector2,
	camera_layer_pos: Vector2
) -> Vector2:
	return screen_to_world_on_layer(tile_map, screen_pos, camera_layer_pos)


func tile_cell_top_local(tile_map: TileMapLayer, tx: int, ty: int) -> Vector2:
	if tile_map == null:
		return world_to_screen(float(tx), float(ty))
	return tile_cell_screen_on_layer(tile_map, tx, ty)


func tile_cell_foot_local(tile_map: TileMapLayer, tx: int, ty: int) -> Vector2:
	return tile_cell_top_local(tile_map, tx, ty) + Vector2(0.0, HALF_H)


func keyboard_to_world_vector() -> Vector2:
	var screen_up := 1.0 if Input.is_action_pressed("move_up") else 0.0
	var screen_down := 1.0 if Input.is_action_pressed("move_down") else 0.0
	var screen_left := 1.0 if Input.is_action_pressed("move_left") else 0.0
	var screen_right := 1.0 if Input.is_action_pressed("move_right") else 0.0
	var wx := -screen_up + screen_down + screen_right - screen_left
	var wy := -screen_up + screen_down - screen_right + screen_left
	var v := Vector2(wx, wy)
	if v.length_squared() > 0.001:
		return v.normalized()
	return Vector2.ZERO


## Угол спрайта (8 направлений) из вектора в мировых тайлах — как game/player.py.
func world_direction_to_sprite_angle(world_dir: Vector2) -> float:
	if world_dir.length_squared() < 0.0001:
		return 0.0
	var sx := world_dir.x - world_dir.y
	var sy := -(world_dir.x + world_dir.y)
	return atan2(sy, sx)


func world_delta_to_sprite_angle(dx: float, dy: float) -> float:
	return world_direction_to_sprite_angle(Vector2(dx, dy))


## Мировые тайлы → точка на слое карты (для мыши / прицеливания).
func world_to_aim_point(world_pos: Vector2) -> Vector2:
	return world_to_screen(world_pos.x, world_pos.y)


## Экран (слой CameraLayer) → мировые тайлы.
func layer_point_to_world(layer_pos: Vector2) -> Vector2:
	return screen_to_world(layer_pos.x, layer_pos.y)


func visible_tile_radius(screen_size: Vector2) -> float:
	return maxf(screen_size.x, screen_size.y) / HALF_W + 12.0


## Аффинное совмещение локали TileMapLayer с world_to_screen (калибровка у центра карты).
func fit_tilemap_to_iso(tile_map: TileMapLayer, center_x: int, center_y: int) -> Transform2D:
	if tile_map == null:
		return Transform2D.IDENTITY
	var i0 := Vector2i(center_x, center_y)
	var i1 := Vector2i(center_x + 1, center_y)
	var i2 := Vector2i(center_x, center_y + 1)
	var p0 := tile_map.map_to_local(i0)
	var p1 := tile_map.map_to_local(i1)
	var p2 := tile_map.map_to_local(i2)
	var s0 := world_to_screen(float(i0.x), float(i0.y))
	var s1 := world_to_screen(float(i1.x), float(i1.y))
	var s2 := world_to_screen(float(i2.x), float(i2.y))
	return _affine_from_three_points(p0, p1, p2, s0, s1, s2)


func _affine_from_three_points(
	p0: Vector2, p1: Vector2, p2: Vector2,
	s0: Vector2, s1: Vector2, s2: Vector2
) -> Transform2D:
	var det := (p1.x - p0.x) * (p2.y - p0.y) - (p2.x - p0.x) * (p1.y - p0.y)
	if absf(det) < 0.0001:
		return Transform2D.IDENTITY
	var x_axis := Vector2(
		((s1.x - s0.x) * (p2.y - p0.y) - (s2.x - s0.x) * (p1.y - p0.y)) / det,
		((s1.y - s0.y) * (p2.y - p0.y) - (s2.y - s0.y) * (p1.y - p0.y)) / det
	)
	var y_axis := Vector2(
		((s2.x - s0.x) * (p1.x - p0.x) - (s1.x - s0.x) * (p2.x - p0.x)) / det,
		((s2.y - s0.y) * (p1.x - p0.x) - (s1.y - s0.y) * (p2.x - p0.x)) / det
	)
	var mapped_p0 := Vector2(x_axis.x * p0.x + y_axis.x * p0.y, x_axis.y * p0.x + y_axis.y * p0.y)
	var origin := s0 - mapped_p0
	return Transform2D(x_axis, y_axis, origin)


## Позиция тайла на CameraLayer после выравнивания TileWorld.
func tile_cell_screen_on_layer(tile_map: TileMapLayer, tx: int, ty: int) -> Vector2:
	if tile_map == null:
		return world_to_screen(float(tx), float(ty))
	var local := tile_map.map_to_local(Vector2i(tx, ty))
	return tile_map.transform * local
