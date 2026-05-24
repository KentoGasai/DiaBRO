class_name EnemySpawner
extends RefCounted

const ENEMY_SCENE := preload("res://scenes/entities/enemy.tscn")


static func spawn_enemy(parent: Node, type_id: String, pos: Vector2) -> GameEnemy:
	var e: GameEnemy = ENEMY_SCENE.instantiate() as GameEnemy
	parent.add_child(e)
	e.setup_from_type(type_id, pos)
	return e


static func spawn_ring(parent: Node, center: Vector2, count: int, type_id: String) -> void:
	for i in range(count):
		var angle := (TAU / count) * i + randf_range(-0.3, 0.3)
		var dist := randf_range(3.0, 6.0)
		var pos := center + Vector2(cos(angle), sin(angle)) * dist
		spawn_enemy(parent, type_id, pos)


static func spawn_from_level(
	parent: Node,
	level: LevelController,
	player_pos: Vector2,
	existing: Array[GameEnemy],
	max_count: int
) -> void:
	if level == null or level.spawn_points.is_empty():
		return
	if existing.size() >= max_count:
		return

	var spawned_grid: Dictionary = {}
	for e: GameEnemy in existing:
		if not is_instance_valid(e):
			continue
		var p: Vector2 = e.world_position
		var gx := int(p.x / 5.0) * 5
		var gy := int(p.y / 5.0) * 5
		spawned_grid[Vector2i(gx, gy)] = true

	var types := EnemyRegistry.get_type_ids()
	var available: Array = []
	for id in types:
		if id != "default":
			available.append(id)
	if available.is_empty():
		return

	for sp in level.spawn_points:
		if existing.size() >= max_count:
			break
		if typeof(sp) != TYPE_DICTIONARY:
			continue
		var x: float = float(sp.get("x", 0))
		var y: float = float(sp.get("y", 0))
		var pos := Vector2(x, y)
		if x < level.bounds_min.x or x > level.bounds_max.x:
			continue
		if y < level.bounds_min.y or y > level.bounds_max.y:
			continue
		var dx := x - player_pos.x
		var dy := y - player_pos.y
		var d2 := dx * dx + dy * dy
		if d2 < 15.0 * 15.0 or d2 > 35.0 * 35.0:
			continue
		var gx := int(x / 5.0) * 5
		var gy := int(y / 5.0) * 5
		if spawned_grid.has(Vector2i(gx, gy)):
			continue
		var too_close := false
		for e: GameEnemy in existing:
			if not is_instance_valid(e):
				continue
			var ep: Vector2 = e.world_position
			var edx := x - ep.x
			var edy := y - ep.y
			if edx * edx + edy * edy < 64.0:
				too_close = true
				break
		if too_close:
			continue
		var tid: String = available[randi() % available.size()]
		var node := spawn_enemy(parent, tid, pos)
		spawned_grid[Vector2i(gx, gy)] = true
		existing.append(node)
