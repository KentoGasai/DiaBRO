# Синхронизация данных Pygame -> Godot
$root = Split-Path -Parent $PSScriptRoot
Copy-Item "$root\game\enemy_types.json" "$PSScriptRoot\data\enemy_types.json" -Force
Copy-Item "$root\game\levels\*" "$PSScriptRoot\data\levels\" -Force
if (Test-Path "$root\game\images") {
    Copy-Item "$root\game\images\*" "$PSScriptRoot\assets\sprites\" -Recurse -Force
}
Write-Host "Synced enemy_types, levels, and images to godot/"
