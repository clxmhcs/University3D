# 江城大学总平面 SVG — R6 正式发布基线

发布版本：`MASTERPLAN-R6-FINAL`  
最高优先级数据补丁：`PATCH-2026-09-13-R6`

## 正式文件

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Engineering.svg`
  - 3600 × 2800 SVG user units
  - 工程/审计版
  - 保留 19 个正式交付层 + 4 个技术审计层
  - SHA256: `45de74f748051aee14b76ab02f774e78450e47f66ee260b484598619f452783f`
  - Size: 150205 bytes

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Presentation.svg`
  - 4200 × 3200 SVG user units
  - Figma / 展示版
  - 19 个正式顶层图层
  - 技术对象ID标签已物理移除
  - SHA256: `913c454c620cccfb0a34d5a644e56670bd839cc94730453f7d4e6a3624a46d26`
  - Size: 162181 bytes

## 发布证据

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Release-R6.json`
  - SHA256: `3a75092e0cfcd7c2bad8f425ed05f1289d06cbf4e208b9fdaa5f5db74e0a1116`
  - 记录正式SVG、Step 7母版及所有确定性输入文件的SHA256。
  - 不写入时间戳和机器路径，避免无意义的非确定性差异。

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Release-R6-SHA256.txt`
  - 用于快速校验正式Engineering、Presentation及发布证据JSON。

## 数据与内容基线

最终发布继续继承已经通过Step 4～7自动验证的当前有效数据：

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
```

GitHub Actions还会连续执行两次 `Tools/release_svg_step8.py`，分别对以下4个文件计算SHA256并执行 `diff`：

1. `Jiangcheng-University-MasterPlan-Engineering.svg`
2. `Jiangcheng-University-MasterPlan-Presentation.svg`
3. `Jiangcheng-University-MasterPlan-Release-R6.json`
4. `Jiangcheng-University-MasterPlan-Release-R6-SHA256.txt`

R6最终流水线结果：`STEP8_DETERMINISTIC_REGENERATION=PASS`，`RESULT=PASS`。

## 冻结规则

`Step 7` 是 `Step 8` 的唯一内容母版。Step 8只允许修改SVG根级发布标题和metadata，不允许改变任何带ID对象的几何、标签文本、图层成员关系或图层顺序。

正式发布文件禁止：位图 `<image>`、外链图片、外部字体文件、`@font-face`、`script`、`foreignObject`。

如未来总平面数据发生调整，应首先建立R7或更高优先级补丁，再由CampusData重新生成；不得直接在正式SVG或Unity中形成第二套坐标。
