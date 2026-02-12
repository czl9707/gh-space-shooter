"""Regression tests for SVG provider internals and structural output behavior."""

import xml.etree.ElementTree as ET
from unittest.mock import patch

from gh_space_shooter.game.svg_timeline import (
    BulletFrameState,
    EnemyFrameState,
    SvgTimelineFrame,
)
from gh_space_shooter.output import SvgOutputProvider
from gh_space_shooter.output._svg_entity_minifier import _tl_entity_minify
from gh_space_shooter.output._svg_timeline_encoder import (
    _tl_encode_svg_timeline_sequence_with_enemy_groupings,
    encode_svg_timeline_sequence,
)


def _assert_valid_svg_xml(markup: str | bytes) -> ET.Element:
    text = markup.decode("utf-8") if isinstance(markup, bytes) else markup
    root = ET.fromstring(text)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    return root


def _xml_semantic_signature(markup: str) -> tuple[str, tuple[tuple[str, str], ...], tuple[object, ...]]:
    root = ET.fromstring(markup)

    def walk(node: ET.Element) -> tuple[str, tuple[tuple[str, str], ...], tuple[object, ...]]:
        children = tuple(walk(child) for child in list(node))
        return (node.tag, tuple(sorted(node.attrib.items())), children)

    return walk(root)


def test_entity_minifier_only_applies_when_savings_positive() -> None:
    svg_with_short_values = (
        '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">'
        '<g x="0"/><g x="0"/></svg>'
    )
    unchanged = _tl_entity_minify(svg_with_short_values)

    assert unchanged == svg_with_short_values
    _assert_valid_svg_xml(unchanged)
    assert _xml_semantic_signature(unchanged) == _xml_semantic_signature(svg_with_short_values)

    long_values = ";".join(str(index) for index in range(1, 61))
    svg_with_repeated_long_values = (
        '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">'
        f'<g values="{long_values}"/><g values="{long_values}"/><g values="{long_values}"/></svg>'
    )
    minimized = _tl_entity_minify(svg_with_repeated_long_values)

    assert "<!DOCTYPE svg [" in minimized
    assert "&" in minimized and ";" in minimized
    assert len(minimized) < len(svg_with_repeated_long_values)
    assert minimized != svg_with_repeated_long_values
    _assert_valid_svg_xml(minimized)
    assert _xml_semantic_signature(minimized) == _xml_semantic_signature(
        svg_with_repeated_long_values
    )


def test_entity_minifier_prefix_rewrites_preserve_xml_values() -> None:
    prefix = ";".join(str(index) for index in range(1, 25))
    value_one = f"{prefix};101"
    value_two = f"{prefix};202"
    key_times_one = f"{prefix};303"
    key_times_two = f"{prefix};404"
    original = (
        '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">'
        f'<g values="{value_one}"/><g values="{value_two}"/>'
        f'<g keyTimes="{key_times_one}"/><g keyTimes="{key_times_two}"/>'
        "</svg>"
    )

    minimized = _tl_entity_minify(original)

    assert len(minimized) < len(original)
    _assert_valid_svg_xml(minimized)
    assert _xml_semantic_signature(minimized) == _xml_semantic_signature(original)


def test_timeline_svg_linear_bullet_track_compresses_size() -> None:
    provider = SvgOutputProvider()
    frames: list[SvgTimelineFrame] = []

    for index in range(1000):
        time_ms = index * 25
        bullets: tuple[BulletFrameState, ...] = ()
        phase = index % 80
        if phase < 60:
            sequence = index // 80
            bullets = (
                BulletFrameState(
                    id=sequence,
                    x=10 + (sequence % 5),
                    y=9.0 - phase * 0.2,
                ),
            )

        frames.append(
            SvgTimelineFrame(
                width=100,
                height=100,
                time_ms=time_ms,
                watermark=False,
                ship_x=0.0,
                stars=(),
                enemies=(),
                bullets=bullets,
                explosions=(),
            )
        )

    optimized = provider.encode(iter(frames), frame_duration=25)

    def _identity_points(
        points: list[tuple[float, float]],
        times: list[int],
        forced_indices: set[int],
    ) -> tuple[list[tuple[float, float]], list[int]]:
        _ = forced_indices
        return points, times

    with patch(
        "gh_space_shooter.output._svg_timeline_encoder._tl_compress_points_with_forced",
        side_effect=_identity_points,
    ):
        uncompressed_points = provider.encode(iter(frames), frame_duration=25)

    assert len(optimized) < len(uncompressed_points)


def test_timeline_svg_picks_smaller_enemy_grouping_variant() -> None:
    enemies = tuple(
        EnemyFrameState(id=f"{x}:2", x=x, y=2, health=2)
        for x in range(52)
    )
    frames = [
        SvgTimelineFrame(
            width=900,
            height=220,
            time_ms=0,
            watermark=False,
            ship_x=25.0,
            stars=(),
            enemies=enemies,
            bullets=(),
            explosions=(),
        )
    ]

    column_only = _tl_encode_svg_timeline_sequence_with_enemy_groupings(
        frames, frame_duration=25, enemy_groupings=("column",)
    )
    row_only = _tl_encode_svg_timeline_sequence_with_enemy_groupings(
        frames, frame_duration=25, enemy_groupings=("row",)
    )
    adaptive = encode_svg_timeline_sequence(frames, frame_duration=25)

    assert len(adaptive) <= len(column_only)
    assert len(adaptive) <= len(row_only)
