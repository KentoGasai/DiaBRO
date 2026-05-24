class_name CombatManager
extends Node
## Система боя (порт game/combat.py)

signal attack_performed(is_melee: bool, target_world: Vector2)

const MELEE_RANGE := 1.5
const MELEE_COOLDOWN := 0.3
const RANGED_RANGE := 8.0
const RANGED_SPEED := 12.0

var is_melee_mode := false
var attack_cooldown := 0.0

var _projectile_scene: PackedScene
var _melee_vfx_scene: PackedScene


func _ready() -> void:
	_projectile_scene = load("res://scenes/combat/projectile.tscn")
	_melee_vfx_scene = load("res://scenes/combat/melee_vfx.tscn")


func _process(delta: float) -> void:
	if attack_cooldown > 0.0:
		attack_cooldown -= delta


func toggle_melee_mode() -> void:
	is_melee_mode = not is_melee_mode


func try_attack(
	player_pos: Vector2,
	target_world: Vector2,
	enemies: Array[GameEnemy],
	projectiles_parent: Node
) -> bool:
	if attack_cooldown > 0.0:
		return false

	var wdir := target_world - player_pos
	if wdir.length_squared() < 0.0001:
		return false

	var screen_angle := IsoMath.world_direction_to_sprite_angle(wdir)
	var world_dir := wdir.normalized()

	if is_melee_mode:
		var damage: int = randi_range(5, 9)
		for e: GameEnemy in enemies:
			if not is_instance_valid(e) or e.is_dead or e.dying:
				continue
			if player_pos.distance_to(e.world_position) <= MELEE_RANGE:
				e.take_damage(damage)
		_spawn_melee_vfx(player_pos, screen_angle, projectiles_parent)
	else:
		var damage: int = randi_range(1, 5)
		_spawn_projectile(player_pos, world_dir, damage, enemies, projectiles_parent)

	attack_cooldown = MELEE_COOLDOWN
	attack_performed.emit(is_melee_mode, target_world)
	return true


func _spawn_projectile(
	start: Vector2,
	world_dir: Vector2,
	damage: int,
	enemies: Array[GameEnemy],
	parent: Node
) -> void:
	if _projectile_scene == null:
		return
	var p = _projectile_scene.instantiate()
	parent.add_child(p)
	p.setup(start, world_dir, damage, RANGED_SPEED, RANGED_RANGE, enemies)


func _spawn_melee_vfx(pos: Vector2, screen_angle: float, parent: Node) -> void:
	if _melee_vfx_scene == null:
		return
	var v = _melee_vfx_scene.instantiate()
	parent.add_child(v)
	v.setup(pos, screen_angle, MELEE_RANGE)
