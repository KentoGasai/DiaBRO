extends Node
## Корень main.tscn — пауза, game over, связь UI

@onready var world: GameWorld = $World
@onready var hud: CanvasLayer = $UI/HUD
@onready var pause_menu: Control = $UI/PauseMenu
@onready var game_over_panel: Control = $UI/GameOverPanel


func _ready() -> void:
	GameState.paused_changed.connect(_on_paused_changed)
	GameState.game_over_changed.connect(_on_game_over_changed)
	pause_menu.visible = false
	game_over_panel.visible = false
	hud.setup(world)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		if GameState.game_over:
			get_tree().quit()
			return
		GameState.set_paused(not GameState.paused)
		get_viewport().set_input_as_handled()

	if GameState.game_over and event.is_action_pressed("restart"):
		await world.restart_run()
		game_over_panel.visible = false
		get_viewport().set_input_as_handled()


func _on_paused_changed(is_paused: bool) -> void:
	pause_menu.visible = is_paused
	get_tree().paused = false
	if is_paused:
		pause_menu.open_menu(world)
	else:
		pause_menu.close_menu()


func _on_game_over_changed(is_over: bool) -> void:
	game_over_panel.visible = is_over
