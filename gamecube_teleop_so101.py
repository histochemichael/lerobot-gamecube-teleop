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


L_TRIGGER_AXIS = 2
R_TRIGGER_AXIS = 5


def clamp(v: float) -> float:
    return max(-100.0, min(100.0, float(v)))


def dz(x: float, deadzone: float) -> float:
    return 0.0 if abs(x) < deadzone else x


def sample_axis_baseline(joy: pygame.joystick.Joystick, axis: int, samples: int = 20, delay_s: float = 0.01) -> float:
    vals: list[float] = []
    for _ in range(samples):
        pygame.event.pump()
        vals.append(joy.get_axis(axis))
        time.sleep(delay_s)
    return sum(vals) / len(vals)


def trigger_level(raw: float, baseline: float, deadzone: float) -> float:
    delta = raw - baseline
    if abs(delta) <= deadzone:
        return 0.0
    return min(1.0, max(0.0, delta))


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
        print('Leave both triggers unpressed for calibration...')
        l_base = sample_axis_baseline(joy, L_TRIGGER_AXIS)
        r_base = sample_axis_baseline(joy, R_TRIGGER_AXIS)
        print(f'Trigger baselines: L axis{L_TRIGGER_AXIS}={l_base:.3f}, R axis{R_TRIGGER_AXIS}={r_base:.3f}')
        print('Controls:')
        print('- Left stick: shoulder pan/lift')
        print('- Right/C stick: wrist roll')
        print('- R trigger: wrist flex forward')
        print('- L trigger: wrist flex backward')
        print('- X/Y: elbow flex (X lower, Y raise)')
        print('- A: open gripper, B: close gripper')
        print('- X + Y + Z: return home pose')
        print('- Start(7) or button 9: quit')

        dt_target = 1.0 / max(1.0, args.hz)
        last_report = None

        while True:
            t0 = time.time()
            pygame.event.pump()

            ax0 = dz(joy.get_axis(0), args.deadzone)
            ax1 = dz(joy.get_axis(1), args.deadzone)
            ax3 = dz(joy.get_axis(3), args.deadzone)
            l_trig = trigger_level(joy.get_axis(L_TRIGGER_AXIS), l_base, args.deadzone)
            r_trig = trigger_level(joy.get_axis(R_TRIGGER_AXIS), r_base, args.deadzone)
            wrist_delta = r_trig - l_trig

            report = (round(l_trig, 2), round(r_trig, 2), round(wrist_delta, 2))
            if report != last_report and (l_trig > 0.0 or r_trig > 0.0):
                print(f'Trigger input: L=axis{L_TRIGGER_AXIS} ({l_trig:.2f}) R=axis{R_TRIGGER_AXIS} ({r_trig:.2f}) wrist_delta={wrist_delta:.2f}')
                last_report = report
            elif l_trig == 0.0 and r_trig == 0.0 and last_report is not None:
                print('Trigger input: idle')
                last_report = None

            pan_speed = 55.0
            lift_speed = 55.0
            elbow_speed = 70.0
            wrist_roll_speed = 90.0
            wrist_flex_speed = 70.0
            grip_speed = 90.0

            pose['shoulder_pan.pos'] = clamp(pose['shoulder_pan.pos'] + ax0 * pan_speed * dt_target)
            pose['shoulder_lift.pos'] = clamp(pose['shoulder_lift.pos'] - ax1 * lift_speed * dt_target)
            pose['wrist_roll.pos'] = clamp(pose['wrist_roll.pos'] + ax3 * wrist_roll_speed * dt_target)
            pose['wrist_flex.pos'] = clamp(pose['wrist_flex.pos'] + wrist_delta * wrist_flex_speed * dt_target)

            b_a = joy.get_button(0)
            b_b = joy.get_button(1)
            b_x = joy.get_button(2)
            b_y = joy.get_button(3) if joy.get_numbuttons() > 3 else 0
            b_z = joy.get_button(4) if joy.get_numbuttons() > 4 else 0
            b_start7 = joy.get_button(7)
            b_9 = joy.get_button(9) if joy.get_numbuttons() > 9 else 0

            pose['elbow_flex.pos'] = clamp(pose['elbow_flex.pos'] + (b_y - b_x) * elbow_speed * dt_target)

            if b_a:
                pose['gripper.pos'] = clamp(pose['gripper.pos'] + grip_speed * dt_target)
            if b_b:
                pose['gripper.pos'] = clamp(pose['gripper.pos'] - grip_speed * dt_target)

            if b_x and b_y and b_z:
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
