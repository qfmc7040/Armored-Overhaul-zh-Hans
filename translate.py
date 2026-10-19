#!/usr/bin/env python3
"""Translate Armored Overhaul in-game menu texts (ModOptionsMenu rows,
ModBindingsMenu entries and the shared category name) inside the extracted
patch lua sources. The rule sets follow the mod's current layout: 3.4.0 moved
each option's title/choices/description into the PARTS table of a shared
source, and 3.5.1 split Turret Aim Range into Gun Depression + Gun Raise,
added Collision Damage, and gave Turret Core a Freelook binding.

Rules are exact source segments; every rule carries the match count expected
in each file that carries it, so any drift aborts instead of silently skipping.

Vehicle names follow the community wiki data (terms.json, stratagems_full.json):
Bastion=堡垒, Maelstrom=风暴漩涡, FRV=快速侦察载具, Exosuit=外骨骼装甲.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'extracted'
DST = ROOT / 'extracted_zh'

ZH = '装甲强化'
SPEC_MOD = ("spec.mod = 'ARMORED OVERHAUL'", "spec.mod = '%s'" % ZH)
BIND_CAT = ("{category = 'ARMORED OVERHAUL'}", "{category = '%s'}" % ZH)

# (3.4.0) handling family (Top Speed / Engine Torque / Grip / gear shifts /
# Stability): one source per option and every copy carries the whole PARTS
# table, so all five files share these texts.
HANDLING_RULES = [
    ("title = 'Tank Top Speed'", "title = '坦克极速'", 1),
    ("choices = {'Off', 'Fast (x1.1)', 'Faster (x1.15)', 'Fastest (x1.3)'}",
     "choices = {'关闭', '快 (x1.1)', '更快 (x1.15)', '最快 (x1.3)'}", 1),
    ("description = 'A faster Bastion and Maelstrom: more engine speed and pulling power, forward and in reverse. Changes the tank you are in at once.'",
     "description = '更快的堡垒与风暴漩涡：发动机转速与牵引力更强，前进和倒车都受益。你所在的那辆坦克立即生效。'", 1),
    ("title = 'Tank Engine Torque'", "title = '坦克发动机扭矩'", 1),
    ("choices = {'Off', 'Strong (x1.2)', 'Stronger (x1.35)', 'Strongest (x1.5)'}",
     "choices = {'关闭', '强 (x1.2)', '更强 (x1.35)', '最强 (x1.5)'}", 1),
    ("description = 'More engine torque for the Bastion and Maelstrom: quicker off the line and up slopes. Changes the tank you are in at once.'",
     "description = '增强堡垒与风暴漩涡的发动机扭矩：起步与爬坡更快。你所在的那辆坦克立即生效。'", 1),
    ("title = 'Tank Grip'", "title = '坦克抓地力'", 1),
    ("choices = {'Off', 'Moderate (x1.2)', 'Strong (x1.35)', 'Maximum (x1.5)'}",
     "choices = {'关闭', '适中 (x1.2)', '强 (x1.35)', '最强 (x1.5)'}", 1),
    ("description = 'More track grip for the Bastion and Maelstrom: less sliding on slopes and in turns. Changes the tank you are in at once.'",
     "description = '增强堡垒与风暴漩涡的履带抓地力：在斜坡上和转弯时更少打滑。你所在的那辆坦克立即生效。'", 1),
    ("title = 'Tank Throttle Response (gear changes)'", "title = '坦克油门响应（换挡）'", 1),
    ("choices = {'Off', 'Quick', 'Quicker', 'Instant'}", "choices = {'关闭', '快', '更快', '瞬时'}", 1),
    ("title = 'Tank Stability'", "title = '坦克稳定性'", 1),
    ("choices = {'Off', 'Stable', 'Steady', 'Planted'}", "choices = {'关闭', '稳定', '沉稳', '稳健'}", 1),
    ("description = 'Keeps the Bastion and Maelstrom on the ground: pressed down harder the faster they go, so they stay flat over crests and bumps instead of floating. Changes the tank you are in at once.'",
     "description = '让堡垒与风暴漩涡紧贴地面：车速越快下压力越大，越过坡顶和颠簸时车身保持平稳而不发飘。你所在的那辆坦克立即生效。'", 1),
]

# (3.4.0) steering / throttle family: same PARTS scheme, two options per copy
STEERING_RULES = [
    ("title = 'Tank Steering'", "title = '坦克转向'", 1),
    ("choices = {'Off', 'Responsive (x1.25)', 'Quick (x1.5)', 'Sharp (x2)'}",
     "choices = {'关闭', '灵敏 (x1.25)', '快 (x1.5)', '锐利 (x2)'}", 1),
    ("description = 'Quicker steering for the Bastion and Maelstrom: they start and stop turning sooner. Changes every tank at once.'",
     "description = '加快堡垒与风暴漩涡的转向：更快开始和停止转弯。所有坦克立即生效。'", 1),
    ("title = 'Tank Throttle Response'", "title = '坦克油门响应'", 1),
    ("choices = {'Off', 'Quick', 'Quicker', 'Instant'}", "choices = {'关闭', '快', '更快', '瞬时'}", 1),
    ("description = 'Snappier Bastion and Maelstrom: the throttle and brake let go sooner, and gear and direction changes wait less (Instant: no wait). Changes every tank at once.'",
     "description = '堡垒与风暴漩涡的反应更干脆：油门与刹车松开得更快，换挡与变向的等待更短（瞬时：无等待）。所有坦克立即生效。'", 1),
]

# hash -> list of (old, new, expected count in that file)
RULES = {
    # Tank Core: autoloader + gunner drive rows, GD choice names, bindings
    '5F6C588CECAB9733': [
        ("label = 'Tank Autoloader', default = true, description = 'The Bastion and Maelstrom main gun reloads by itself when it runs dry, at the normal reload speed (perks count). You can still reload by hand.'",
         "label = '坦克自动装弹机', default = true, description = '堡垒与风暴漩涡的主炮在弹药打空后自动装填，装填速度与手动相同（技能加成有效）。仍可手动装填。'", 1),
        ("{name = 'Off', tanks = false, frv = false}",
         "{name = '关闭', tanks = false, frv = false}", 2),
        ("{name = 'Tanks and FRV', tanks = true, frv = true}",
         "{name = '坦克与快速侦察载具', tanks = true, frv = true}", 1),
        ("{name = 'Tanks', tanks = true, frv = false}",
         "{name = '坦克', tanks = true, frv = false}", 1),
        ("{name = 'FRV', tanks = false, frv = true}",
         "{name = '快速侦察载具', tanks = false, frv = true}", 1),
        ("label = 'Gunner Drive', choices = names, default = 2, description = 'Drive from the gunner seat when the driver seat is empty: your movement keys drive, shift and CTRL change gear, Space is the handbrake, F the horn, Mouse 3 the Maelstrom\\'s smoke. Controller: the left stick drives, its click is the horn, the right stick click pops smoke. Mod Bindings Menu keys replace Forward, Back, Handbrake, Horn and Smoke. A teammate at the wheel drives. Pick which vehicles.'",
         "label = '炮手驾驶', choices = names, default = 2, description = '驾驶员座位空着时，可从炮手席驾驶载具：移动键驾驶，Shift 与 CTRL 换挡，空格为手刹；F 鸣笛，鼠标中键打出风暴漩涡的烟雾。手柄：左摇杆驾驶，按下左摇杆鸣笛，按下右摇杆打烟雾。模组绑定菜单中的按键可替代前进、后退、手刹、鸣笛与烟雾。队友坐进驾驶位则由其驾驶。选择适用的载具。'", 1),
        ("'Gunner Drive: Forward'", "'炮手驾驶：前进'", 1),
        ("'Gunner Drive: Back'", "'炮手驾驶：后退'", 1),
        ("'Gunner Drive: Handbrake'", "'炮手驾驶：手刹'", 1),
        ("'Gunner Drive: Horn'", "'炮手驾驶：鸣笛'", 1),
        ("'Gunner Drive: Smoke (Maelstrom)'", "'炮手驾驶：烟雾（风暴漩涡）'", 1),
    ],
    # Turret Core: position / traverse / elevation / aim range rows
    '1AC7D6D7F0E75FFB': [
        ("label = 'Tank Turret Position',", "label = '坦克炮塔位置',", 1),
        ("choices = {'Original', 'Centered'}, default = 1,", "choices = {'原版', '居中'}, default = 1,", 1),
        ("description = 'MBT Turrets: where the Bastion and Maelstrom turret sits. Original is the game\\'s place. Centered puts it in the middle of the hull like a main battle tank: the gun reaches past the front deck, so it clips less when aimed low. Changes at once. The tank\\'s hit areas stay the game\\'s own.'",
         "description = '主战坦克炮塔：调整堡垒与风暴漩涡炮塔的位置。原版为游戏自带的位置。居中会把炮塔移到车体中部，如同真正的主战坦克：炮管可以越过前甲，向下瞄准时穿模更少。立即生效。坦克的受击区域保持游戏原样。'", 1),
        ("label = 'Tank Turret Traverse',", "label = '坦克炮塔回转速度',", 1),
        ("choices = {'Off', 'Quick (x1.5)', 'Fast (x2)', 'Very fast (x3)'}, default = pick_of(TRAVERSE_SPEEDS, o.traverse),",
         "choices = {'关闭', '较快 (x1.5)', '快 (x2)', '极快 (x3)'}, default = pick_of(TRAVERSE_SPEEDS, o.traverse),", 1),
        ("description = 'How fast the Bastion and Maelstrom turrets turn (the game: 25 degrees a second), and the gunner view left/right with them. Very fast is 75. Changes every tank at once; the view from the next time you sit in the gunner seat.'",
         "description = '堡垒与风暴漩涡炮塔的回转速度（游戏原版为每秒 25 度），炮手视角随炮塔一起左右转动。极快为每秒 75 度。所有坦克立即生效；视角自下次进入炮手席时改变。'", 1),
        ("label = 'Tank Turret Elevation',", "label = '坦克火炮俯仰速度',", 1),
        ("choices = {'Off', 'Quick (x1.25)', 'Fast (x1.5)', 'Very fast (x2)'}, default = pick_of(SPEEDS, o.elevation),",
         "choices = {'关闭', '较快 (x1.25)', '快 (x1.5)', '极快 (x2)'}, default = pick_of(SPEEDS, o.elevation),", 1),
        ("description = 'How fast the Bastion and Maelstrom guns move up and down (the game: 35 degrees a second), and the gunner view up/down with them. Changes every tank at once; the view from the next time you sit in the gunner seat.'",
         "description = '堡垒与风暴漩涡火炮的俯仰速度（游戏原版为每秒 35 度），炮手视角随火炮一起上下移动。所有坦克立即生效；视角自下次进入炮手席时改变。'", 1),
        ("label = 'Tank Gun Depression',", "label = '坦克火炮俯角',", 1),
        ("choices = {'Off', 'Low (6 below)', 'Lower (10 below)', 'Lowest (15 below)'}, default = pick,",
         "choices = {'关闭', '低（下压 6 度）', '更低（下压 10 度）', '最低（下压 15 度）'}, default = pick,", 1),
        ("description = 'How far down the Bastion and Maelstrom guns aim (the game: 3 degrees below level), and the gunner view down with them. Changes every tank at once; the view from the next time you sit in the gunner seat.'",
         "description = '堡垒与风暴漩涡火炮可向下瞄准的角度（游戏原版为低于水平 3 度），炮手视角随之下移。所有坦克立即生效；视角自下次进入炮手席时改变。'", 1),
        ("label = 'Tank Gun Raise',", "label = '坦克火炮仰角',", 1),
        ("choices = {'Off', 'High (30 above)', 'Higher (45 above)', 'Highest (60 above)'}, default = pick,",
         "choices = {'关闭', '高（上抬 30 度）', '更高（上抬 45 度）', '最高（上抬 60 度）'}, default = pick,", 1),
        ("description = 'How far up the Bastion and Maelstrom guns aim (the game: 25 degrees above level), and the gunner view up with them. Changes every tank at once; the view from the next time you sit in the gunner seat.'",
         "description = '堡垒与风暴漩涡火炮可向上瞄准的角度（游戏原版为高于水平 25 度），炮手视角随之上移。所有坦克立即生效；视角自下次进入炮手席时改变。'", 1),
        ("'Tank Turret: Freelook'", "'坦克炮塔：自由观察'", 1),
    ],
    # (3.5.1) Collision Damage: one toggle row
    'A223EC3A199F34E3': [
        ("label = 'Tank Collision Demolition Boost', default = true,", "label = '坦克碰撞拆毁强化', default = true,", 1),
        ("description = 'The faster the Bastion and Maelstrom drive into things, the harder they hit: demolition force 30 when crawling, 35 at half speed, 40 from three-quarter speed (walls, fences, small buildings). Works for the tank you drive; turning it off puts the game\\'s own back.'",
         "description = '堡垒与风暴漩涡撞上物体时车速越快、拆毁值越高：慢速时为 30，半速为 35，四分之三速及以上为 40（对围墙、栅栏、小型建筑）。对你所驾驶的那辆坦克生效；关闭后恢复游戏原本的数值。'", 1),
    ],
    # (3.4.0) handling family: one source per option (grip / torque / speed /
    # gear shifts / stability), five builds sharing the same PARTS texts
    '1F43A5BD3F9E8829': HANDLING_RULES,      # Tank Grip
    '418F81EAB72CD2E6': HANDLING_RULES,      # Tank Engine Torque
    '4C89F28021A44647': HANDLING_RULES,      # Tank Top Speed
    'F4DA43DFBBF5C440': HANDLING_RULES,      # Tank Stability
    'FF7ACC1FA237A691': HANDLING_RULES,      # gear changes of Throttle Response
    # (3.4.0) steering / throttle family
    'C133BEEB811C1854': STEERING_RULES,      # Tank Steering
    '36D38A89F1CD69B8': STEERING_RULES,      # Tank Throttle Response
    # Camera group + zoom bindings
    '8F7FD48E0ECA9B5E': [
        ("label = 'Tank Gunner Camera',", "label = '坦克炮手镜头',", 1),
        ("choices = {'Off', 'Close (about 1.5 m back)', 'Far (about 3.5 m back)', 'Farther (about 5 m back)', 'Farthest (about 6.5 m back)'}, default = MENU_PICK,",
         "choices = {'关闭', '近（后方约 1.5 米）', '远（后方约 3.5 米）', '更远（后方约 5 米）', '最远（后方约 6.5 米）'}, default = MENU_PICK,", 1),
        ("description = 'Puts the Bastion and Maelstrom gunner camera lower and further back so you see more around the tank. It stays behind the turret as it turns. The pick is where the camera starts: the mouse wheel (or the Mod Bindings Menu\\'s Zoom In / Zoom Out keys) moves it closer or further back, and from the closest point zooms in on the crosshair.'",
         "description = '将堡垒与风暴漩涡的炮手镜头放低并后移，让你能看清坦克周围更多情况；镜头在炮塔回转时始终跟在其后方。所选档位是进入时的初始机位：鼠标滚轮（或模组绑定菜单的拉近/拉远按键）可将镜头拉近或拉远，最近档会对准准星放大。'", 1),
        ("'Gunner Camera: Zoom In'", "'炮手镜头：拉近'", 1),
        ("'Gunner Camera: Zoom Out'", "'炮手镜头：拉远'", 1),
    ],
    # Driver Panel
    '78445AA48F6FB49E': [
        ("label = 'Driver Panel', default = true,", "label = '驾驶员面板', default = true,", 1),
        ("description = 'While you drive from the gunner seat with Gunner Drive, a panel like the driver\\'s own HUD shows the gear, rpm, speed, fuel and the Maelstrom\\'s smoke rounds. It only shows while you are the one driving. Only you see it.'",
         "description = '通过炮手驾驶从炮手席开车时，会显示一块与驾驶员 HUD 相同的面板，展示挡位、转速、车速、油量以及风暴漩涡的烟雾弹余量。仅在你实际驾驶时显示，且只有你自己可见。'", 1),
    ],
    # Vehicle Indicator
    '7D815785EAA72B5F': [
        ("label = 'Vehicle Indicator', default = true, description = 'A small outline of your vehicle shows where the gun points compared to the hull, colored by health (blue to red). Works in the Bastion, the Maelstrom and the M-102, M-103 and M-104 FRVs, in any seat; the FRVs\\' tires show their own health and go clear when popped. In the driver seat a bar shows the gunner\\'s ammo left (the M-103\\'s turret: any seat). Only you see it.'",
         "label = '载具指示器', default = true, description = '用一个载具轮廓小图标显示炮管相对车体的指向，并按生命值由蓝到红着色。适用于堡垒、风暴漩涡，以及 M-102、M-103 与 M-104 快速侦察载具，任何座位都有效；快速侦察载具的各个轮胎分别显示生命值，爆胎后该轮显示消失。坐在驾驶位时，一条进度条显示炮手剩余弹药（M-103 的炮塔则在任何座位都显示）。只有你自己可见。'", 1),
    ],
    # (3.6.0) Maelstrom Weapons: fire rate + single belt toggles (menu group 'maelstrom')
    '5C6913399380DB0C': [
        ("label = 'Maelstrom Fire Rate', default = true,", "label = '风暴漩涡射速', default = true,", 1),
        ("description = 'Hold reload in the Maelstrom\\'s gun seat to switch its main gun\\'s fire rate on the fly: 1200, 1800 (where it starts) or 2400 rounds a minute (the game: 1200 only); the new rate pops up by the ammo bar as the menu closes. A change here reaches the next Maelstrom called in, not one already out. Off: the game\\'s own.'",
         "description = '在风暴漩涡的炮手席按住装填键，即可随时切换主炮射速：每分钟 1200、1800（初始档位）或 2400 发（游戏原版只有 1200）；菜单关闭时会在弹药条旁显示新的射速。此处修改对之后召唤的风暴漩涡生效，已在场的无效。关闭后恢复游戏原本的射速。'", 1),
        ("label = 'Maelstrom Single Belt', default = true,", "label = '风暴漩涡单弹链', default = true,", 1),
        ("description = 'The Maelstrom\\'s main gun carries all its ammo on one belt (2,100 rounds) and never reloads: reload does nothing (hold it for the fire-rate choice when Maelstrom Fire Rate is on). A change here reaches the next Maelstrom called in, not one already out. Off: the game\\'s 300-round belts.'",
         "description = '风暴漩涡的主炮把所有弹药串成一条弹链（2100 发），永不装填：按装填键无效果（开启风暴漩涡射速时，按住装填键用于选择射速）。此处修改对之后召唤的风暴漩涡生效，已在场的无效。关闭后恢复游戏原本的 300 发弹链。'", 1),
    ],
    # (3.6.0) FRV Run Flat: one toggle row (menu group 'run_flat')
    '512401A3C373703F': [
        ("label = 'FRV Run-Flat Tires', default = true,", "label = '快速侦察载具防爆胎', default = true,", 1),
        ("description = 'The M-102, M-103 and M-104 FRVs\\' tires never pop, and the tires of the FRV you ride in stay at full health. Works when you host or play alone (in someone else\\'s game their game decides). Turning it off puts the game\\'s own back.'",
         "description = 'M-102、M-103 与 M-104 快速侦察载具的轮胎永不爆胎；你乘坐的快速侦察载具轮胎始终满生命值。仅在你是房主或单人游戏时有效（在他人房间中由对方的游戏决定）。关闭后恢复游戏原本的机制。'", 1),
    ],
    # Vehicle Loadout
    'F98C72F519463ACB': [
        ("label = 'Vehicle Loadout', default = true,", "label = '载具配置', default = true,", 1),
        ("description = 'Pick more than one tank, exosuit or FRV in your stratagem loadout (the game puts a second one in the first one\\'s slot). Changes at once; turning it off puts the game\\'s limit back.'",
         "description = '可在战备配置中选择多辆坦克、外骨骼装甲或快速侦察载具（游戏会把第二辆放进第一辆的栏位）。立即生效；关闭后恢复游戏原本的数量限制。'", 1),
    ],
}

# files that carry the shared category name; only these register bindings
BINDING_FILES = {'5F6C588CECAB9733', '8F7FD48E0ECA9B5E', '1AC7D6D7F0E75FFB'}
CARRIES_COMMON = set(RULES)


def main():
    problems = []
    if DST.exists():
        shutil.rmtree(DST)
    for folder in sorted(p for p in SRC.iterdir() if p.is_dir()):
        outdir = DST / folder.name
        outdir.mkdir(parents=True)
        for lua in sorted(folder.glob('*.lua')):
            stem = lua.stem.split('.')[0]
            text = lua.read_bytes().decode('utf-8')
            if stem in RULES or stem in CARRIES_COMMON:
                rules = [(SPEC_MOD[0], SPEC_MOD[1], 1),
                         (BIND_CAT[0], BIND_CAT[1], 1 if stem in BINDING_FILES else 0)]
                rules += RULES.get(stem, [])
                for old, new, expected in rules:
                    got = text.count(old)
                    if got != expected:
                        problems.append(f'{folder.name}/{lua.name}: rule matched {got}x (want {expected}): {old[:70]}...')
                        continue
                    text = text.replace(old, new)
            (outdir / lua.name).write_bytes(text.encode('utf-8'))
        for binf in sorted(folder.glob('*.bin')):
            shutil.copy2(binf, outdir / binf.name)
    if problems:
        print('\n'.join(problems))
        return 1
    total = sum(1 + len(RULES.get(p.stem.split('.')[0], []))
                for f in SRC.rglob('*.lua')
                for p in [f])
    print(f'translated lua sources -> {DST} (all rule counts verified)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
