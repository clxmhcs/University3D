#!/usr/bin/env python3
"""Official Step-7 execution entrypoint with corrected SVG group matching.

The core implementation lives in generate_svg_step7.py. This runner replaces only
the two group-string helpers whose original regex incorrectly used a word boundary
after a closing quote. No data or geometry behavior is changed.
"""
from __future__ import annotations

import re
import generate_svg_step7 as step7


def remove_group(svg: str, group_id: str):
    paired = re.compile(rf'\n?\s*<g id="{re.escape(group_id)}"[^>]*>.*?</g>\s*', re.S)
    svg2, count = paired.subn("\n", svg, count=1)
    if count:
        return svg2
    self_closing = re.compile(rf'\n?\s*<g id="{re.escape(group_id)}"[^>]*/>\s*')
    svg2, count = self_closing.subn("\n", svg, count=1)
    if not count:
        raise ValueError(f"Step 7 prune group not found: {group_id}")
    return svg2


def replace_group(svg: str, group_id: str, replacement: str):
    paired = re.compile(rf'\s*<g id="{re.escape(group_id)}"[^>]*>.*?</g>', re.S)
    svg2, count = paired.subn("\n" + replacement, svg, count=1)
    if count:
        return svg2
    self_closing = re.compile(rf'\s*<g id="{re.escape(group_id)}"[^>]*/>')
    svg2, count = self_closing.subn("\n" + replacement, svg, count=1)
    if not count:
        raise ValueError(f"Step 7 replace group not found: {group_id}")
    return svg2


step7.remove_group = remove_group
step7.replace_group = replace_group

if __name__ == "__main__":
    step7.main()
