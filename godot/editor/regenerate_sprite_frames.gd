@tool
extends EditorScript
## Project → Tools → Run (или Файл → Запустить) — пересобрать все .tres из PNG.
## После этого анимации правятся в инспекторе AnimatedSprite2D → Sprite Frames.


func _run() -> void:
	SpriteFramesPipeline.regenerate_all()
