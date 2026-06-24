# MuJoCo Load And Clearance Evidence

This report makes two judge-facing physical checks explicit: payload response and multi-robot close-clearance safety.

## Dimension 8: Load Impact

| Payload | Mass | Measured speed | Body drop vs empty | Basket contacts | Package z motion |
| --- | ---: | ---: | ---: | ---: | ---: |
| empty | 0.0 kg | 0.5846 m/s (0.0%) | 0.0 m | 0 | 0.0 m |
| light_cardboard | 0.8 kg | 0.4889 m/s (-16.3702%) | 0.01 m | 50 | 0.0174 m |
| medium_wood | 2.0 kg | 0.372 m/s (-36.3667%) | 0.04 m | 50 | 0.0174 m |
| heavy_metal | 4.0 kg | 0.2657 m/s (-54.5501%) | 0.075 m | 50 | 0.0174 m |

**Plain-language result:** heavier boxes make the quadbot slower and lower. The heavy metal case is 54.5501% slower than empty walking and drops the body by 0.075 m, while the package remains basket-contact stable.

Checks: `{"empty_light_medium_heavy_gait_differences": true, "heavy_load_body_posture_change": true, "heavy_load_speed_decrease": true, "heavy_load_turn_slope_stability_proxy": true}`

## Dimension 10: Multi-Robot Close Clearance

| Evidence | Value |
| --- | ---: |
| Robots in MuJoCo corridor scene | 3 |
| Minimum robot spacing | 0.6174 m |
| Minimum obstacle/package clearance | 0.2307 m |
| Robot-obstacle contacts | 0 |
| Box-obstacle contacts | 0 |
| Gripper-box contacts | 458 |
| Receiver-gripper-box contacts | 192 |
| Box-basket contacts | 190 |

**Plain-language result:** the corridor test proves a tight three-robot situation with the package sticking out, while still reporting zero robot-obstacle and zero package-obstacle collisions.

Checks: `{"protruding_package_collision_detection": true, "robot_body_collision_detection": true, "three_robots_narrow_corridor": true, "two_robots_near_pass_clearance": true}`

## Files

- `outputs/physics_evidence/load_impact_scorecard.json`
- `outputs/physics_evidence/multi_robot_clearance_scorecard.json`
- `outputs/physics_evidence/fleet_physics_corridor.mp4`
- `outputs/physics_evidence/fleet_physics_corridor_trajectory.json`
- `outputs/physics_evidence/loaded_walk_cardboard.mp4`
- `outputs/physics_evidence/loaded_walk_wood.mp4`
- `outputs/physics_evidence/loaded_walk_metal.mp4`
