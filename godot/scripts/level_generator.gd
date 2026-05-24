class_name LevelGenerator
extends RefCounted
## Генерация уровня: биомы (пол) + окружение (пропсы и здания).

const _Props := preload("res://scripts/kenney_prop_catalog.gd")
const _Tiles := preload("res://scripts/kenney_tile_catalog.gd")

class BiomeData:
	var name: String
	var pack: String
	var base: String
	var spawn_chance: float

	func _init(n: String, pack_id: String, tile_base: String, sc: float) -> void:
		name = n
		pack = pack_id
		base = tile_base
		spawn_chance = sc

	func tile_dict(facing: String) -> Dictionary:
		return {"pack": pack, "base": base, "facing": facing}


static var BIOMES: Dictionary = {
	"plains": BiomeData.new(
		"plains", "kenney_isometricMiniatureFarm", "dirt", 0.15
	),
	"forest": BiomeData.new(
		"forest", "kenney_isometricMiniatureFarm", "dirtFarmland", 0.25
	),
	"desert": BiomeData.new(
		"desert", "kenney_isometricDungeon", "dirtTiles", 0.20
	),
	"dirt": BiomeData.new(
		"dirt", "kenney_isometricDungeon", "dirt", 0.10
	),
	"dry_grass": BiomeData.new(
		"dry_grass", "kenney_isometricMiniatureFarm", "planksOld", 0.18
	),
	"medium_grass": BiomeData.new(
		"medium_grass", "kenney_isometricMiniatureFarm", "dirtFarmland", 0.12
	),
	"library": BiomeData.new(
		"library", "kenney_isometricLibrary", "floorCarpet", 0.12
	),
	"stone": BiomeData.new(
		"stone", "kenney_isometricDungeon", "stoneInset", 0.05
	),
	"dark_dirt": BiomeData.new(
		"dark_dirt", "kenney_isometricDungeon", "planks", 0.22
	),
}

static var BIOME_THRESHOLDS: Array = [
	["desert", -0.35, -0.15],
	["dirt", -0.15, -0.02],
	["dry_grass", -0.02, 0.15],
	["plains", 0.15, 0.32],
	["medium_grass", 0.32, 0.48],
	["forest", 0.48, 0.62],
	["library", 0.62, 0.76],
	["dark_dirt", 0.76, 0.88],
	["stone", 0.88, 1.0],
]

const PROP_NOISE_FREQ := 0.11
const PROP_NOISE_THRESHOLD := 0.52
const SCATTER_PROP_CHANCE := 0.22
const STRUCTURE_CLUSTER_SPACING := 9
const STRUCTURE_TRY_CHANCE := 0.38

var seed_value: int
var _biome_noise: FastNoiseLite
var _prop_noise: FastNoiseLite
var _rng: RandomNumberGenerator
var _width: int
var _height: int
var _biome_grid: Dictionary = {}


func _init(p_seed: int = 0) -> void:
	_rng = RandomNumberGenerator.new()
	seed_value = p_seed
	_rng.seed = p_seed
	_biome_noise = FastNoiseLite.new()
	_biome_noise.seed = p_seed + 1000
	_biome_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_biome_noise.frequency = 0.045
	_prop_noise = FastNoiseLite.new()
	_prop_noise.seed = p_seed + 2000
	_prop_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_prop_noise.frequency = PROP_NOISE_FREQ


static func generate_level(
	width: int,
	height: int,
	p_seed: int = 0,
	_preset: String = "overworld"
) -> Dictionary:
	var gen := LevelGenerator.new(p_seed)
	return gen._fill_grid(width, height)


func _get_biome(wx: float, wy: float) -> BiomeData:
	var v := (_biome_noise.get_noise_2d(wx, wy) + 1.0) / 2.0
	for entry: Array in BIOME_THRESHOLDS:
		var min_v: float = entry[1]
		var max_v: float = entry[2]
		if v >= min_v and v < max_v:
			return BIOMES[entry[0]]
	return BIOMES["plains"]


