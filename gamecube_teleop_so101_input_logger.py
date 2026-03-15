import argparse
import time

import pygame


def fmt(v: float) -> str:
    return f'{v:.3f}'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='COM4')
    ap.add_argument('--joy-index', type=int, default=0)
    ap.add_argument('--deadzone', type=float, default=0.12)
    ap.add_argument('--poll-hz', type=float, default=60.0)
    args = ap.parse_args()

    pygame.init()
    pygame.joystick.init()

    count = pygame.joystick.get_count()
    if count <= args.joy_index:
        raise RuntimeError(f'Joystick index {args.joy_index} unavailable; detected {count} joystick(s).')

    joy = pygame.joystick.Joystick(args.joy_index)
    joy.init()

    num_axes = joy.get_numaxes()
    num_buttons = joy.get_numbuttons()
    num_hats = joy.get_numhats()

    print(f'Using joystick #{args.joy_index}: {joy.get_name()}')
    print(f'Axes: {num_axes}')
    print(f'Buttons: {num_buttons}')
    print(f'Hats: {num_hats}')
    print('Logging button presses/releases and axis movements. Press Ctrl+C to quit.')

    prev_axes = [joy.get_axis(i) for i in range(num_axes)]
    prev_buttons = [joy.get_button(i) for i in range(num_buttons)]
    prev_hats = [joy.get_hat(i) for i in range(num_hats)]
    poll_dt = 1.0 / max(1.0, args.poll_hz)

    try:
        while True:
            pygame.event.pump()
            now = time.strftime('%H:%M:%S')

            for i in range(num_axes):
                value = joy.get_axis(i)
                changed = abs(value - prev_axes[i]) >= args.deadzone
                left_deadzone = abs(value) < args.deadzone and abs(prev_axes[i]) >= args.deadzone
                if changed or left_deadzone:
                    print(f'[{now}] axis{i}: {fmt(prev_axes[i])} -> {fmt(value)}')
                    prev_axes[i] = value

            for i in range(num_buttons):
                value = joy.get_button(i)
                if value != prev_buttons[i]:
                    state = 'pressed' if value else 'released'
                    print(f'[{now}] button{i}: {state}')
                    prev_buttons[i] = value

            for i in range(num_hats):
                value = joy.get_hat(i)
                if value != prev_hats[i]:
                    print(f'[{now}] hat{i}: {prev_hats[i]} -> {value}')
                    prev_hats[i] = value

            time.sleep(poll_dt)
    except KeyboardInterrupt:
        print('Stopped.')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
