# Warehouse Sprite Sheet V23

This is the current review sheet for the game-canvas portion of the mission
control UI. It is intentionally separate from the live canvas renderer until
the sprites are approved one by one.

## Base Scale

- Floor source PNG cell: `128x128 px`
- Visible isometric diamond: `128x64 px`
- Tile angle: 45-degree isometric diamond
- Robot dog source PNG: `128x128 px` with transparent padding
- Every exported sprite cell is square. Non-square objects such as `1x2`
  racks, `1x3` racks, depot zones, terminals, and conveyors keep their visual
  proportions inside a square transparent canvas.
- Medium 4K view target: one tile should display around `128-192 px` wide
- Zoom out target: one tile can display around `96-128 px` wide
- Zoom in target: one tile can display around `256 px` or higher

The live UI can scale the source sprites with `imageSmoothingEnabled = false`
so the pixels stay crisp at every zoom level.

## Visual Occupancy

- Robot visual size: roughly one third of a visible tile width
- Logical occupancy: one robot per tile for simulation
- Visual parking zone exception: an idle/depot zone can visually show four small
  parking pads inside a `2x2` tile area

## V23 Direction

The twenty-third pass keeps square transparent sprite cells and changes exit
gate conveyor sprites from diagonal `NE/SE/SW/NW` variants to cardinal
`E/S/W/N` variants. All exit gate directions are generated from model
coordinates and projected through the shared isometric camera.

- Floor plates use cool warehouse concrete/metal tones, corner rivets, panel
  seams, and fine pixel-grain material texture clipped inside each isometric
  diamond. These are treated as the current base floor tiles.
- LED markers are transparent overlays, not baked into floor tiles. They only
  draw the four edge lines around a single isometric tile.
- LED edge meanings:
  - `led_edge_pick_orange`: selected rack picking-zone tile only.
  - `led_edge_delivery_green`: persistent delivery/truck drop-off zone tile.
  - `led_edge_robot_route_cyan`: selected robot current tile and next navigation target.
  - `led_edge_congestion_red`: temporary active congestion tile until blockage clears.
- AEGIS base dog has eight directions: N, NE, E, SE, S, SW, W, NW. These are
  tile/world directions projected into the 45-degree isometric camera, not flat
  screen-space rotations.
- AEGIS is treated as a white/gray quadruped with dark exposed joints,
  wheel-like feet, and a compact sensor head.
- AEGIS wheel scale is depth-aware: wheels lower on the isometric screen render
  larger and brighter; far wheels render smaller and darker.
- AEGIS wheel shape is heading-aware: side-facing wheels are rounder, while
  front/back-facing wheels are narrower ellipses instead of identical circles.
- Loaded AEGIS variants place the carried SKU box directly on top of the dog:
  `cardboard` is light, `wood` is medium, and `metal` is heavy. Heavier loads
  make the body lower and slightly longer, with a wider leg stance for visual
  feedback even before speed changes are wired into runtime logic.
- Shelves are pallet racks with four screen directions: NE, SE, SW, NW. They
  are generated from model coordinates, not image-rotated. Current rack sizes
  are `1x2` and `1x3`, both standard two-tier versions.
- Rack visuals include green punched upright frames, orange load beams, quiet
  back rails, diagonal end-frame bracing, footplates, pallets, and SKU boxes.
- Rack cargo materials are `cardboard`, `wood`, and `metal`.
- Rack fill states are `full`, `half`, `almost_none`, and `empty`.
- Rack sprite naming pattern:
  `pallet_rack_1x{2|3}_{ne|se|sw|nw}_{cardboard|wood|metal}_{full|half|almost_none|empty}`.
  This produces `96` rack sprites for runtime replacement.
- Rack picking faces are intentionally open so robots can visually access the
  pallets from the aisle. Back faces use subdued horizontal support rails rather
  than large X bracing so the rack does not read as sealed.
- All sprite-sheet cells are square in the manifest `rect`. The `art_size`
  field records the non-square visual art size before transparent padding.
- Output is organized by functional category: `floor/`, `LED/`, `robot_dog/`,
  `rack/`, and `visual/`. There is no packed catch-all review folder.
