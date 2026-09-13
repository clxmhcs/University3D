#!/usr/bin/env python3
"""Shared Jiangcheng University world<->SVG coordinate transform.

All masterplan generators must use this module/config instead of duplicating constants.
World: X east, Z north, meters. SVG: X right, Y down.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "CampusData/svg/svg_coordinate_system_r6.json"


@dataclass(frozen=True)
class SvgCoordinateSystem:
    x_min: float
    x_max: float
    z_min: float
    z_max: float
    engineering_offset_x: float
    engineering_offset_y: float
    presentation_offset_x: float
    presentation_offset_y: float
    units_per_meter: float
    round_trip_tolerance_m: float

    @classmethod
    def from_file(cls, path: Path = DEFAULT_CONFIG) -> "SvgCoordinateSystem":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        bounds = data["mapFrame"]["worldBounds"]
        eng = data["profiles"]["engineering"]["mapOffset"]
        pre = data["profiles"]["presentation"]["mapOffset"]
        return cls(
            x_min=float(bounds["xMin"]),
            x_max=float(bounds["xMax"]),
            z_min=float(bounds["zMin"]),
            z_max=float(bounds["zMax"]),
            engineering_offset_x=float(eng[0]),
            engineering_offset_y=float(eng[1]),
            presentation_offset_x=float(pre[0]),
            presentation_offset_y=float(pre[1]),
            units_per_meter=float(data["mapFrame"]["svgUnitsPerMeter"]),
            round_trip_tolerance_m=float(data["precision"]["roundTripToleranceMeters"]),
        )

    @property
    def map_width(self) -> float:
        return (self.x_max - self.x_min) * self.units_per_meter

    @property
    def map_height(self) -> float:
        return (self.z_max - self.z_min) * self.units_per_meter

    def _offset(self, profile: str) -> Tuple[float, float]:
        if profile == "engineering":
            return self.engineering_offset_x, self.engineering_offset_y
        if profile == "presentation":
            return self.presentation_offset_x, self.presentation_offset_y
        raise ValueError(f"unknown SVG profile: {profile}")

    def world_to_svg(self, x: float, z: float, profile: str = "engineering") -> Tuple[float, float]:
        ox, oy = self._offset(profile)
        sx = (float(x) - self.x_min) * self.units_per_meter + ox
        sy = (self.z_max - float(z)) * self.units_per_meter + oy
        return sx, sy

    def svg_to_world(self, sx: float, sy: float, profile: str = "engineering") -> Tuple[float, float]:
        ox, oy = self._offset(profile)
        x = (float(sx) - ox) / self.units_per_meter + self.x_min
        z = self.z_max - (float(sy) - oy) / self.units_per_meter
        return x, z

    def world_points_to_svg(
        self,
        points_xz: Iterable[Sequence[float]],
        profile: str = "engineering",
    ) -> list[Tuple[float, float]]:
        return [self.world_to_svg(p[0], p[1], profile=profile) for p in points_xz]

    @staticmethod
    def world_rotation_y_to_svg_degrees(rotation_y: float) -> float:
        # Local +Z is rendered north/up when rotationY=0. In SVG's y-down
        # coordinate system, positive rotation is visually clockwise, matching
        # the frozen 0=N, 90=E, 180=S, 270=W campus convention.
        return float(rotation_y) % 360.0

    def contains_world_point(self, x: float, z: float, margin_m: float = 0.0) -> bool:
        m = float(margin_m)
        return (
            self.x_min + m <= float(x) <= self.x_max - m
            and self.z_min + m <= float(z) <= self.z_max - m
        )


def format_svg_number(value: float) -> str:
    """Stable numeric formatting: integer when exact, else max two decimals."""
    v = round(float(value), 2)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def svg_points_attribute(points: Iterable[Sequence[float]]) -> str:
    return " ".join(f"{format_svg_number(p[0])},{format_svg_number(p[1])}" for p in points)


if __name__ == "__main__":
    cs = SvgCoordinateSystem.from_file()
    print("map", cs.map_width, cs.map_height)
    for profile in ("engineering", "presentation"):
        print(profile, "origin", cs.world_to_svg(0, 0, profile))
