class_name SpriteSheetBuilder
extends RefCounted
## Нарезка спрайтшита 8x8 x 256px (порт game/sprites.py)

const FRAME_SIZE := 256
const DIR_TO_ROW := {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 7, 6: 6, 7: 5}

const ANIM_COLUMNS := {
	"walk": [0, 4],
	"attack_melee": [4, 5],
	"attack_ranged": [5, 6],
	"hurt": [6, 7],
	"death": [7, 8],
}


static func angle_to_direction(angle: float) -> int:
	var a := fposmod(angle, TAU)
	return int((a + PI / 8.0) / (PI / 4.0)) % 8


static func build_frames(
	char_path: String,
	weapon_path: String = "",
	scale: float = 1.0,
	weapon_offset: Vector2 = Vector2.ZERO
) -> SpriteFrames:
	var frames := SpriteFrames.new()
	if not ResourceLoader.exists(char_path):
		push_warning("Sprite not found: %s" % char_path)
		return frames

	var char_tex: Texture2D = load(char_path)
	var weapon_tex: Texture2D = null
	if weapon_path != "" and ResourceLoader.exists(weapon_path):
		weapon_tex = load(weapon_path)

	var char_img := char_tex.get_image()
	var weapon_img: Image = weapon_tex.get_image() if weapon_tex else null

	for dir_idx in range(8):
		var row: int = DIR_TO_ROW[dir_idx]
		for anim_name in ANIM_COLUMNS:
			var cols: Array = ANIM_COLUMNS[anim_name]
			var anim_id := "%s_%d" % [anim_name, dir_idx]
			if not frames.has_animation(anim_id):
				frames.add_animation(anim_id)
				frames.set_animation_speed(anim_id, 8.0 if anim_name == "walk" else 5.0)
				frames.set_animation_loop(anim_id, anim_name == "walk")

			for col in range(cols[0], cols[1]):
				var frame_img := _extract_frame(char_img, col, row)
				if weapon_img:
					var w_frame := _extract_frame(weapon_img, col, row)
					var ox := int(weapon_offset.x * scale)
					var oy := int(weapon_offset.y * scale)
					frame_img.blend_rect(
						w_frame,
						Rect2i(0, 0, FRAME_SIZE, FRAME_SIZE),
						Vector2i(ox, oy)
					)
				if scale != 1.0:
					var ns := Vector2i(int(FRAME_SIZE * scale), int(FRAME_SIZE * scale))
					frame_img.resize(ns.x, ns.y, Image.INTERPOLATE_NEAREST)
				var tex := ImageTexture.create_from_image(frame_img)
				frames.add_frame(anim_id, tex)

	return frames


static func _extract_frame(sheet: Image, col: int, row: int) -> Image:
	var rect := Rect2i(col * FRAME_SIZE, row * FRAME_SIZE, FRAME_SIZE, FRAME_SIZE)
	return sheet.get_region(rect)


static func resolve_asset_path(relative: String) -> String:
	if relative.is_empty():
		return ""
	if relative.begins_with("res://"):
		return relative
	# Pygame/редактор: game/images/enemy/skeleton.png
	if relative.begins_with("game/images/"):
		return "res://assets/sprites/" + relative.substr("game/images/".length())
	if relative.begins_with("game/"):
		return "res://assets/sprites/" + relative.substr(5)
	return "res://assets/sprites/" + relative
