extends Node
## Изометрические преобразования (порт game/isometric.py + main.py tile 128x64)

const TILE_WIDTH := 128.0
const TILE_HEIGHT := 64.0

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


func world_to_global(world_pos: Vector2, camera_offset: Vector2) -> Vector2:
	var s := world_to_screen(world_pos.x, world_pos.y)
	return s + camera_offset


func global_to_world(global_pos: Vector2, camera_offset: Vector2) -> Vector2:
	var local := global_pos - camera_offset
	return screen_to_world(local.x, local.y)


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


func world_direction_to_sprite_angle(world_dir: Vector2) -> float:
	if world_dir.length_squared() < 0.0001:
		return 0.0
	var sx := world_dir.x - world_dir.y
	var sy := -(world_dir.x + world_dir.y)
	return atan2(sy, sx)


func world_delta_to_sprite_angle(dx: float, dy: float) -> float:
	return world_direction_to_sprite_angle(Vector2(dx, dy))


## Радиус тайлов вокруг игрока по размеру экрана (как level.draw / fog в Pygame)
func visible_tile_radius(screen_size: Vector2) -> float:
	return maxf(screen_size.x, screen_size.y) / HALF_W + 12.0
