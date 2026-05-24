extends Control
## Экран загрузки — мир генерируется до появления геймплея.

@onready var progress_bar: ProgressBar = $Center/Panel/VBox/ProgressBar
@onready var status_label: Label = $Center/Panel/VBox/StatusLabel
@onready var title_label: Label = $Center/Panel/VBox/TitleLabel


func _ready() -> void:
	if title_label:
		title_label.text = "DiaBRO"
	if progress_bar:
		progress_bar.value = 0.0


func run(world: GameWorld, level_name: String) -> void:
	visible = true
	_set_progress(0.0, "Инициализация…")
	await GameBootstrap.load_world(world, level_name, _on_bootstrap_progress)
	_set_progress(1.0, "Запуск…")
	await get_tree().process_frame


func _on_bootstrap_progress(ratio: float, message: String) -> void:
	# 0..1 на всю загрузку (уровень + тайлмап)
	var display := clampf(ratio, 0.0, 1.0)
	_set_progress(display, message)


func _set_progress(ratio: float, message: String) -> void:
	if progress_bar:
		progress_bar.value = ratio * 100.0
	if status_label:
		status_label.text = message
