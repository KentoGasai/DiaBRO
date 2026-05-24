class_name ProceduralGenerator
extends RefCounted
## Процедурный мир (порт game/procedural_world.py)

const CHUNK_SIZE := 16

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
var _height_noise: FastNoiseLite
var _biome_noise: FastNoiseLite
var _chunks: Dictionary = {}
var _rng: RandomNumberGenerator


func _init(p_seed: int = -1) -> void:
	_rng = RandomNumberGenerator.new()
	if p_seed < 0:
		p_seed = randi()
	seed_value = p_seed
	_rng.seed = p_seed

	_height_noise = FastNoiseLite.new()
	_height_noise.seed = p_seed
	_height_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_height_noise.frequency = 0.05

	_biome_noise = FastNoiseLite.new()
	_biome_noise.seed = p_seed + 1000
	_biome_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_biome_noise.frequency = 0.03


func _chunk_key(cx: int, cy: int) -> Vector2i:
	return Vector2i(cx, cy)


func _world_to_chunk(wx: float, wy: float) -> Vector2i:
	return Vector2i(int(floor(wx / CHUNK_SIZE)), int(floor(wy / CHUNK_SIZE)))


func _get_biome(wx: float, wy: float) -> BiomeData:
	var v := (_biome_noise.get_noise_2d(wx, wy) + 1.0) / 2.0
	for entry: Array in BIOME_THRESHOLDS:
		var min_v: float = entry[1]
		var max_v: float = entry[2]
		if v >= min_v and v < max_v:
			return BIOMES[entry[0]]
	return BIOMES["plains"]


func _generate_chunk(cx: int, cy: int) -> Dictionary:
	var key := _chunk_key(cx, cy)
	if _chunks.has(key):
		return _chunks[key]

	var chunk := {
		"tiles": {},
		"spawn_points": [],
	}
	var sx := cx * CHUNK_SIZE
	var sy := cy * CHUNK_SIZE
	for x in range(sx, sx + CHUNK_SIZE):
		for y in range(sy, sy + CHUNK_SIZE):
			var biome: BiomeData = _get_biome(float(x), float(y))
			chunk["tiles"][Vector2i(x, y)] = biome.tile_dict()
			if x % 3 == 0 and y % 3 == 0:
				if _rng.randf() < biome.spawn_chance * 0.5:
					var dist := sqrt(float(x * x + y * y))
					if dist > 8.0:
						chunk["spawn_points"].append({
							"x": x, "y": y, "biome": biome.name
						})

	_chunks[key] = chunk
	return chunk


func get_tile(wx: int, wy: int) -> Dictionary:
	var c := _world_to_chunk(float(wx), float(wy))
	var chunk := _generate_chunk(c.x, c.y)
	return chunk["tiles"].get(Vector2i(wx, wy), BIOMES["plains"].tile_dict())


func get_tiles_in_radius(cx: float, cy: float, radius: float) -> Dictionary:
	var out: Dictionary = {}
	var min_c := _world_to_chunk(cx - radius, cy - radius)
	var max_c := _world_to_chunk(cx + radius, cy + radius)
	for chunk_x in range(min_c.x, max_c.x + 1):
		for chunk_y in range(min_c.y, max_c.y + 1):
			var chunk := _generate_chunk(chunk_x, chunk_y)
			for pos: Vector2i in chunk["tiles"]:
				var dx := pos.x - cx
				var dy := pos.y - cy
				if dx * dx + dy * dy <= radius * radius:
					out[pos] = chunk["tiles"][pos]
	return out


func trim_chunks(center: Vector2, max_chunk_radius: int = 22) -> void:
	if _chunks.size() < 96:
		return
	var pc := _world_to_chunk(center.x, center.y)
	var to_erase: Array[Vector2i] = []
	for key: Vector2i in _chunks:
		if absi(key.x - pc.x) > max_chunk_radius or absi(key.y - pc.y) > max_chunk_radius:
			to_erase.append(key)
	for key in to_erase:
		_chunks.erase(key)


func get_spawn_points_in_radius(cx: float, cy: float, radius: float) -> Array:
	var points: Array = []
	var min_c := _world_to_chunk(cx - radius, cy - radius)
	var max_c := _world_to_chunk(cx + radius, cy + radius)
	for chunk_x in range(min_c.x, max_c.x + 1):
		for chunk_y in range(min_c.y, max_c.y + 1):
			var chunk := _generate_chunk(chunk_x, chunk_y)
			for sp in chunk["spawn_points"]:
				var sp_x: float = float(sp["x"])
				var sp_y: float = float(sp["y"])
				var dx: float = sp_x - cx
				var dy: float = sp_y - cy
				if dx * dx + dy * dy <= radius * radius:
					points.append(sp)
	return points
