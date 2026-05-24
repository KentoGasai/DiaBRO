extends Node2D
## Снаряд игрока (дальний бой)

var world_position: Vector2 = Vector2.ZERO
var velocity: Vector2 = Vector2.ZERO
var damage: int = 1
var max_range: float = 8.0
var distance_traveled: float = 0.0
var enemies: Array[GameEnemy] = []
var _hit: bool = false


func setup(
	start: Vector2,
	angle: float,
	p_damage: int,
	speed: float,
	p_range: float,
	p_enemies: Array[GameEnemy]
) -> void:
	world_position = start
	damage = p_damage
	max_range = p_range
	velocity = Vector2(cos(angle), sin(angle)) * speed
	enemies = p_enemies
	queue_redraw()


func _process(delta: float) -> void:
	if _hit:
		return
	var move := velocity * delta
	world_position += move
	distance_traveled += move.length()
	position = IsoMath.world_to_screen(world_position.x, world_position.y)
	if distance_traveled < 0.5:
		queue_redraw()
		return
	for e: GameEnemy in enemies:
		if not is_instance_valid(e) or e.is_dead or e.dying:
			continue
		if world_position.distance_to(e.world_position) < 0.8:
			e.take_damage(damage)
			_hit = true
			queue_free()
			return
	if distance_traveled >= max_range:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var pulse := sin(Time.get_ticks_msec() * 0.015) * 1.5
	var r := 8.0 + pulse
	draw_circle(Vector2.ZERO, r + 2, Color(0.78, 0.2, 0.0))
	draw_circle(Vector2.ZERO, r, Color(1.0, 0.4, 0.0))
	draw_circle(Vector2.ZERO, r - 2, Color(1.0, 0.8, 0.0))
	draw_circle(Vector2.ZERO, maxf(1.0, r - 4), Color(1.0, 1.0, 0.78))
