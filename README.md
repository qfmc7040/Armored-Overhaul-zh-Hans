# Armored Overhaul 简体中文汉化（当前：3.4.0）

成品：`HD2\Armored-Overhaul-3.4.0-zh-Hans.zip`
（与原版同 GUID `370555ae-cb28-4b9d-96d0-8381505c3f89`，导入即原位更新）。
上一版 3.3.0 的成品仍在工作区根目录，可删。

## 汉化范围（游戏内全部会显示的模组文本）

3.4.0 共 **30 个菜单模块**全部汉化：

- **模组选项菜单（MODS 页，类别「装甲强化」）**：
  坦克极速 / 坦克发动机扭矩 / 坦克抓地力 / 坦克稳定性 / 坦克油门响应 /
  坦克油门响应（换挡）/ 坦克转向 / 坦克炮塔位置 / 坦克炮塔回转速度 /
  坦克火炮俯仰速度 / 坦克火炮俯仰范围 / 坦克炮手镜头 / 坦克自动装弹机 /
  炮手驾驶 / 驾驶员面板 / 载具指示器 / 载具配置——含全部下拉选项与描述。
- **模组绑定菜单（控制页 MODS 分区「装甲强化」）** 11 条按键：
  炮手驾驶：前进/后退/左转/右转/升挡/降挡/手刹/鸣笛/烟雾（风暴漩涡），
  炮手镜头：拉近/拉远。
- **术语**按社区 wiki 口径（`terms.json`/`stratagems_full.json`）：
  Bastion=堡垒，Maelstrom=风暴漩涡，FRV=快速侦察载具，Exosuit=外骨骼装甲。

### 版本差异备忘

| 版本 | 菜单模块 | 结构 | 规则表变更 |
|---|---|---|---|
| 3.3.0 | 18 | 文案写在各文件的 `menu_rows` 里 | 首版 9 个 hash 的规则 |
| 3.4.0 | 30 | 驾驶组 5 个选项合并为一套源码，文案移入 `PARTS` 表（`title`/`choices`/`description`）；新增 Top Speed / Engine Torque / Gear Shifts / Stability / Throttle Response 五组 | 新增 6 个 hash（4 组新选项 + 2 个家族源），改写 Camera 档位、Turret Core 三条描述 |


## 为什么是直接改 Lua 而不是翻译包

该模组把菜单文本**硬编码**在 Lua 里（`label = 'Tank Grip'` 等），
没有接 Bingus Text 翻译系统，翻译包（按 key 查表、未知 key 会被拒绝）无法覆盖；
因此从 patch 档案中解出 Lua 源码，替换字符串字面量后重建 patch。

## 目录内容

| 文件 | 作用 |
|---|---|
| `patch_tool.py` | HD2 Lua patch 档案（`9ba626afa44a3aa3.patch_0`）的 info / extract / build / verify 工具 |
| `update_zh.py` | **版本更新后的一键重汉化**：解包→diff→套规则→重建→校验→刷新 baseline |
| `translate.py` | 按"精确原文段落→中文"规则表替换菜单 Lua（每条规则校验命中次数，漂移即中止；规则集覆盖 3.3.0 与 3.4.0 两种结构） |
| `build_zh.py` | 回环验证 → 用译文重建全部含 Lua 的 patch（纯资源 patch 原样拷贝）→ 打包 zip |
| `verify_zh.py` | 校验：zip 清单与原版一致、**菜单模块数（动态统计）全部汉化**、无英文菜单字符串残留 |
| `extracted/` | 从原版 patch 解出的原始 Lua/bin 资源 |
| `extracted_zh/` | 翻译后的 Lua（bin 原样） |
| `baseline/` | 当前规则所对应的原始源码快照（下次版本更新时用来 diff） |
| `rebuilt/` | 重建后的 patch（按选项文件夹分布） |
| `wiki_terms.json` / `vehicle_hits.txt` | wiki 术语数据与载具名检索结果（参考） |

## 版本更新后的重汉化流程（一条命令）

作者发新版（例如 3.4.0）后，把新 zip 放进 `HD2\`，然后：

```powershell
python ArmoredOverhaul-zh-Hans/update_zh.py "HD2\Armored-Overhaul-3.4.0.zip"
```

它会自动完成：解包新版本 → 从全部 patch 提取 Lua → **与 `baseline/`（上次翻译时的源码
快照）逐文件 diff**，列出改了哪些 Lua 及差异行 → 套用翻译规则（哪条规则因原文改动而
失配会**点名报错**）→ 扫描"仍无中文的菜单文本"（捕捉新增/改名选项）→ 回环验证 + 重建 +
打包 `Armored-Overhaul-3.4.0-zh-Hans.zip` → 与原版逐项校验 → 成功后刷新 `baseline/`。

三种典型情况：

| 情况 | 你要做的 |
|---|---|
| 菜单文本没动（改数值/修 bug） | 全自动完成，直接安装输出的 zip |
| 改了某句英文 / 新增选项 | `update_zh.py` 会点名失配规则与未翻译文本；在 `translate.py` 规则表里把老英文改成新英文并给出中文（或新增一条），重跑同一条命令 |
| manifest Guid 变了 | 打印 WARNING（管理器里会与旧版并存为两个条目），流程照常 |

扫描器说明：它按 `title =` / `label =` / `description =` / `choices =` 找"尚未变成中文的
菜单文本"，**这类缺口会直接中止流程**（不产出半汉化包）；另有一批内部识别表（按内存特征
码标记载具的 `{name = 'Bastion', hull = '...'}`、材质槽的 `{name = 'the skull', mat = ...}`、
炮塔资源的 `{name = 'Bastion', res = ...'}`）只进日志不显示，会被自动识别为"提示项"
（3.4.0 实测 20 条），不影响出包。

## 手动微调（改个别译名后）

```powershell
python ArmoredOverhaul-zh-Hans/translate.py                                     # 重套规则（直接改 extracted_zh 可跳过）
python ArmoredOverhaul-zh-Hans/build_zh.py  "解包目录" "输出zip"                 # 目录如 Armored-Overhaul-3.4.0-extract
python ArmoredOverhaul-zh-Hans/verify_zh.py "原版zip"  "输出zip"
```

安全边界：
- 每个**含 Lua 的 patch** 在重建前先做"原样提取→原样重建→逐字节对比"回环测试，全部通过才动手
  （3.4.0 实测 44 个含 Lua 的 patch 全部无损）；
- 不含 Lua 的游戏资源 patch（悬挂、FRV 稳定、炮塔模型/骷髅贴图等）原字节拷贝，绝不重建；
- 中文文本不含单引号/反斜杠（全角标点），不会破坏 Lua 字符串语法。

## 安装

把 zip 导入 HD2 Arsenal / HD2MM，替换原 "Armored Overhaul" 条目 → Purge/Deploy。
前置：Bingus Shared Loader v19+（模组菜单/绑定菜单来自 Vanilla Plus Megapack）。

## 备注

- `manifest.json` 未改动（管理器内选项名/描述仍为英文；游戏内全中文）。如需管理器侧也中文，
  改 manifest 的 Options Name/Description 即可，但要保持 `Guid`/`Name` 不变以免产生重复条目。
- 模组更新版本后，按上面的"版本更新后的重汉化流程"用 `update_zh.py` 一键重做；
  只有作者改动了菜单文案或新增选项时才需要动 `translate.py` 的规则表。

## 原模组
[Th3chef/Armored-Overhaul](https://github.com/Th3chef/Armored-Overhaul)
