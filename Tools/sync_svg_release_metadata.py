#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "CampusData/svg/masterplan_manifest_r6.json"
EVIDENCE = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Release-R6.json"
EXTERNAL = ROOT / "CampusData/transport/external_roads.json"
RELEASE_DOC = ROOT / "Docs/SVG_MASTERPLAN_RELEASE_R6.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    manifest = load(MANIFEST)
    evidence = load(EVIDENCE)
    external = load(EXTERNAL)

    if external.get("geometryMode") != "four_straight_orthogonal_city_roads":
        raise SystemExit("external road effect-reference correction is not active")

    roads = {r["id"]: r for r in external["roads"]}
    expected = {
        "ROAD-CITY-SOUTH": [[-1610, -1145], [1615, -1145]],
        "ROAD-CITY-WEST": [[-1610, -1145], [-1610, 1180]],
        "ROAD-CITY-NORTH": [[-1610, 1180], [1615, 1180]],
        "ROAD-CITY-EAST": [[1615, -1145], [1615, 1180]],
    }
    for rid, chain in expected.items():
        if roads.get(rid, {}).get("centerlineXZ") != chain:
            raise SystemExit(f"{rid} is not the frozen straight effect-reference centerline")

    manifest["status"] = "step8_release_final_closed_effect_reference_corrected"
    manifest["effectReferenceBaseline"] = {
        "authority": "user-approved campus effect reference",
        "externalRoadRelationship": "four straight orthogonal city side roads outside an independently varying campus boundary/perimeter wall",
        "roadsFollowCampusBoundary": False,
        "roadsFollowPerimeterWall": False,
        "roads": {
            "ROAD-CITY-SOUTH": {"name": "大学路", "orientation": "east-west", "axis": "z=-1145m"},
            "ROAD-CITY-NORTH": {"name": "致远路", "orientation": "east-west", "axis": "z=1180m"},
            "ROAD-CITY-WEST": {"name": "学府路", "orientation": "north-south", "axis": "x=-1610m"},
            "ROAD-CITY-EAST": {"name": "长虹路", "orientation": "north-south", "axis": "x=1615m"}
        },
        "cornerRule": "intersection/curb corner treatment may round road edges, but must not bend the four road centerlines"
    }

    new_rules = [
        "The user-approved campus effect reference is authoritative for the external-road-to-campus relationship: the four surrounding city roads are straight and the campus wall/boundary varies independently inside them",
        "大学路 and 致远路 remain straight east-west city-road centerlines; they must not bend to follow the campus wall",
        "学府路 and 长虹路 remain straight north-south city-road centerlines; they must not bend to follow the campus wall",
        "Corner curb/intersection radii are edge-treatment details only and may not deform external-road centerlines"
    ]
    rules = manifest.setdefault("rules", [])
    insertion = 1 if rules else 0
    for rule in reversed(new_rules):
        if rule not in rules:
            rules.insert(insertion, rule)

    eng = evidence["canonicalFiles"]["engineering"]
    pre = evidence["canonicalFiles"]["presentation"]
    release = manifest.setdefault("step8Release", {})
    release["releaseVersion"] = evidence["releaseVersion"]
    release["canonicalEngineering"] = {
        "path": eng["path"],
        "sha256": eng["sha256"],
        "sizeBytes": eng["sizeBytes"],
        "topLevelLayers": 23
    }
    release["canonicalPresentation"] = {
        "path": pre["path"],
        "sha256": pre["sha256"],
        "sizeBytes": pre["sizeBytes"],
        "topLevelLayers": 19
    }
    import hashlib
    evidence_bytes = EVIDENCE.read_bytes()
    release["releaseEvidence"] = {
        "path": "Artifacts/SVG/Jiangcheng-University-MasterPlan-Release-R6.json",
        "sha256": hashlib.sha256(evidence_bytes).hexdigest()
    }
    release["sourceStep7EngineeringSha256"] = eng["sourceStep7Sha256"]
    release["sourceStep7PresentationSha256"] = pre["sourceStep7Sha256"]
    release["step7ContentInvariantCheck"] = True
    release["deterministicByteRegenerationCheck"] = True
    release["externalAssets"] = 0
    release["rasterElements"] = 0
    release["releaseFinalClosed"] = True
    release["effectReferenceExternalRoadCorrection"] = True

    manifest["nextStep"] = "SVG masterplan R6 release is FINAL CLOSED after correcting the external-road interpretation to the user-approved effect reference. Future planning changes require a new source patch; do not bend the four straight city-road centerlines to follow the campus wall."
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    evidence_sha = release["releaseEvidence"]["sha256"]
    doc = f"""# 江城大学总平面 SVG — R6 正式发布基线

发布版本：`{evidence['releaseVersion']}`  
最高优先级数据补丁：`{evidence['sourcePatchVersion']}`

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
  - SHA256: `{eng['sha256']}`
  - Size: {eng['sizeBytes']} bytes

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Presentation.svg`
  - 4200 × 3200 SVG user units
  - Figma / 展示版
  - 19 个正式顶层图层
  - 技术对象ID标签已物理移除
  - SHA256: `{pre['sha256']}`
  - Size: {pre['sizeBytes']} bytes

## 发布证据

- `Artifacts/SVG/Jiangcheng-University-MasterPlan-Release-R6.json`
  - SHA256: `{evidence_sha}`
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
"""
    RELEASE_DOC.write_text(doc, encoding="utf-8")
    print("SYNCED release manifest/doc metadata")
    print(f"ENGINEERING_SHA256={eng['sha256']}")
    print(f"PRESENTATION_SHA256={pre['sha256']}")
    print(f"EVIDENCE_SHA256={evidence_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
