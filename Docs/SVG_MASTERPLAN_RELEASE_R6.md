# 江城大学总平面 SVG — R6 正式发布基线

发布版本：`MASTERPLAN-R6-FINAL`  
最高优先级数据补丁：`PATCH-2026-09-13-R6`

## 效果图基准修正：四周城市道路必须为直线

本发布基线已按用户确认的校园效果图纠正外围道路解释。校园围墙与校界可以在道路内侧独立变化，但四条外围城市道路不得跟随围墙折弯：

- 大学路：东西向直线，中心线 `Z=-1145m`
- 致远路：东西向直线，中心线 `Z=1180m`
- 学府路：南北向直线，中心线 `X=-1610m`
- 长虹路：南北向直线，中心线 `X=1615m`

四角可在道路边缘/路缘层面设置转角半径，但不得改变上述四条中心线的直线关系。该规则已进入 `CampusData/transport/external_roads.json` 与自动校验，后续若道路重新追随围墙弯曲，CI必须失败。

## 正式文件

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Engineering.svg`
  - 3600 × 2800 SVG user units
  - 工程/审计版
  - 保留 19 个正式交付层 + 4 个技术审计层
  - SHA256: `be742bfb7c28476a8ab681b6f3bb3415bbd81db44c1fa2348cf4ce7dbbb67e59`
  - Size: 150005 bytes

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Presentation.svg`
  - 4200 × 3200 SVG user units
  - Figma / 展示版
  - 19 个正式顶层图层
  - 技术对象ID标签已物理移除
  - SHA256: `e4531c7da8377725335c982afbccbbeb486b5d5af03d07fdef03e367627bc7c2`
  - Size: 161973 bytes

## 发布证据

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Release-R6.json`
  - SHA256: `995adfd6ee87fc3c59d99b2c7db399e440391c6f53479cf6b9b70f163a5630b1`
  - 记录正式SVG、Step 7母版及确定性输入文件的SHA256。
  - 不写入时间戳和机器路径，避免无意义的非确定性差异。

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Release-R6-SHA256.txt`
  - 用于快速校验正式Engineering、Presentation及发布证据JSON。

## 数据与内容基线

最终发布继续继承已经通过Step 4～8自动验证的当前有效数据：

- 校园面积：约 `6.5128 km²`
- 建筑/主要设施源记录：`204`
- 学生住宿：`56`（42本科 + 10研究生 + 4国际）
- 校园内部道路/慢行记录：`28`
- 校车站：`22`
- 主要交叉口：`20`
- 主要水体：`11`
- 户外体育记录：`36`
- Presentation顶层图层：`19`
- Engineering顶层图层：`23`

本科宿舍的 `78–82m` 长度范围继续保留；没有隐式改成80m。HSP-02继续作为HSP-01上部住院塔楼覆盖层，不恢复为旧独立地块。

## 可复现性

官方发布生成命令：

```bash
python Tools/run_svg_step7.py
python Tools/normalize_svg_step7_layers.py
python Tools/validate_svg_step7.py
python Tools/release_svg_step8.py
python Tools/validate_svg_step8.py
python Tools/sync_svg_release_metadata.py
```

GitHub Actions会连续执行两次 `Tools/release_svg_step8.py` 并比较发布文件SHA256。最终要求：`STEP8_DETERMINISTIC_REGENERATION=PASS` 且 `RESULT=PASS`。

## 冻结规则

`Step 7` 是 `Step 8` 的唯一内容母版。Step 8只允许修改SVG根级发布标题和metadata，不允许改变任何带ID对象的几何、标签文本、图层成员关系或图层顺序。

正式发布文件禁止：位图 `<image>`、外链图片、外部字体文件、`@font-face`、`script`、`foreignObject`。

效果图确定的四条外围直路关系属于本R6实现纠错后的冻结基准，不得再次解释为沿围墙变化的曲折/弯曲道路。
