class_name GameBootstrap
extends RefCounted
## Загрузка уровня и сборка мира до старта игры.


static func load_world(
	world: GameWorld,
	level_name: String,
	on_progress: Callable
) -> LevelController:
	if on_progress.is_valid():
		on_progress.call(0.05, "Загрузка уровня…")

	var level := LevelController.new(level_name)
	if level.tiles.is_empty():
		push_error("GameBootstrap: уровень '%s' без тайлов" % level_name)

	if on_progress.is_valid():
		on_progress.call(0.15, "Генерация биомов завершена")

	await world.prepare_level(level, on_progress)
	return level
