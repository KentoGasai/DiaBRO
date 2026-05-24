extends CanvasLayer

@onready var health_bar: ProgressBar = $Margin/HealthBar
@onready var mana_bar: ProgressBar = $Margin/ManaBar
@onready var info_label: Label = $Margin/InfoLabel
@onready var controls_label: Label = $Margin/ControlsLabel
@onready var minimap: Control = $Minimap

var _world: GameWorld


func setup(world: GameWorld) -> void:
	_world = world
	if minimap.has_method("set_world"):
		minimap.set_world(world)


func _process(_delta: float) -> void:
	if _world == null or not is_instance_valid(_world.player):
		return
	var p: GamePlayer = _world.player
	health_bar.max_value = p.MAX_HEALTH
	health_bar.value = p.health
	mana_bar.max_value = p.MAX_MANA
	mana_bar.value = p.mana

	var mode: String = "Ближний" if _world.combat.is_melee_mode else "Дальний"
	var fps: int = int(Engine.get_frames_per_second())
	var pos: Vector2 = p.world_position
	var txt: String = "FPS: %d\nПозиция: (%.1f, %.1f)\nУровень: %s\nРежим боя: %s" % [
		fps, pos.x, pos.y, GameState.current_level_name, mode
	]
	if GameState.enemies_enabled:
		var n: int = _world.get_enemies().size()
		txt += "\nВраги: %d/%d (частота: %.1fс)" % [
			n, GameState.max_enemies, GameState.enemy_spawn_frequency
		]
	info_label.text = txt
