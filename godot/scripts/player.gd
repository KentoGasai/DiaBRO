extends Node2D
class_name GamePlayer
## Игрок (порт game/player.py)

signal died

const MAX_SPEED := 8.0
const ACCELERATION := 50.0
const DECELERATION := 80.0
const MAX_HEALTH := 100
const MAX_MANA := 100
const INVINCIBILITY_DURATION := 0.5

var world_position: Vector2 = Vector2.ZERO
var velocity: Vector2 = Vector2.ZERO
var health: int = MAX_HEALTH
var mana: int = MAX_MANA
var sprite_angle := 0.0
var attack_sprite_angle := 0.0
var walking := false
var is_attacking := false
var invincibility_time := 0.0
var damage_flash_time := 0.0

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
	_setup_sprites()
	if sprite:
		sprite.animation_finished.connect(_on_attack_anim_done)


func _setup_sprites() -> void:
	var char_path := "res://assets/sprites/character/male_unarmored.png"
	var weapon_path := "res://assets/sprites/weapon/male_longsword.png"
	if ResourceLoader.exists(char_path):
		var frames := SpriteSheetBuilder.build_frames(char_path, weapon_path, 1.0)
		sprite.sprite_frames = frames
		sprite.visible = true
	else:
		sprite.visible = false


func update_player(delta: float, camera_offset: Vector2) -> void:
	if invincibility_time > 0.0:
		invincibility_time -= delta
	if damage_flash_time > 0.0:
		damage_flash_time -= delta

	var target_vel := Vector2.ZERO
	var input_dir := IsoMath.keyboard_to_world_vector()
	if input_dir.length_squared() > 0.001:
		target_vel = input_dir * MAX_SPEED
		sprite_angle = IsoMath.world_direction_to_sprite_angle(input_dir)
		walking = true
	else:
		walking = false

	_apply_velocity(delta, target_vel)
	world_position += velocity * delta
	_update_animation(delta)
	_sync_position(camera_offset)
	queue_redraw()


func _apply_velocity(delta: float, target_vel: Vector2) -> void:
	if target_vel.length_squared() > 0.001:
		var accel := ACCELERATION * delta
		var diff := target_vel - velocity
		if diff.length() > accel:
			velocity += diff.normalized() * accel
		else:
			velocity = target_vel
	else:
		var decel := DECELERATION * delta
		var spd := velocity.length()
		if spd > decel:
			velocity = velocity.normalized() * (spd - decel)
		else:
			velocity = Vector2.ZERO
	if velocity.length() > MAX_SPEED:
		velocity = velocity.normalized() * MAX_SPEED


func _update_animation(delta: float) -> void:
	if not sprite.sprite_frames:
		return
	var dir := SpriteSheetBuilder.angle_to_direction(
		attack_sprite_angle if is_attacking else sprite_angle
	)
	if is_attacking:
		var anim := "attack_melee_%d" % dir
		if not sprite.sprite_frames.has_animation(anim):
			anim = "attack_melee_%d" % 0
		if sprite.animation != anim:
			sprite.play(anim)
		return
	if walking:
		var walk_anim := "walk_%d" % SpriteSheetBuilder.angle_to_direction(sprite_angle)
		if sprite.animation != walk_anim:
			sprite.play(walk_anim)
	else:
		var idle := "walk_%d" % SpriteSheetBuilder.angle_to_direction(sprite_angle)
		sprite.animation = idle
		sprite.stop()
		sprite.frame = 0


func play_attack_animation(is_melee: bool, target_world: Vector2) -> void:
	var wdir := target_world - world_position
	if wdir.length_squared() > 0.0001:
		attack_sprite_angle = IsoMath.world_direction_to_sprite_angle(wdir)
	else:
		attack_sprite_angle = sprite_angle
	is_attacking = true
	var dir := SpriteSheetBuilder.angle_to_direction(attack_sprite_angle)
	var anim := ("attack_melee_%d" if is_melee else "attack_ranged_%d") % dir
	if sprite.sprite_frames and sprite.sprite_frames.has_animation(anim):
		sprite.play(anim)
		if not sprite.animation_finished.is_connected(_on_attack_anim_done):
			sprite.animation_finished.connect(_on_attack_anim_done)


func _on_attack_anim_done() -> void:
	if is_attacking and sprite.animation.begins_with("attack_"):
		is_attacking = false


func take_damage(amount: int) -> bool:
	if invincibility_time > 0.0:
		return false
	health = maxi(0, health - amount)
	invincibility_time = INVINCIBILITY_DURATION
	damage_flash_time = 0.15
	if health <= 0:
		died.emit()
		return true
	return false


func restore_mana(amount: float) -> void:
	mana = minf(MAX_MANA, mana + amount)


func is_dead() -> bool:
	return health <= 0


func _sync_position(camera_offset: Vector2) -> void:
	var inv_skip := invincibility_time > 0.0 and int(invincibility_time * 10) % 2 == 0
	if inv_skip:
		return
	position = IsoMath.world_to_screen(world_position.x, world_position.y) + camera_offset
	if sprite:
		var fs := sprite.sprite_frames
		if fs and fs.get_frame_count(sprite.animation) > 0:
			var tex := fs.get_frame_texture(sprite.animation, sprite.frame)
			if tex:
				sprite.position = Vector2(-tex.get_width() * 0.5, -tex.get_height() * 0.75)


func _draw() -> void:
	if sprite and sprite.visible and sprite.sprite_frames:
		return
	var col := Color(0.39, 0.59, 1.0)
	if damage_flash_time > 0.0:
		col = Color(1, 0.4, 0.4)
	draw_circle(Vector2(0, -8), 14, col)
	draw_circle(Vector2(0, -22), 8, Color(1, 0.86, 0.71))
