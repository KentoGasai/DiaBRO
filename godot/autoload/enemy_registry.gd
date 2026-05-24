extends Node
## Типы врагов: встроенный default + data/enemy_types.json

const CONFIG_PATH := "res://data/enemy_types.json"

const BUILTIN_DEFAULT := {
	"name": "Default",
	"sprite_path": "",
	"weapon_path": "",
	"projectile_path": "",
	"sprite_scale": 1.0,
	"max_health": 30,
	"damage": 5,
	"speed": 6.0,
	"attack_type": "melee",
	"aggro_range": 150.0,
	"attack_range": 1.2,
	"attack_cooldown": 1.5,
	"color": [200, 50, 50],
}

var _cache: Dictionary = {}


func get_all_types() -> Dictionary:
	if _cache.is_empty():
		_reload()
	return _cache


func reload() -> void:
	_cache.clear()
	_reload()


func _reload() -> void:
	_cache = {"default": BUILTIN_DEFAULT.duplicate(true)}
	if FileAccess.file_exists(CONFIG_PATH):
		var f := FileAccess.open(CONFIG_PATH, FileAccess.READ)
		if f:
			var parsed = JSON.parse_string(f.get_as_text())
			if typeof(parsed) == TYPE_DICTIONARY:
				for id in parsed:
					_cache[id] = _normalize_enemy_data(parsed[id])


func get_type(enemy_id: String) -> Dictionary:
	var all := get_all_types()
	if all.has(enemy_id):
		return all[enemy_id]
	return all["default"]


func get_type_ids() -> Array:
	return get_all_types().keys()


func _normalize_enemy_data(data: Dictionary) -> Dictionary:
	var d: Dictionary = data.duplicate(true)
	if d.get("color") is Array and d["color"].size() >= 3:
		d["color"] = Color(
			d["color"][0] / 255.0,
			d["color"][1] / 255.0,
			d["color"][2] / 255.0
		)
	for key in ["sprite_path", "weapon_path", "projectile_path"]:
		var raw: String = str(d.get(key, ""))
		if not raw.is_empty():
			d[key] = SpriteSheetBuilder.resolve_asset_path(raw)
	return d
