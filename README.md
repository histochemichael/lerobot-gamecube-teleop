# LeRobot GameCube Teleop

Use a GameCube controller to drive an SO101 follower arm through upstream [LeRobot](https://github.com/huggingface/lerobot).

This repository is intentionally small. It does not vendor LeRobot or modify its internals. It only provides a GameCube-specific teleop script plus a controller input logger.

## Included Scripts

- `scripts/gamecube_input_logger.py`
  - Logs joystick axes, button presses, and hat changes so you can confirm your adapter mapping.
- `scripts/gamecube_teleop_so101.py`
  - Sends GameCube controller input to an SO101 follower arm through `lerobot`.

## Hardware And Software

You will need:

- An SO101 follower arm supported by `lerobot`
- A GameCube controller
- A USB GameCube adapter recognized by your OS as a joystick
- Python 3.10+
- A working `lerobot` installation

## Install

Create and activate a virtual environment, then install the runtime dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install lerobot pygame
```

If your SO101 setup needs any extra platform-specific steps, follow the upstream LeRobot setup first.

## How It Works

This project depends on upstream `lerobot` and `pygame`. It does not replace LeRobot, bundle LeRobot source, or patch LeRobot internals.

## 1. Check Controller Mapping First

Run the logger before moving the robot so you can confirm the correct joystick index and button numbering:

```powershell
python .\scripts\gamecube_input_logger.py --joy-index 0 --deadzone 0.12 --poll-hz 60
```

Move the sticks, press the triggers, and tap each button. If your adapter reports a different mapping than the defaults used here, adjust the teleop script before testing on hardware.

## 2. Start Teleop

After confirming the mapping, run teleop:

```powershell
python .\scripts\gamecube_teleop_so101.py --port COM4 --joy-index 0 --hz 30 --deadzone 0.12
```

The script samples trigger baselines at startup, then enters the control loop.

## Default Controls

| GameCube input | Robot action |
| --- | --- |
| Left stick | Shoulder pan / shoulder lift |
| Right / C-stick | Wrist roll |
| Up / C-stick | Wrist flex forward |
| L trigger | Wrist flex backward |
| `Y` | Raise elbow flex |
| `X` | Lower elbow flex |
| `A` | Open gripper |
| `B` | Close gripper |
| `X + Y + Z` | Return to home pose captured at startup |
| `Start` or button `9` | Quit |

## CLI Options

### `gamecube_input_logger.py`

- `--joy-index`  
  Joystick index to read from
- `--deadzone`  
  Minimum axis change before logging movement
- `--poll-hz`  
  Polling rate for joystick events

### `gamecube_teleop_so101.py`

- `--port`  
  Serial port for the SO101 follower arm
- `--joy-index`  
  Joystick index to read from
- `--hz`  
  Teleop update rate
- `--deadzone`  
  Deadzone for analog inputs and trigger calibration

## Controller Diagram

When your images are ready, place them here:

- `docs/images/controller-map.png`
- `docs/images/demo.gif`

Then enable these lines:

```md
![GameCube controller mapping](docs/images/controller-map.png)
![Teleop demo](docs/images/demo.gif)
```

## Safety

- Start with the arm clear of people, cables, and obstacles.
- Keep one hand ready to quit immediately during first movement tests.
- Verify the COM port, joint directions, and trigger calibration before doing larger motions.
- Run the logger first whenever you change controller, adapter, or OS.

## Troubleshooting

### Controller Not Detected

- Confirm the adapter is connected before launching the script.
- Check how many joysticks `pygame` sees and adjust `--joy-index`.
- Re-run the logger to confirm the OS is exposing the controller as a joystick.

### Wrong Joystick Index

- If you have multiple controllers connected, the GameCube adapter may not be joystick `0`.
- Run the logger with different `--joy-index` values until the reported device name matches your controller.

### Wrong COM Port

- Confirm the SO101 follower is on the port passed to `--port`.
- If connection fails immediately, re-check the port assignment in Device Manager or your serial tool.

### Trigger Calibration Looks Wrong

- Leave both triggers fully released during startup calibration.
- Restart teleop if the adapter was touched during the baseline sampling window.
- Use the logger to verify which physical triggers map to which joystick axes on your system.

## Attribution

This project is built to work with upstream [LeRobot](https://github.com/huggingface/lerobot). If you later start modifying LeRobot itself, keep those changes in a separate upstream-tracking fork rather than in this repo.

## License

Apache-2.0 is a reasonable default for this repo.
