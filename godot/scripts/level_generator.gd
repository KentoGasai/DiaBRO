class_name LevelGenerator
extends RefCounted
## Генерация фиксированного уровня (биомы + точки спавна), один раз при загрузке.

class BiomeData:
	var name: String
	var tileset: String
	var tile_index: int
	var spawn_chance: float

	func _init(n: String, ts: String, ti: int, sc: float) -> void:
		name = n
		tileset = ts
		tile_index = ti
		spawn_chance = sc

	func tile_dict() -> Dictionary:
		return {"tileset": tileset, "tile": tile_index}


static var BIOMES: Dictionary = {
	"plains": BiomeData.new("plains", "grass_green_128x64", 0, 0.15),
	"forest": BiomeData.new("forest", "forest_ground_128x64", 0, 0.25),
	"desert": BiomeData.new("desert", "sand_128x64", 0, 0.20),
	"dirt": BiomeData.new("dirt", "dirt_128x64", 0, 0.10),
	"dry_grass": BiomeData.new("dry_grass", "grass_dry_128x64", 0, 0.18),
	"medium_grass": BiomeData.new("medium_grass", "grass_medium_128x64", 0, 0.12),
	"stone": BiomeData.new("stone", "stone_path_128x64", 0, 0.05),
	"dark_dirt": BiomeData.new("dark_dirt", "dirt_dark_128x64", 0, 0.22),
}

static var BIOME_THRESHOLDS: Array = [
	["desert", -0.3, -0.1],
	["dirt", -0.1, 0.0],
	["dry_grass", 0.0, 0.2],
	["plains", 0.2, 0.4],
	["medium_grass", 0.4, 0.6],
	["forest", 0.6, 0.8],
	["dark_dirt", 0.8, 0.9],
	["stone", 0.9, 1.0],
]

var seed_value: int
var _biome_noise: FastNoiseLite
var _rng: RandomNumberGenerator


func _init(p_seed: int = 0) -> void:
	_rng = RandomNumberGenerator.new()
	seed_value = p_seed
	_rng.seed = p_seed
	_biome_noise = FastNoiseLite.new()
	_biome_noise.seed = p_seed + 1000
	_biome_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_biome_noise.frequency = 0.03


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
	var tiles: Dictionary = {}
	var spawn_points: Array = []
	var edge_biome: BiomeData = BIOMES["stone"]

	for x in range(width):
		for y in range(height):
			var pos := Vector2i(x, y)
			# Кромка 1 тайл — камень; игровая зона внутри (совпадает с bounds в LevelController)
			var on_edge := x == 0 or y == 0 or x >= width - 1 or y >= height - 1
			var biome: BiomeData = edge_biome if on_edge else _get_biome(float(x), float(y))
			tiles[pos] = biome.tile_dict()

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

	return {
		"tiles": tiles,
		"spawn_points": spawn_points,
		"width": width,
		"height": height,
	}
