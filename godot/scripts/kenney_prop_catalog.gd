class_name KenneyPropCatalog
extends RefCounted
## Декорации Kenney (домики из стен/крыш, мебель, заборы) по биомам.

const _Tiles := preload("res://scripts/kenney_tile_catalog.gd")

const PROP_POOLS: Dictionary = {
	"plains": [
		{"pack": "kenney_isometricMiniatureFarm", "base": "hayBales", "weight": 4},
		{"pack": "kenney_isometricMiniatureFarm", "base": "hayBalesStacked", "weight": 2},
		{"pack": "kenney_isometricMiniatureFarm", "base": "fenceLow", "weight": 3},
		{"pack": "kenney_isometricMiniatureFarm", "base": "sacksCrate", "weight": 2},
		{"pack": "kenney_isometricMiniatureFarm", "base": "ladderStand", "weight": 1},
	],
	"forest": [
		{"pack": "kenney_isometricMiniatureFarm", "base": "corn", "weight": 4},
		{"pack": "kenney_isometricMiniatureFarm", "base": "cornDouble", "weight": 2},
		{"pack": "kenney_isometricMiniatureFarm", "base": "fenceHigh", "weight": 3},
		{"pack": "kenney_isometricMiniatureFarm", "base": "hayBales", "weight": 2},
	],
	"desert": [
		{"pack": "kenney_isometricDungeon", "base": "barrel", "weight": 3},
		{"pack": "kenney_isometricDungeon", "base": "barrels", "weight": 2},
		{"pack": "kenney_isometricDungeon", "base": "stoneColumn", "weight": 2},
		{"pack": "kenney_isometricDungeon", "base": "stoneCorner", "weight": 2},
	],
	"dirt": [
		{"pack": "kenney_isometricDungeon", "base": "barrelsStacked", "weight": 3},
		{"pack": "kenney_isometricDungeon", "base": "woodenCrate", "weight": 2},
		{"pack": "kenney_isometricDungeon", "base": "barrel", "weight": 2},
	],
	"dry_grass": [
		{"pack": "kenney_isometricMiniatureFarm", "base": "hayBalesStacked", "weight": 4},
		{"pack": "kenney_isometricMiniatureFarm", "base": "fenceLowBroken", "weight": 2},
	],
	"medium_grass": [
		{"pack": "kenney_isometricMiniatureFarm", "base": "cornYoung", "weight": 3},
		{"pack": "kenney_isometricMiniatureFarm", "base": "fenceLow", "weight": 2},
	],
	"stone": [
		{"pack": "kenney_isometricDungeon", "base": "stoneWall", "weight": 3},
		{"pack": "kenney_isometricDungeon", "base": "stoneWallBroken", "weight": 2},
		{"pack": "kenney_isometricDungeon", "base": "stoneColumnWood", "weight": 2},
	],
	"dark_dirt": [
		{"pack": "kenney_isometricDungeon", "base": "chair", "weight": 2},
		{"pack": "kenney_isometricDungeon", "base": "tableShort", "weight": 3},
		{"pack": "kenney_isometricDungeon", "base": "tableShortChairs", "weight": 2},
		{"pack": "kenney_isometricDungeon", "base": "tableRound", "weight": 2},
		{"pack": "kenney_isometricDungeon", "base": "chestClosed", "weight": 2},
		{"pack": "kenney_isometricDungeon", "base": "barrel", "weight": 2},
	],
	"library": [
		{"pack": "kenney_isometricLibrary", "base": "bookcaseBooks", "weight": 4},
		{"pack": "kenney_isometricLibrary", "base": "libraryChair", "weight": 3},
		{"pack": "kenney_isometricLibrary", "base": "longTable", "weight": 2},
		{"pack": "kenney_isometricLibrary", "base": "bookStand", "weight": 2},
		{"pack": "kenney_isometricLibrary", "base": "displayCaseBooks", "weight": 1},
	],
}

## Шаблоны «зданий» — несколько тайлов рядом (ферма / руины).
const STRUCTURE_BLUEPRINTS: Dictionary = {
	"farm_shack": {
		"biomes": ["plains", "medium_grass", "dry_grass"],
		"pack": "kenney_isometricMiniatureFarm",
		"parts": [
			{"dx": 0, "dy": 0, "base": "woodWall"},
			{"dx": 1, "dy": 0, "base": "woodWallDoorClosed"},
			{"dx": 0, "dy": 1, "base": "woodWallWindow"},
			{"dx": 1, "dy": 1, "base": "woodWall"},
			{"dx": 0, "dy": -1, "base": "roof"},
			{"dx": 1, "dy": -1, "base": "roof"},
		],
	},
	"dungeon_room": {
		"biomes": ["desert", "dark_dirt", "dirt"],
		"pack": "kenney_isometricDungeon",
		"parts": [
			{"dx": 0, "dy": 0, "base": "stoneWall"},
			{"dx": 1, "dy": 0, "base": "stoneWallDoorClosed"},
			{"dx": 0, "dy": 1, "base": "stoneWallWindow"},
			{"dx": 1, "dy": 1, "base": "stoneWall"},
		],
	},
	"library_corner": {
		"biomes": ["library"],
		"pack": "kenney_isometricLibrary",
		"parts": [
			{"dx": 0, "dy": 0, "base": "bookcaseBooks"},
			{"dx": 1, "dy": 0, "base": "bookcaseWideBooks"},
			{"dx": 0, "dy": 1, "base": "libraryChair"},
			{"dx": 1, "dy": 1, "base": "longTableChairs"},
		],
	},
}


static func pick_prop(biome_name: String, rng: RandomNumberGenerator) -> Dictionary:
	var pool: Array = PROP_POOLS.get(biome_name, PROP_POOLS["plains"])
	var total := 0
	for entry: Dictionary in pool:
		if _prop_exists(entry):
			total += int(entry.get("weight", 1))
	if total <= 0:
		return {}
	var roll := rng.randi_range(0, total - 1)
	for entry: Dictionary in pool:
		if not _prop_exists(entry):
			continue
		var w := int(entry.get("weight", 1))
		if roll < w:
			return entry.duplicate()
		roll -= w
	if pool.size() > 0:
		return (pool[0] as Dictionary).duplicate()
	return {}


static func _prop_exists(entry: Dictionary) -> bool:
	return FileAccess.file_exists(
		_Tiles.texture_path(
			str(entry.get("pack", "")),
			str(entry.get("base", "")),
			"E"
		)
	)


static func blueprint_ids_for_biome(biome_name: String) -> Array[String]:
	var ids: Array[String] = []
	for blueprint_id in STRUCTURE_BLUEPRINTS:
		var bp: Dictionary = STRUCTURE_BLUEPRINTS[blueprint_id]
		if biome_name in bp.get("biomes", []):
			ids.append(blueprint_id)
	return ids
