extends CanvasLayer
class_name FogOfWar
## Туман: TextureRect + GradientTexture2D (встроенный Godot), без шейдера.
## Логика тайлов — для миникарты и видимости врагов.

const VISION_RADIUS := 12.0
const EXPLORATION_RADIUS := 10.0

var explored_tiles: Dictionary = {}
var visible_tiles: Dictionary = {}
var last_player_pos: Vector2 = Vector2.ZERO

@onready var _overlay: TextureRect = $Overlay


func _ready() -> void:
	layer = 0
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_overlay.stretch_mode = TextureRect.STRETCH_SCALE
	_overlay.texture = _build_fog_gradient()


func _build_fog_gradient() -> GradientTexture2D:
	var grad := Gradient.new()
	grad.colors = PackedColorArray([Color(0, 0, 0, 0), Color(0, 0, 0, 0), Color(0, 0, 0, 0.75)])
	grad.offsets = PackedFloat32Array([0.0, 0.42, 1.0])
	var tex := GradientTexture2D.new()
	tex.gradient = grad
	tex.width = 512
	tex.height = 512
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	return tex


func reset() -> void:
	explored_tiles.clear()
	visible_tiles.clear()
	last_player_pos = Vector2.ZERO


func update_fog(player_pos: Vector2, _delta: float = 0.0) -> void:
	visible_tiles.clear()
	last_player_pos = player_pos
	var ri := int(EXPLORATION_RADIUS) + 1
	var px := int(player_pos.x)
	var py := int(player_pos.y)
	for dx in range(-ri, ri + 1):
		for dy in range(-ri, ri + 1):
			var tx := px + dx
			var ty := py + dy
			var cx := float(tx) + 0.5
			var cy := float(ty) + 0.5
			if Vector2(cx, cy).distance_to(player_pos) <= EXPLORATION_RADIUS:
				var key := Vector2i(tx, ty)
				visible_tiles[key] = true
				explored_tiles[key] = true


func is_position_visible(world_pos: Vector2) -> bool:
	if last_player_pos == Vector2.ZERO and visible_tiles.is_empty():
		return true
	return last_player_pos.distance_to(world_pos) <= VISION_RADIUS


func is_tile_visible(tx: int, ty: int) -> bool:
	return visible_tiles.has(Vector2i(tx, ty))