- Warehouse fixtures are larger and more specific: animated dark isometric
  Macintosh-inspired 1x1 order server with RGB LEDs, four-way roll-up/sectional
  exit gate, conveyor bed, moving rollers, moving parcels, control post, and
  optional rear warehouse walls.
- Visual fixture animation naming:
  - `computer_terminal_1x1_frame_{00|01|02|03}`
  - `exit_gate_conveyor_3x1_{e|s|w|n}_frame_{00|01|02|03}`
- Exit gates use sectional roll-up door slats. The belt rollers and parcels
  shift between frames so runtime can loop the conveyor without redrawing art.
  Direction names are cardinal tile/world directions, not screen-space labels.
- Wall modules assume one tile is roughly `1.5m x 1.5m` in-world. `h3m` is a
  single wall level, while `h6m` is a taller two-level wall module.
- Wall module naming:
  - `warehouse_wall_segment_{ne|nw}_h{3|6}m`
  - `warehouse_wall_corner_back_h{3|6}m`
- Each sprite is rendered on its own transparent canvas before packing into the
  sheet, so extended robot arms and rack bracing cannot leak into neighboring
  sprite cells.

## Current Sprite Categories

- Floor:
  - `floor_concrete_01` ... `floor_concrete_08`
- LED overlays:
  - `led_edge_pick_orange`
  - `led_edge_delivery_green`
  - `led_edge_robot_route_cyan`
  - `led_edge_congestion_red`
- Robot:
  - `robot_dog_base_n`
  - `robot_dog_base_ne`
  - `robot_dog_base_e`
  - `robot_dog_base_se`
  - `robot_dog_base_s`
  - `robot_dog_base_sw`
  - `robot_dog_base_w`
  - `robot_dog_base_nw`
  - `robot_dog_carry_cardboard_{n|ne|e|se|s|sw|w|nw}`
  - `robot_dog_carry_wood_{n|ne|e|se|s|sw|w|nw}`
  - `robot_dog_carry_metal_{n|ne|e|se|s|sw|w|nw}`
- Shelf:
  - `pallet_rack_1x2_ne_cardboard_full`
  - `pallet_rack_1x2_ne_cardboard_half`
  - `pallet_rack_1x2_ne_cardboard_almost_none`
  - `pallet_rack_1x2_ne_cardboard_empty`
  - plus all direction, material, fill-state, and `1x3` variants
- Warehouse fixtures:
  - `depot_zone_2x2`
  - `computer_terminal_1x1_frame_{00|01|02|03}`
  - `exit_gate_conveyor_3x1_{e|s|w|n}_frame_{00|01|02|03}`
  - `warehouse_wall_segment_{ne|nw}_h{3|6}m`
  - `warehouse_wall_corner_back_h{3|6}m`

## Files

- `floor/floor_sprite_sheet_v23.png`
- `floor/floor_contact_v23.png`
- `floor/floor_manifest_v23.json`
- `LED/LED_sprite_sheet_v23.png`
- `LED/LED_contact_v23.png`
- `LED/LED_manifest_v23.json`
- `robot_dog/robot_dog_sprite_sheet_v23.png`
- `robot_dog/robot_dog_contact_v23.png`
- `robot_dog/robot_dog_on_tile_contact_v23.png`
- `robot_dog/robot_dog_cargo_matrix_v23.png`
- `robot_dog/robot_dog_manifest_v23.json`
- `rack/rack_sprite_sheet_v23.png`
- `rack/pallet_rack_contact_v23.png`
- `rack/pallet_rack_state_matrix_v23.png`
- `rack/rack_manifest_v23.json`
- `visual/visual_sprite_sheet_v23.png`
- `visual/visual_contact_v23.png`
- `visual/visual_animation_matrix_v23.png`
- `visual/visual_manifest_v23.json`
- `generate_sprites.py`: reproducible sprite generator

Only the current version and the immediately previous version should stay in
the sprite folders. For example, while v23 is current, keep v23 and v22 assets
and remove v1-v21 outputs.

## Regenerate

```bash
python3 submissions/warehouse_quadbot_atomic_demos/ui/sprites/generate_sprites.py
```
