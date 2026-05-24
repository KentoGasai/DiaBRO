@tool
extends Node
## Сцена tools/sprite_frames_generator.tscn — кнопка в инспекторе для пересборки .tres.


@export_tool_button("Сгенерировать все SpriteFrames (.tres)")
var regenerate_all_frames := func() -> void:
	SpriteFramesPipeline.regenerate_all()
