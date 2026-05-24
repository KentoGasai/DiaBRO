class_name KenneyTileCatalog
extends RefCounted
## Каталог изометрических тайлов Kenney (256×512, основание 256×128).
## Паки: res://assets/sprites/bioms_tiles/<pack_name>/

const BIOMS_DIR := "res://assets/sprites/bioms_tiles/"

## Логический размер клетки на карте (ромб Kenney).
const TILE_SIZE := Vector2i(256, 128)
## Полный спрайт в PNG.
const TEXTURE_SIZE := Vector2i(256, 512)
## Точка привязки — центр нижнего ребра ромба (см. Kenney Knowledge Base).
const TEXTURE_ORIGIN := Vector2i(128, 512)

const FACINGS: PackedStringArray = ["E", "N", "S", "W"]


static func facing_for_cell(cell_x: int, cell_y: int) -> String:
	return FACINGS[(cell_x + cell_y) % 4]


static func texture_path(pack: String, base: String, facing: String) -> String:
	return BIOMS_DIR + pack + "/" + base + "_" + facing + ".png"


static func tile_key(data: Dictionary) -> String:
	var pack := str(data.get("pack", ""))
	var base := str(data.get("base", ""))
	if pack.is_empty():
		# Старый формат grass_green_128x64 + index — больше не используется.
		return ""
	var facing := str(data.get("facing", "E"))
	return "%s|%s|%s" % [pack, base, facing]


static func default_floor_tile() -> Dictionary:
	return {"pack": "kenney_isometricMiniatureFarm", "base": "dirt", "facing": "E"}


static func file_exists(data: Dictionary) -> bool:
	var path := texture_path(
		str(data.get("pack", "")),
		str(data.get("base", "")),
		str(data.get("facing", "E"))
	)
	return FileAccess.file_exists(path)
