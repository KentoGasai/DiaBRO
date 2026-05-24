extends Node

## Глобальное состояние игры (пауза, враги, game over)



signal paused_changed(is_paused: bool)

signal game_over_changed(is_over: bool)

signal enemies_enabled_changed(enabled: bool)



var paused := false

var game_over := false

var enemies_enabled := false

var enemy_spawn_frequency := 2.0

var max_enemies := 12



var current_level_name := "procedural"





func set_paused(value: bool) -> void:

	if paused == value:

		return

	paused = value

	paused_changed.emit(paused)





func set_game_over(value: bool) -> void:

	if game_over == value:

		return

	game_over = value

	game_over_changed.emit(game_over)





func toggle_enemies() -> void:

	enemies_enabled = not enemies_enabled

	enemies_enabled_changed.emit(enemies_enabled)





func reset_run_state() -> void:

	set_game_over(false)
