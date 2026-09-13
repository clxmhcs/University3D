# 江城大学总平面 SVG 坐标规范（R6 / Step 2）

本规范是 `CampusData/svg/svg_coordinate_system_r6.json` 的人类可读说明。后续工程版、展示版 SVG 生成器必须读取该 JSON，不允许在其他脚本里重新定义一套坐标常量。

## 1. 数据基线

- 最高优先级补丁：`PATCH-2026-09-13-R6`
- 世界坐标：X 向东、Z 向北、Y 为高程。
- 单位：1m。
- 总平面只投影 X/Z，不使用 Y 改变平面位置。
- 建筑 Local +Z 为主入口方向；`rotationY=0/90/180/270` 分别为北/东/南/西。

## 2. 固定工程地图框

为了保证后续 R6/R7 小范围修订不会导致整张图重新 auto-fit、进而让 Figma 中所有对象整体漂移，SVG 地图框不按当前几何动态计算，而是冻结为：

- 世界 X：`-1800 .. +1800m`
- 世界 Z：`-1400 .. +1400m`
- SVG 工程 ViewBox：`0 0 3600 2800`
- `1 SVG user unit = 1m`
- 世界原点 `(0,0)` → SVG `(1800,1400)`

当前 R6 外围城市道路中心线最外范围为：

- X：`-1610 .. +1615m`
- Z：`-1145 .. +1180m`

计入 36m 道路宽度的一半（18m）后，仍完整位于冻结地图框内。

## 3. 世界坐标到 SVG

工程地图：

```text
svgX = worldX + 1800
svgY = 1400 - worldZ
```

反向：

```text
worldX = svgX - 1800
worldZ = 1400 - svgY
```

只翻转 Z→SVG Y，不翻转 X，不做额外缩放。

已冻结校验点：

| 对象 | World X/Z | Engineering SVG X/Y |
|---|---:|---:|
| 世界原点 | 0, 0 | 1800, 1400 |
| 南门 | 0, -1098 | 1800, 2498 |
| 北门 | 0, 1142 | 1800, 258 |
| 西门 | -1548, -80 | 252, 1480 |
| 东门 | 1555, 120 | 3355, 1280 |

## 4. 建筑旋转

未旋转建筑的 Local +Z 在图纸中指向北，也就是 SVG 上方。

因此直接采用：

```text
svgRotationDeg = worldRotationY
```

即：

- 0° → 北
- 90° → 东
- 180° → 南
- 270° → 西

禁止因为 SVG 的 Y 轴向下而再次把 rotationY 取负；这样会把东西方向颠倒。

## 5. 两种输出 Profile

### Engineering

用于坐标审计和工程母图：

```text
ViewBox = 0 0 3600 2800
Map Offset = 0,0
World Origin = 1800,1400
```

不预留标题栏，不对地图做任何平移或缩放。

### Presentation / Figma

用于 Figma 展示总平面：

```text
Document ViewBox = 0 0 4200 3200
Map Frame = 3600 x 2800
Map Offset = 300,200
World Origin = 2100,1600
```

地图本身仍保持 1m=1 SVG unit，只允许整体平移 `(300,200)`，不允许缩放。四周留白用于标题、图例、比例尺和说明。

## 6. Figma 导入规则

SVG 采用普通矢量导入，不依赖 Figma AI。

根分组固定为：

1. `01_CityRoads`
2. `02_CampusBoundary`
3. `03_PerimeterWall`
4. `04_Gates`
5. `05_InternalRoads`
6. `06_Water`
7. `07_Landscape`
8. `08_Buildings`
9. `09_Residential`
10. `10_Sports`
11. `11_POI`
12. `12_Labels`
13. `13_RoadNames`
14. `14_Legend`

图层顺序以后由生成器保证，不靠导入 Figma 后人工重排。

## 7. 网格与比例尺

- Chunk 主网格：250m。
- 辅助参考网格：50m。
- 推荐比例尺：100m / 250m / 500m / 1000m。
- 因为 1 SVG unit=1m，所以 500m 比例尺必须精确为 500 SVG units。

Chunk 网格以世界原点 `(0,0)` 为逻辑原点，不要求地图框边缘恰好落在 Chunk 边线上。

## 8. 精度与禁止项

允许生成结果保留到 0.01 SVG unit（0.01m），但源数据有整数或更低精度时不得伪造更高空间精度。

禁止：

- 根据现有几何自动 fit ViewBox；
- 把世界坐标归一化到 0..1；
- 在地图组内按像素比例缩放；
- 人工拖动建筑以“看起来更整齐”；
- 单独为 Figma 再维护第二套坐标；
- 把 SVG 栅格化后作为主母图；
- 在不同生成脚本里复制 `1800/1400` 等常量。

所有转换必须调用 `Tools/svg_coordinates.py`。

## 9. Step 2 验收

执行：

```bash
python3 Tools/validate_svg_coordinate_system.py
```

必须检查：

- R6 数据版本一致；
- 3600×2800 工程 ViewBox；
- 世界原点映射正确；
- 四个主校门已知点正确；
- World→SVG→World 往返误差≤0.01m；
- 北为 SVG 上、东为 SVG 右；
- rotationY 映射未反转；
- 36m 外围道路完整落在冻结地图框内；
- 6.513km²校园边界没有被 ViewBox 裁切；
- 500m 比例尺仍为500 SVG units。

Step 3 开始绘制外围城市道路、校园边界、围墙和校门时，直接复用本规范，不再讨论坐标映射。
