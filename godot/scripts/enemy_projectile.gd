extends Node2D

var world_position := Vector2.ZERO
var velocity := Vector2.ZERO
var damage := 5
var max_range := 15.0
var distance_traveled := 0.0
var _age := 0.0
var _player: GamePlayer


func setup(start: Vector2, target: Vector2, p_damage: int, player: GamePlayer) -> void:
	world_position = start
	damage = p_damage
	_player = player
	var dir := (target - start).normalized()
	velocity = dir * 10.0
	_age = 0.0


func update_projectile(delta: float, camera_offset: Vector2) -> bool:
	_age += delta
	var move := velocity * delta
	world_position += move
	distance_traveled += move.length()
	position = IsoMath.world_to_screen(world_position.x, world_position.y) + camera_offset
	if distance_traveled >= max_range:
		return true
	if _player and is_instance_valid(_player):
		if world_position.distance_to(_player.world_position) < 0.8:
			_player.take_damage(damage)
			return true
	queue_redraw()
	return false


func _draw() -> void:
	var pulse := sin(_age * 15.0) * 2.0
	var r := 6.0 + pulse
	draw_circle(Vector2.ZERO, r + 3, Color(0.31, 0.0, 0.47, 0.6))
	draw_circle(Vector2.ZERO, r + 1, Color(0.55, 0.0, 0.78))
	draw_circle(Vector2.ZERO, r - 1, Color(0.78, 0.39, 1.0))
	draw_circle(Vector2.ZERO, maxf(1.0, r - 3), Color(1.0, 0.78, 1.0))
