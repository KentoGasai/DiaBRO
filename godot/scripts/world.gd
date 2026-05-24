extends Node2D
class_name GameWorld
## Игровой мир — логика из main.py Game

const SCREEN_SIZE := Vector2(1920, 1080)
const BG_COLOR := Color(0.12, 0.16, 0.2)

@onready var camera_layer: Node2D = $CameraLayer
@onready var tile_world: TileMapLayer = $CameraLayer/TileWorld
@onready var entities: Node2D = $CameraLayer/Entities
@onready var player: GamePlayer = $CameraLayer/Entities/Player
@onready var combat: CombatManager = $CombatManager
@onready var projectiles: Node2D = $CameraLayer/Projectiles
@onready var enemy_projectiles: Node2D = $CameraLayer/EnemyProjectiles
@onready var fog: FogOfWar = $CameraLayer/FogOfWar

var level := LevelController.new("procedural")
var camera_offset := Vector2.ZERO
var camera_target := Vector2.ZERO
const CAMERA_SMOOTH := 0.1

var _enemy_spawn_cooldown := 0.0
var _last_spawn_pos := Vector2.ZERO
var _attack_pressed_prev := false
var _ability_prev: Dictionary = {}


func _ready() -> void:
	GameState.current_level_name = "procedural"
	tile_world.setup(level)
	player.died.connect(_on_player_died)
	combat.attack_performed.connect(_on_attack_performed)
	_refresh_background()


func _process(delta: float) -> void:
	if GameState.paused or GameState.game_over:
		return

	_update_camera(delta)
	camera_layer.position = camera_offset
	player.update_player(delta, Vector2.ZERO)
	fog.update_fog(player.world_position, delta)
	tile_world.refresh_around(player.world_position, false, get_viewport_rect().size)

	_update_enemy_highlight()
	_handle_combat_input()
	_update_enemies(delta)
	_update_enemy_projectiles(delta)
	_sync_entity_projectiles()

	player.restore_mana(5.0 * delta)
	fog.camera_offset = Vector2.ZERO

	if player.is_dead():
		GameState.set_game_over(true)


func _sync_entity_projectiles() -> void:
	for c in projectiles.get_children():
		if "world_position" in c:
			c.position = IsoMath.world_to_screen(c.world_position.x, c.world_position.y)


func _update_camera(_delta: float) -> void:
	var target_screen := IsoMath.world_to_screen(player.world_position.x, player.world_position.y)
	camera_target = SCREEN_SIZE / 2.0 - target_screen
	camera_offset = camera_offset.lerp(camera_target, CAMERA_SMOOTH)


func get_enemies() -> Array[GameEnemy]:
	var list: Array[GameEnemy] = []
	for c in entities.get_children():
		if c == player:
			continue
		if c is GameEnemy:
			list.append(c as GameEnemy)
	return list


func _update_enemies(delta: float) -> void:
	var pp: Vector2 = player.world_position
	for e: GameEnemy in get_enemies():
		if not is_instance_valid(e):
			continue
		if not fog.is_position_visible(e.world_position):
			e.visible = false
			continue
		e.visible = true
		var info: Dictionary = e.update_enemy(delta, pp, Vector2.ZERO)
		if info.is_empty():
			continue
		if info.get("is_melee", true):
			player.take_damage(int(info.get("damage", 5)))
		else:
			_spawn_enemy_projectile(info)
		if e.is_dead:
			e.queue_free()


func _spawn_enemy_projectile(info: Dictionary) -> void:
	var scene := load("res://scenes/combat/enemy_projectile.tscn")
	var p = scene.instantiate()
	enemy_projectiles.add_child(p)
	p.setup(info["start"], info["target"], int(info["damage"]), player)


func _update_enemy_projectiles(delta: float) -> void:
	for c in enemy_projectiles.get_children():
		if c.has_method("update_projectile"):
			if c.update_projectile(delta, Vector2.ZERO):
				c.queue_free()


func _handle_combat_input() -> void:
	if Input.is_action_just_pressed("toggle_melee"):
		combat.toggle_melee_mode()

	var mouse_g := get_viewport().get_mouse_position()
	var target_w := IsoMath.global_to_world(mouse_g, camera_offset)

	if Input.is_action_just_pressed("attack"):
		combat.try_attack(player.world_position, target_w, get_enemies(), projectiles)

	for action in ["ability_1", "ability_3", "ability_4", "ability_5", "ability_6", "ability_7", "ability_8", "ability_9"]:
		if Input.is_action_just_pressed(action):
			combat.try_attack(player.world_position, target_w, get_enemies(), projectiles)


func _on_attack_performed(is_melee: bool, target_world: Vector2) -> void:
	player.play_attack_animation(is_melee, target_world)


func _update_enemy_highlight() -> void:
	var mouse_g := get_viewport().get_mouse_position()
	var mw := IsoMath.global_to_world(mouse_g, camera_offset)
	for e: GameEnemy in get_enemies():
		if is_instance_valid(e):
			e.highlighted = e.check_mouse_hover(mw)


func _process_enemy_spawn(delta: float) -> void:
	if not GameState.enemies_enabled:
		return
	if level.procedural_generator == null:
		return
	_enemy_spawn_cooldown -= delta
	if _enemy_spawn_cooldown > 0.0:
		return
	var pp: Vector2 = player.world_position
	if pp.distance_squared_to(_last_spawn_pos) < 100.0:
		return
	var existing := get_enemies()
	EnemySpawner.procedural_spawn(
		entities, pp, existing, level.procedural_generator, GameState.max_enemies
	)
	_last_spawn_pos = pp
	_enemy_spawn_cooldown = GameState.enemy_spawn_frequency


func _physics_process(delta: float) -> void:
	_process_enemy_spawn(delta)


func spawn_enemy_type(type_id: String, count: int = 1) -> void:
	EnemySpawner.spawn_ring(entities, player.world_position, count, type_id)


func kill_all_enemies() -> void:
	for e: GameEnemy in get_enemies():
		if is_instance_valid(e):
			e.queue_free()


func load_level(level_name: String) -> bool:
	if level_name != "procedural":
		var path := LevelController.LEVELS_DIR + level_name + ".json"
		if not FileAccess.file_exists(path):
			return false
	level = LevelController.new(level_name)
	GameState.current_level_name = level_name
	tile_world.setup(level)
	tile_world.refresh_around(player.world_position, true, get_viewport_rect().size)
	fog.reset()
	return true


func restart_run() -> void:
	player.world_position = Vector2.ZERO
	player.velocity = Vector2.ZERO
	player.health = player.MAX_HEALTH
	player.mana = player.MAX_MANA
	player.invincibility_time = 0.0
	player.damage_flash_time = 0.0
	player.is_attacking = false
	player.walking = false

	camera_offset = Vector2.ZERO
	camera_target = Vector2.ZERO
	camera_layer.position = Vector2.ZERO

	level = LevelController.new("procedural")
	GameState.current_level_name = "procedural"
	tile_world.setup(level)
	tile_world.refresh_around(Vector2.ZERO, true, get_viewport_rect().size)

	kill_all_enemies()
	for c in projectiles.get_children():
		c.queue_free()
	for c in enemy_projectiles.get_children():
		c.queue_free()

	fog.reset()
	_enemy_spawn_cooldown = 0.0
	_last_spawn_pos = Vector2.ZERO
	GameState.reset_run_state()


func _on_player_died() -> void:
	GameState.set_game_over(true)


func _refresh_background() -> void:
	pass


func _draw() -> void:
	draw_rect(Rect2(-10000, -10000, 20000, 20000), BG_COLOR)
