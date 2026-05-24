extends Node2D
class_name GameEnemy
## Враг (порт game/enemy.py)

var world_position: Vector2 = Vector2.ZERO
var max_health := 30
var health := 30
var damage := 5
var speed := 6.0
var aggro_range := 150.0
var attack_range := 1.2
var attack_cooldown_time := 1.5
var attack_cooldown := 0.0
var is_melee := true
var is_dead := false
var dying := false
var highlighted := false
var is_moving := false
var enemy_type_id := "default"
var death_time := 0.0
const DEATH_DURATION := 0.5

var _sprite_angle := 0.0
var _fallback_color := Color(0.78, 0.2, 0.2)
var _fallback_size := 18.0

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var hp_bar: ProgressBar = $HPBar


func setup_from_type(type_id: String, pos: Vector2) -> void:
	enemy_type_id = type_id
	world_position = pos
	var data := EnemyRegistry.get_type(type_id)
	max_health = int(data.get("max_health", 30))
	health = max_health
	damage = int(data.get("damage", 5))
	speed = float(data.get("speed", 6.0))
	var atk: String = data.get("attack_type", "melee")
	is_melee = atk == "melee"
	attack_range = 1.2 if is_melee else 8.0
	aggro_range = float(data.get("aggro_range", 150.0))
	attack_cooldown_time = float(data.get("attack_cooldown", 1.5))
	if data.get("color") is Color:
		_fallback_color = data["color"]
	_load_sprites(data)
	if hp_bar:
		hp_bar.max_value = max_health
		hp_bar.value = health


func _load_sprites(data: Dictionary) -> void:
	var sp: String = str(data.get("sprite_path", ""))
	if sp.is_empty():
		sprite.visible = false
		return
	var path: String = str(data.get("sprite_path", ""))
	if path.is_empty():
		path = SpriteSheetBuilder.resolve_asset_path(sp)
	var weapon: String = str(data.get("weapon_path", ""))
	var scale := float(data.get("sprite_scale", 1.0))
	if ResourceLoader.exists(path):
		sprite.sprite_frames = SpriteSheetBuilder.build_frames(path, weapon, scale)
		sprite.visible = sprite.sprite_frames.has_animation("walk_0")
		if sprite.visible:
			var ft := sprite.sprite_frames.get_frame_texture("walk_0", 0)
			if ft:
				_fallback_size = ft.get_height() / 4.0
	else:
		push_warning("Enemy sprite not found: %s (from %s)" % [path, sp])
		sprite.visible = false


func update_enemy(delta: float, player_pos: Vector2, camera_offset: Vector2) -> Dictionary:
	is_moving = false
	if dying:
		death_time += delta
		if death_time >= DEATH_DURATION:
			is_dead = true
		_sync_visual(camera_offset)
		queue_redraw()
		return {}
	if is_dead:
		return {}

	if attack_cooldown > 0.0:
		attack_cooldown -= delta

	var dx := player_pos.x - world_position.x
	var dy := player_pos.y - world_position.y
	var dist := sqrt(dx * dx + dy * dy)
	var attack_info := {}

	if dist <= aggro_range:
		if dist <= attack_range and attack_cooldown <= 0.0:
			attack_info = {
				"damage": damage,
				"is_melee": is_melee,
				"start": world_position,
				"target": player_pos,
			}
			attack_cooldown = attack_cooldown_time
			_play_attack_anim()
		elif dist > attack_range:
			var step := speed * delta
			world_position.x += (dx / dist) * step
			world_position.y += (dy / dist) * step
			is_moving = true
		_sprite_angle = IsoMath.world_delta_to_sprite_angle(dx, dy)
		_update_sprite_anim(delta)
	elif sprite.sprite_frames:
		sprite.stop()

	_sync_visual(camera_offset)
	queue_redraw()
	return attack_info


func _play_attack_anim() -> void:
	if not sprite.sprite_frames:
		return
	var dir := SpriteSheetBuilder.angle_to_direction(_sprite_angle)
	var anim := ("attack_melee_%d" if is_melee else "attack_ranged_%d") % dir
	if sprite.sprite_frames.has_animation(anim):
		sprite.play(anim)


func _update_sprite_anim(delta: float) -> void:
	if not sprite.sprite_frames or not is_moving:
		return
	var dir := SpriteSheetBuilder.angle_to_direction(_sprite_angle)
	var anim := "walk_%d" % dir
	if sprite.animation != anim:
		sprite.play(anim)


func take_damage(amount: int) -> void:
	if is_dead or dying:
		return
	health = maxi(0, health - amount)
	if hp_bar:
		hp_bar.value = health
	if health <= 0:
		dying = true
		death_time = 0.0
		if sprite.sprite_frames:
			var dir := SpriteSheetBuilder.angle_to_direction(_sprite_angle)
			var anim := "death_%d" % dir
			if sprite.sprite_frames.has_animation(anim):
				sprite.play(anim)
	elif sprite.sprite_frames:
		var dir := SpriteSheetBuilder.angle_to_direction(_sprite_angle)
		var anim := "hurt_%d" % dir
		if sprite.sprite_frames.has_animation(anim):
			sprite.play(anim)


func check_mouse_hover(mouse_world: Vector2, radius: float = 1.0) -> bool:
	if is_dead or dying:
		return false
	return world_position.distance_to(mouse_world) <= radius


func _sync_visual(camera_offset: Vector2) -> void:
	position = IsoMath.world_to_screen(world_position.x, world_position.y) + camera_offset
	if sprite and sprite.visible and sprite.sprite_frames:
		var tex := sprite.sprite_frames.get_frame_texture(sprite.animation, sprite.frame)
		if tex:
			sprite.position = Vector2(-tex.get_width() * 0.5, -tex.get_height() * 0.75)
	if hp_bar:
		hp_bar.position = Vector2(-30, -50)


func _draw() -> void:
	if sprite and sprite.visible:
		if highlighted and not dying:
			draw_circle(Vector2(0, -20), _fallback_size + 8, Color(1, 1, 0, 0.25))
		return
	var col := _fallback_color
	if highlighted:
		col = Color(1, 1, 0.4)
	var sz := _fallback_size
	if dying:
		sz *= 1.0 - (death_time / DEATH_DURATION) * 0.5
		col.a = 1.0 - death_time / DEATH_DURATION
	draw_rect(Rect2(-sz / 2, -sz / 2, sz, sz), col)
