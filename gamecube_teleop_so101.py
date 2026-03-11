import argparse
import time

import pygame

from lerobot.robots.so_follower import SOFollower, SOFollowerRobotConfig


JOINTS = [
    'shoulder_pan.pos',
    'shoulder_lift.pos',
    'elbow_flex.pos',
    'wrist_flex.pos',
    'wrist_roll.pos',
    'gripper.pos',
]


def clamp(v: float) -> float:
    return max(-100.0, min(100.0, float(v)))


def dz(x: float, deadzone: float) -> float:
    return 0.0 if abs(x) < deadzone else x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='COM4')
    ap.add_argument('--joy-index', type=int, default=0)
    ap.add_argument('--hz', type=float, default=30.0)
    ap.add_argument('--deadzone', type=float, default=0.12)
    args = ap.parse_args()

    pygame.init()
    pygame.joystick.init()

    n = pygame.joystick.get_count()
    if n <= args.joy_index:
        raise RuntimeError(f'Joystick index {args.joy_index} unavailable; detected {n} joystick(s).')

    joy = pygame.joystick.Joystick(args.joy_index)
    joy.init()

    arm = SOFollower(SOFollowerRobotConfig(port=args.port, id=None, disable_torque_on_disconnect=False))
    arm.connect()

    try:
        obs = arm.get_observation()
        pose = {k: float(obs[k]) for k in JOINTS}
        home = dict(pose)

        print(f'Using joystick #{args.joy_index}: {joy.get_name()}')
        print('Controls:')
        print('- Left stick: shoulder pan/lift')
        print('- Right/C stick: wrist roll/flex')
        print('- Triggers: elbow flex (R raise, L lower)')
        print('- A: open gripper, B: close gripper')
        print('- X: return home pose')
        print('- Start(7) or button 9: quit')

        dt_target = 1.0 / max(1.0, args.hz)

        while True:
            t0 = time.time()
            pygame.event.pump()

            # Axis mapping (GameCube USB adapters commonly expose 6 axes)
            ax0 = dz(joy.get_axis(0), args.deadzone)  # left x
            ax1 = dz(joy.get_axis(1), args.deadzone)  # left y
            ax3 = dz(joy.get_axis(3), args.deadzone)  # right x / c-stick x
            ax4 = dz(joy.get_axis(4), args.deadzone)  # right y / c-stick y
            ax2 = joy.get_axis(2)  # L trigger axis
            ax5 = joy.get_axis(5)  # R trigger axis

            # Convert trigger axes to [0, 1]
            l_trig = max(0.0, (ax2 + 1.0) * 0.5)
            r_trig = max(0.0, (ax5 + 1.0) * 0.5)

            # Speeds in normalized units per second
            pan_speed = 55.0
            lift_speed = 55.0
            elbow_speed = 70.0
            wrist_roll_speed = 90.0
            wrist_flex_speed = 70.0
            grip_speed = 90.0

            # Integrate target pose
            pose['shoulder_pan.pos'] = clamp(pose['shoulder_pan.pos'] + ax0 * pan_speed * dt_target)
            pose['shoulder_lift.pos'] = clamp(pose['shoulder_lift.pos'] - ax1 * lift_speed * dt_target)
            pose['wrist_roll.pos'] = clamp(pose['wrist_roll.pos'] + ax3 * wrist_roll_speed * dt_target)
            pose['wrist_flex.pos'] = clamp(pose['wrist_flex.pos'] - ax4 * wrist_flex_speed * dt_target)
            pose['elbow_flex.pos'] = clamp(pose['elbow_flex.pos'] + (r_trig - l_trig) * elbow_speed * dt_target)

            # Buttons
            b_a = joy.get_button(0)
            b_b = joy.get_button(1)
            b_x = joy.get_button(2)
            b_start7 = joy.get_button(7)
            b_9 = joy.get_button(9) if joy.get_numbuttons() > 9 else 0

            if b_a:
                pose['gripper.pos'] = clamp(pose['gripper.pos'] + grip_speed * dt_target)
            if b_b:
                pose['gripper.pos'] = clamp(pose['gripper.pos'] - grip_speed * dt_target)
            if b_x:
                pose = dict(home)
            if b_start7 or b_9:
                print('Quit pressed.')
                break

            arm.send_action(pose)

            elapsed = time.time() - t0
            sleep_t = dt_target - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)

    finally:
        try:
            arm.disconnect()
        finally:
            pygame.quit()
            print('Disconnected.')


if __name__ == '__main__':
    main()
