# Demo Video Script / Provenance

Final video has been rebuilt and included as `demo.mp4`. This file now records the program-only requirement and source provenance.

## Current Submitted Video

- Output: `submissions/warehouse_quadbot_atomic_demos/demo.mp4`
- Duration: 1:25.00
- Resolution: 1280x720
- Size: approximately 3.75 MB
- Builder: `python examples/build_program_only_demo_video.py`
- Manifest: `submissions/warehouse_quadbot_atomic_demos/outputs/program_only_demo_manifest.json`

## Compliance Rule

All moving footage must come from real program output. The submitted video uses:

- Web runtime recording: `outputs/runtime_live_decision_replay.mp4`
- Chrome capture of the current UI: `docs/screenshots/mission_control_program_only.png`
- MuJoCo renderer clips from `outputs/physics_evidence/`
- MuJoCo generated contact sheet
- Generated title cards, captions, and benchmark text

No AI-generated moving video clip is used.

## Segment Outline

1. Program-only title card
2. Current Web runtime UI capture
3. Live runtime decision replay
4. Human-intrusion metric card
5. 30-robot benchmark metric card
6. MuJoCo fleet corridor clip
7. MuJoCo 6-DOF grasp clip
8. MuJoCo handoff clip
9. MuJoCo heterogeneous end-effector clip
10. MuJoCo contact sheet
11. Closing validation card
