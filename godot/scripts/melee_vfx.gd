extends Node2D
## Визуал ближней атаки

var world_position: Vector2 = Vector2.ZERO
var _age: float = 0.0
const LIFETIME := 0.35
var _angle: float = 0.0
var _range: float = 1.5


func setup(pos: Vector2, angle: float, p_range: float) -> void:
	world_position = pos
	_angle = angle
	_range = p_range
	position = IsoMath.world_to_screen(pos.x, pos.y)


func _process(delta: float) -> void:
	_age += delta
	if _age >= LIFETIME:
		queue_free()
		return
	position = IsoMath.world_to_screen(world_position.x, world_position.y)
	queue_redraw()


func _draw() -> void:
	var progress := _age / LIFETIME
	var max_r := _range * 35.0
	var current_r := max_r * progress
	var alpha := int(200 * (1.0 - progress))
	var col := Color(1, 1, 0.4, alpha / 255.0)
	draw_arc(Vector2.ZERO, current_r, 0, TAU, 32, col, maxf(1.0, 4.0 * (1.0 - progress)))
	var arc_len := max_r * 0.8
	var end := Vector2(cos(_angle), sin(_angle)) * arc_len * (1.0 - progress * 0.5)
	draw_line(Vector2.ZERO, end, Color(1, 1, 0.58, 1.0 - progress), maxf(2.0, 5.0 * (1.0 - progress)))
