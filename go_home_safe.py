from lerobot.robots.so_follower import SOFollower, SOFollowerRobotConfig
import time, math

# Home pose tuned from your earlier stable readings
HOME = {
    'shoulder_pan.pos': -6.0,
    'shoulder_lift.pos': -99.0,
    'elbow_flex.pos': 99.5,
    'wrist_flex.pos': 2.0,
    'wrist_roll.pos': 1.0,
    'gripper.pos': 4.0,
}

arm = SOFollower(SOFollowerRobotConfig(port='COM4', id=None, disable_torque_on_disconnect=False))
arm.connect()

try:
    obs = arm.get_observation()
    keys = list(HOME.keys())
    cur = {k: float(obs[k]) for k in keys}

    def clamp(v):
        return max(-100.0, min(100.0, float(v)))

    # Stage 1: neutralize wrist roll / slightly open gripper first.
    stage1 = dict(cur)
    stage1['wrist_roll.pos'] = HOME['wrist_roll.pos']
    stage1['gripper.pos'] = max(cur['gripper.pos'], HOME['gripper.pos'])

    # Stage 2: partially lift/fold before final home.
    stage2 = dict(stage1)
    stage2['shoulder_lift.pos'] = -70.0
    stage2['elbow_flex.pos'] = 80.0
    stage2['wrist_flex.pos'] = 8.0
    stage2['shoulder_pan.pos'] = -3.0

    def move_to(target, duration=1.2, steps=30):
        start = dict(cur)
        for i in range(steps + 1):
            t = i / steps
            e = 0.5 - 0.5 * math.cos(math.pi * t)
            cmd = {}
            for k in keys:
                v = start[k] + (target[k] - start[k]) * e
                cmd[k] = clamp(v)
            arm.send_action(cmd)
            time.sleep(max(0.01, duration / steps))
        cur.update(target)

    move_to(stage1, duration=0.7, steps=18)
    move_to(stage2, duration=1.2, steps=30)
    move_to(HOME, duration=1.8, steps=40)

    print('ARRIVED_HOME', {k: round(v,2) for k,v in HOME.items()})
finally:
    arm.disconnect()
    print('DONE')