func _fill_grid(width: int, height: int) -> Dictionary:
	_width = width
	_height = height
	_biome_grid.clear()

	var tiles: Dictionary = {}
	var props: Array = []
	var spawn_points: Array = []
	var edge_biome: BiomeData = BIOMES["stone"]

	for x in range(width):
		for y in range(height):
			var pos := Vector2i(x, y)
			var on_edge := x == 0 or y == 0 or x >= width - 1 or y >= height - 1
			var biome: BiomeData = edge_biome if on_edge else _get_biome(float(x), float(y))
			_biome_grid[pos] = biome.name
			var facing := _Tiles.facing_for_cell(x, y)
			tiles[pos] = biome.tile_dict(facing)

			if on_edge:
				continue
			if x % 3 == 0 and y % 3 == 0:
				if _rng.randf() < biome.spawn_chance * 0.45:
					spawn_points.append({
						"x": x,
						"y": y,
						"kind": "enemy",
						"biome": biome.name,
					})

	_place_structures(props)
	_scatter_props(props)

	return {
		"tiles": tiles,
		"props": props,
		"spawn_points": spawn_points,
		"width": width,
		"height": height,
	}


func _place_structures(props: Array) -> void:
	var margin := 4
	for ax in range(margin, _width - margin, STRUCTURE_CLUSTER_SPACING):
		for ay in range(margin, _height - margin, STRUCTURE_CLUSTER_SPACING):
			if _rng.randf() > STRUCTURE_TRY_CHANCE:
				continue
			var anchor := Vector2i(ax + _rng.randi_range(0, 2), ay + _rng.randi_range(0, 2))
			var biome_name: String = _biome_grid.get(anchor, "plains")
			var blueprints := _Props.blueprint_ids_for_biome(biome_name)
			if blueprints.is_empty():
				continue
			var bp_id: String = blueprints[_rng.randi_range(0, blueprints.size() - 1)]
			var bp: Dictionary = _Props.STRUCTURE_BLUEPRINTS[bp_id]
			if not _can_place_blueprint(anchor, bp):
				continue
			_append_blueprint(props, anchor, bp)


func _can_place_blueprint(anchor: Vector2i, bp: Dictionary) -> bool:
	for part: Dictionary in bp.get("parts", []):
		var p := anchor + Vector2i(int(part.get("dx", 0)), int(part.get("dy", 0)))
		if p.x < 2 or p.y < 2 or p.x >= _width - 2 or p.y >= _height - 2:
			return false
		if _is_near_center(p, 6):
			return false
	return true


func _is_near_center(cell: Vector2i, radius: int) -> bool:
	var cx := _width / 2
	var cy := _height / 2
	return absi(cell.x - cx) <= radius and absi(cell.y - cy) <= radius


func _append_blueprint(props: Array, anchor: Vector2i, bp: Dictionary) -> void:
	var pack := str(bp.get("pack", ""))
	for part: Dictionary in bp.get("parts", []):
		var p := anchor + Vector2i(int(part.get("dx", 0)), int(part.get("dy", 0)))
		props.append({
			"x": p.x,
			"y": p.y,
			"pack": pack,
			"base": str(part.get("base", "")),
			"facing": _Tiles.facing_for_cell(p.x, p.y),
		})


func _scatter_props(props: Array) -> void:
	var occupied: Dictionary = {}
	for entry: Dictionary in props:
		occupied[Vector2i(int(entry.get("x", 0)), int(entry.get("y", 0)))] = true

	var margin := 3
	for x in range(margin, _width - margin):
		for y in range(margin, _height - margin):
			var cell := Vector2i(x, y)
			if occupied.has(cell):
				continue
			if _is_near_center(cell, 5):
				continue
			var biome_name: String = _biome_grid.get(cell, "plains")
			var n := (_prop_noise.get_noise_2d(float(x), float(y)) + 1.0) * 0.5
			if n < PROP_NOISE_THRESHOLD:
				continue
			if _rng.randf() > SCATTER_PROP_CHANCE:
				continue
			var picked := _Props.pick_prop(biome_name, _rng)
			if picked.is_empty():
				continue
			props.append({
				"x": x,
				"y": y,
				"pack": str(picked.get("pack", "")),
				"base": str(picked.get("base", "")),
				"facing": _Tiles.facing_for_cell(x, y),
			})
			occupied[cell] = true
