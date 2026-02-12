"""Timeline/object-based SVG encoder."""

from dataclasses import dataclass
import math
from typing import TypeVar

from PIL import Image, ImageDraw, ImageFont

from ..constants import BULLET_TRAIL_SPACING, BULLET_TRAILING_LENGTH, SHIP_POSITION_Y
from ..game.render_context import RenderContext
from ..game.renderer import WATERMARK_TEXT
from ..game.svg_timeline import ExplosionFrameState, SvgTimelineFrame
from ._svg_entity_minifier import _tl_entity_minify
from ._svg_shared import _tl_hex, _tl_num, _to_compact_name
from ._svg_tracks import (
    _tl_build_object_slot_tracks,
    _tl_compress_discrete_points,
    _tl_compress_discrete_track,
    _tl_compress_linear_scalar_track,
    _tl_compress_points_with_forced,
    _tl_compress_scalar_track,
    _tl_has_distinct_values,
    _tl_key_times_attr,
    _tl_pad_local_track,
)


_NameKey = TypeVar("_NameKey")
_Point = tuple[float, float]
_StarTrackSample = tuple[int, float, float, int, float]


@dataclass
class _ExplosionTrackSamples:
    path_values: list[str]
    center_values: list[_Point]
    progress_values: list[float]
    stroke_width_values: list[float]
    stroke_color_values: list[str]
    opacity_values: list[float]


def encode_svg_timeline_sequence(frames: list[SvgTimelineFrame], frame_duration: int) -> bytes:
    """Encode timeline snapshots into a compact animated SVG.

    Pipeline:
    1. Build reusable symbol/paint palettes.
    2. Build per-entity animation tracks (stars/enemies/explosions/bullets/ship).
    3. Minify repeated XML attribute values.
    """
    context = RenderContext.darkmode()
    total_duration_ms = max(1, len(frames) * frame_duration)
    width, height = _tl_resolve_timeline_dimensions(frames)
    enemy_size = context.cell_size + 1

    star_defs, star_symbol_ids = _tl_star_template_defs(frames)
    enemy_fill_color_counts = _tl_collect_enemy_fill_color_usage(frames, context)
    explosion_stroke_color_counts = _tl_collect_explosion_stroke_color_usage(
        frames, context, total_duration_ms
    )
    enemy_fill_palette, explosion_stroke_palette = _tl_build_palette_class_maps(
        enemy_fill_color_counts, explosion_stroke_color_counts
    )
    enemy_elements = _tl_enemy_elements(
        frames, context, total_duration_ms, enemy_fill_palette
    )
    explosion_elements = _tl_explosion_elements(
        frames, context, total_duration_ms, explosion_stroke_palette
    )
    palette_css = _tl_palette_style(enemy_fill_palette, explosion_stroke_palette)

    ship_fill = _tl_hex(context.ship_color)
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        *([f"<style>{palette_css}</style>"] if palette_css else []),
        f'<g id="b">{"".join(_tl_bullet_shape_elements(context))}</g>',
        f'<g id="s" shape-rendering="crispEdges" fill="{ship_fill}">'
        f'{"".join(_tl_ship_symbol_elements(context))}</g>',
        f'<rect id="e" width="{enemy_size}" height="{enemy_size}" rx="2" ry="2"/>',
        *star_defs,
        "</defs>",
    ]

    parts.append('<g shape-rendering="crispEdges">')

    parts.append(
        f'<rect width="{width}" height="{height}" fill="{_tl_hex(context.background_color)}"/>'
    )
    parts.extend(_tl_star_elements(frames, context, total_duration_ms, star_symbol_ids))
    parts.extend(enemy_elements)
    parts.extend(explosion_elements)
    parts.extend(_tl_bullet_elements(frames, context, total_duration_ms))
    parts.extend(_tl_ship_elements(frames, context, total_duration_ms))

    parts.append("</g>")
    if frames[0].watermark:
        parts.append(_tl_watermark_element(width, height))
    parts.append("</svg>")
    svg_markup = "".join(parts)
    return _tl_entity_minify(svg_markup).encode("utf-8")


def _tl_resolve_timeline_dimensions(frames: list[SvgTimelineFrame]) -> tuple[int, int]:
    width = frames[0].width
    height = frames[0].height
    for frame in frames[1:]:
        if frame.width != width or frame.height != height:
            raise ValueError("All SVG timeline frames must have the same dimensions")
    return width, height


def _tl_star_elements(
    frames: list[SvgTimelineFrame],
    context: RenderContext,
    total_duration_ms: int,
    star_symbol_ids: dict[tuple[int, str], str],
) -> list[str]:
    if not frames:
        return []

    star_tracks = _tl_collect_star_tracks(frames, context)
    elements: list[str] = []
    for _star_id, samples in sorted(star_tracks.items()):
        star_element = _tl_render_star_track(
            samples, total_duration_ms, star_symbol_ids
        )
        if star_element:
            elements.append(star_element)

    return elements


def _tl_collect_star_tracks(
    frames: list[SvgTimelineFrame], context: RenderContext
) -> dict[int, list[_StarTrackSample]]:
    star_tracks: dict[int, list[_StarTrackSample]] = {}
    for frame in frames:
        for star in frame.stars:
            x, y = context.get_cell_position(star.x, star.y)
            star_tracks.setdefault(star.id, []).append(
                (frame.time_ms, x, y, star.size, star.brightness)
            )
    return star_tracks


def _tl_render_star_track(
    samples: list[_StarTrackSample],
    total_duration_ms: int,
    star_symbol_ids: dict[tuple[int, str], str],
) -> str:
    if not samples:
        return ""

    symbol_id = _tl_star_symbol_id(samples[0], star_symbol_ids)
    if symbol_id is None:
        return ""

    global_times = [sample[0] for sample in samples]
    global_points = [(sample[1], sample[2]) for sample in samples]

    wrap_indices = _tl_star_wrap_indices(global_points)
    forced_indices = _tl_forced_indices_for_wraps(wrap_indices, len(global_points))
    points, times = _tl_compress_points_with_forced(global_points, global_times, forced_indices)
    times, points = _tl_pad_local_track(times, points, total_duration_ms)

    translate_values = ";".join(
        f"{_tl_num_step(x, 0.01)} {_tl_num_step(y, 0.01)}" for x, y in points
    )
    key_times_attr = _tl_key_times_attr(times, total_duration_ms)

    base_group = (
        f'<g transform="translate({_tl_num_step(points[0][0], 0.01)} '
        f'{_tl_num_step(points[0][1], 0.01)})">'
        f'<use href="#{symbol_id}"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{translate_values}" {key_times_attr} dur="{total_duration_ms}ms" '
        f'repeatCount="indefinite"/>'
    )
    if not wrap_indices:
        return f"{base_group}</g>"

    visibility_times, visibility_values = _tl_star_visibility_track(
        global_times, wrap_indices, total_duration_ms
    )
    visibility_values_attr = ";".join(_tl_num(value) for value in visibility_values)
    return (
        f'<g opacity="{_tl_num(visibility_values[0])}" '
        f'transform="translate({_tl_num_step(points[0][0], 0.01)} '
        f'{_tl_num_step(points[0][1], 0.01)})">'
        f'<use href="#{symbol_id}"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{translate_values}" {key_times_attr} dur="{total_duration_ms}ms" '
        f'repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="{visibility_values_attr}" '
        f'{_tl_key_times_attr(visibility_times, total_duration_ms)} '
        f'dur="{total_duration_ms}ms" repeatCount="indefinite" calcMode="discrete"/></g>'
    )


def _tl_star_symbol_id(
    first_sample: _StarTrackSample,
    star_symbol_ids: dict[tuple[int, str], str],
) -> str | None:
    size = first_sample[3]
    brightness = first_sample[4]
    star_value = max(0, min(255, int(255 * brightness)))
    fill = _tl_hex((star_value, star_value, star_value))
    return star_symbol_ids.get((size, fill))


def _tl_star_wrap_indices(points: list[_Point]) -> list[int]:
    # Track vertical wrap points so stars can be hidden briefly while
    # jumping from bottom back to top.
    wrap_indices: list[int] = []
    for index in range(1, len(points)):
        prev_y = points[index - 1][1]
        curr_y = points[index][1]
        if curr_y < prev_y - 0.5:
            wrap_indices.append(index)
    return wrap_indices


def _tl_forced_indices_for_wraps(wrap_indices: list[int], point_count: int) -> set[int]:
    forced_indices = {0, point_count - 1}
    for index in wrap_indices:
        forced_indices.add(index - 1)
        forced_indices.add(index)
    return forced_indices


def _tl_star_visibility_track(
    global_times: list[int], wrap_indices: list[int], total_duration_ms: int
) -> tuple[list[int], list[float]]:
    visibility_events: list[tuple[int, float]] = [(0, 1.0), (total_duration_ms, 1.0)]
    for index in wrap_indices:
        t_prev = global_times[index - 1]
        t_curr = global_times[index]
        off_start = min(total_duration_ms, max(0, t_prev + 1))
        off_end = min(total_duration_ms, max(off_start, t_curr))
        on_time = min(total_duration_ms, off_end + 1)
        visibility_events.extend(
            [
                (max(0, t_prev), 1.0),
                (off_start, 0.0),
                (off_end, 0.0),
                (on_time, 1.0),
            ]
        )

    visibility_events.sort(key=lambda item: item[0])
    visibility_times = [event_time for event_time, _ in visibility_events]
    visibility_values = [event_value for _, event_value in visibility_events]
    visibility_times, visibility_values = _tl_compress_scalar_track(
        visibility_times, visibility_values
    )
    return _tl_pad_local_track(visibility_times, visibility_values, total_duration_ms)


def _tl_enemy_elements(
    frames: list[SvgTimelineFrame],
    context: RenderContext,
    total_duration_ms: int,
    fill_palette: dict[str, str],
) -> list[str]:
    enemies_by_id: dict[str, tuple[int, int]] = {}
    for enemy in frames[0].enemies:
        enemies_by_id[enemy.id] = (enemy.x, enemy.y)

    enemy_health_by_frame = [{enemy.id: enemy.health for enemy in frame.enemies} for frame in frames]

    enemies_by_x: dict[int, list[str]] = {}
    for enemy_id, (x_cell, _) in enemies_by_id.items():
        enemies_by_x.setdefault(x_cell, []).append(enemy_id)

    elements: list[str] = []
    for x_cell in sorted(enemies_by_x):
        x, _ = context.get_cell_position(x_cell, 0)
        column_parts: list[str] = []
        for enemy_id in sorted(enemies_by_x[x_cell]):
            _, y_cell = enemies_by_id[enemy_id]
            _, y = context.get_cell_position(0, y_cell)
            health_series: list[int | None] = []
            for frame_map in enemy_health_by_frame:
                health_series.append(frame_map.get(enemy_id))

            initial_health = next((value for value in health_series if value is not None), None)
            if initial_health is None:
                continue

            fill_times: list[int] = [0]
            fill_classes: list[str] = [
                fill_palette[_tl_hex(context.enemy_colors.get(initial_health, context.enemy_colors[1]))]
            ]
            previous: int | None = initial_health

            for index, health in enumerate(health_series):
                current_ms = frames[index].time_ms
                if health is None:
                    previous = None
                    continue
                if previous is None:
                    previous = health
                    continue
                if health != previous:
                    fill_times.append(current_ms)
                    fill_classes.append(
                        fill_palette[_tl_hex(context.enemy_colors.get(health, context.enemy_colors[1]))]
                    )
                    previous = health

            fill_times, fill_classes = _tl_compress_discrete_track(fill_times, fill_classes)
            fill_times, fill_classes = _tl_pad_local_track(fill_times, fill_classes, total_duration_ms)
            initial_fill_class = fill_classes[0]
            rect_parts = [f'<use href="#e" y="{_tl_num(y)}" class="{initial_fill_class}">']
            if _tl_has_distinct_values(fill_classes):
                fill_class_values = ";".join(fill_classes)
                rect_parts.append(
                    f'<animate attributeName="class" values="{fill_class_values}" '
                    f'{_tl_key_times_attr(fill_times, total_duration_ms)} '
                    f'dur="{total_duration_ms}ms" repeatCount="indefinite" calcMode="discrete"/>'
                )

            presence_times = [frame.time_ms for frame in frames]
            presence_values = [1.0 if health is not None else 0.0 for health in health_series]
            presence_times, presence_values = _tl_compress_scalar_track(
                presence_times, presence_values
            )
            presence_times, presence_values = _tl_pad_local_track(
                presence_times, presence_values, total_duration_ms
            )
            if any(value < 0.5 for value in presence_values):
                presence_value_text = ";".join(
                    "1" if value >= 0.5 else "0" for value in presence_values
                )
                rect_parts.append(
                    f'<animate attributeName="opacity" values="{presence_value_text}" '
                    f'{_tl_key_times_attr(presence_times, total_duration_ms)} '
                    f'dur="{total_duration_ms}ms" repeatCount="indefinite" calcMode="discrete"/>'
                )

            rect_parts.append("</use>")
            column_parts.append("".join(rect_parts))

        if column_parts:
            elements.append(
                f'<g transform="translate({_tl_num(x)} 0)">{"".join(column_parts)}</g>'
            )

    return elements


def _tl_bullet_elements(
    frames: list[SvgTimelineFrame],
    context: RenderContext,
    total_duration_ms: int,
) -> list[str]:
    bullet_frames = [{bullet.id: bullet for bullet in frame.bullets} for frame in frames]
    slot_tracks = _tl_build_object_slot_tracks(
        bullet_frames,
        reuse_slots_within_frame=False,
    )
    frame_times = [frame.time_ms for frame in frames]

    elements: list[str] = []
    for slot_track in slot_tracks:
        if all(state is None for state in slot_track):
            continue

        first_active = next((state for state in slot_track if state is not None), None)
        if first_active is None:
            continue
        first_x, first_y = context.get_cell_position(first_active.x, first_active.y)
        last_point = (
            float(int(round(first_x + context.cell_size / 2))),
            float(int(round(first_y + context.cell_size / 2))),
        )

        position_values: list[tuple[float, float]] = []
        opacity_values: list[float] = []

        for bullet in slot_track:
            if bullet is not None:
                x, y = context.get_cell_position(bullet.x, bullet.y)
                last_point = (
                    float(int(round(x + context.cell_size / 2))),
                    float(int(round(y + context.cell_size / 2))),
                )
                opacity_values.append(1.0)
            else:
                opacity_values.append(0.0)
            position_values.append(last_point)

        times = [*frame_times, total_duration_ms]
        position_values.append(position_values[-1])
        opacity_values.append(opacity_values[-1])

        forced_indices = _tl_transition_forced_indices(opacity_values)
        track_points, track_times = _tl_compress_points_with_forced(
            position_values, times, forced_indices
        )
        track_times, track_points = _tl_pad_local_track(track_times, track_points, total_duration_ms)

        opacity_times, opacity_values = _tl_compress_scalar_track(times, opacity_values)
        opacity_times, opacity_values = _tl_pad_local_track(
            opacity_times, opacity_values, total_duration_ms
        )

        elements.append(
            f'<g opacity="{_tl_num(opacity_values[0])}" '
            f'transform="translate({_tl_num(track_points[0][0])} {_tl_num(track_points[0][1])})">'
            f'<use href="#b"/>'
            f'{_tl_point_animate_transform(track_points, track_times, total_duration_ms)}'
            f'<animate attributeName="opacity" '
            f'values="{";".join(_tl_num(value) for value in opacity_values)}" '
            f'{_tl_key_times_attr(opacity_times, total_duration_ms)} '
            f'dur="{total_duration_ms}ms" repeatCount="indefinite" calcMode="discrete"/></g>'
        )

    return elements


def _tl_star_template_defs(
    frames: list[SvgTimelineFrame],
) -> tuple[list[str], dict[tuple[int, str], str]]:
    if not frames:
        return [], {}

    template_counts: dict[tuple[int, str], int] = {}
    for frame in frames:
        for star in frame.stars:
            star_value = max(0, min(255, int(255 * star.brightness)))
            fill = _tl_hex((star_value, star_value, star_value))
            key = (star.size, fill)
            template_counts[key] = template_counts.get(key, 0) + 1

    symbol_ids = _tl_assign_compact_names_by_count(template_counts, reserved={"b", "s", "e"})

    defs: list[str] = []
    for (size, fill), symbol_id in sorted(symbol_ids.items(), key=lambda item: item[1]):
        defs.append(
            f'<rect id="{symbol_id}" width="{size}" height="{size}" fill="{fill}"/>'
        )
    return defs, symbol_ids


def _tl_explosion_path_points(explosion: ExplosionFrameState) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = set()
    for angle in explosion.particle_angles:
        x = int(round(explosion.max_radius * math.cos(angle)))
        y = int(round(explosion.max_radius * math.sin(angle)))
        point = (x, y)
        if point in used:
            continue
        used.add(point)
        points.append(point)
    return points


def _tl_explosion_progress(explosion: ExplosionFrameState) -> float:
    if explosion.duration <= 0:
        return 1.0
    return min(1.0, max(0.0, explosion.elapsed_time / explosion.duration))


def _tl_explosion_fade(progress: float) -> float:
    return int(255 * max(0.0, 1.0 - progress)) / 255.0


def _tl_explosion_particle_size(progress: float) -> int:
    return int((1 - progress * 0.5) * 3) + 1


def _tl_explosion_path_data(points: list[tuple[int, int]]) -> str:
    return "".join(f"M{x} {y}h0" for x, y in points)


def _tl_explosion_center(context: RenderContext, x_cell: float, y_cell: float) -> _Point:
    x, y = context.get_cell_position(x_cell, y_cell)
    return (
        float(int(round(x + context.cell_size / 2))),
        float(int(round(y + context.cell_size / 2))),
    )


def _tl_sample_explosion_track(
    slot_track: list[ExplosionFrameState | None],
    context: RenderContext,
    bullet_rgb: tuple[int, int, int],
    background_rgb: tuple[int, int, int],
) -> _ExplosionTrackSamples | None:
    first_active = next((state for state in slot_track if state is not None), None)
    if first_active is None:
        return None

    first_points = _tl_explosion_path_points(first_active)
    if not first_points:
        return None

    current_path = _tl_explosion_path_data(first_points)
    current_progress = _tl_explosion_progress(first_active)
    current_width = float(_tl_explosion_particle_size(current_progress) * 2 + 1)
    current_color = _tl_blend_hex_over_background(
        bullet_rgb, background_rgb, _tl_explosion_fade(current_progress)
    )
    current_center = _tl_explosion_center(context, first_active.x, first_active.y)

    samples = _ExplosionTrackSamples(
        path_values=[],
        center_values=[],
        progress_values=[],
        stroke_width_values=[],
        stroke_color_values=[],
        opacity_values=[],
    )

    # Carry forward the latest sampled values while the slot is active;
    # when a slot is inactive we keep position/path stable and animate opacity to 0.
    for explosion in slot_track:
        if explosion is not None:
            points = _tl_explosion_path_points(explosion)
            if points:
                current_path = _tl_explosion_path_data(points)
            current_progress = _tl_explosion_progress(explosion)
            current_width = float(_tl_explosion_particle_size(current_progress) * 2 + 1)
            current_color = _tl_blend_hex_over_background(
                bullet_rgb, background_rgb, _tl_explosion_fade(current_progress)
            )
            current_center = _tl_explosion_center(context, explosion.x, explosion.y)
            samples.opacity_values.append(1.0)
        else:
            samples.opacity_values.append(0.0)

        samples.path_values.append(current_path)
        samples.center_values.append(current_center)
        samples.progress_values.append(current_progress)
        samples.stroke_width_values.append(current_width)
        samples.stroke_color_values.append(current_color)

    return samples


def _tl_extend_explosion_track_to_loop_end(
    samples: _ExplosionTrackSamples, frame_times: list[int], total_duration_ms: int
) -> list[int]:
    times = [*frame_times, total_duration_ms]
    samples.path_values.append(samples.path_values[-1])
    samples.center_values.append(samples.center_values[-1])
    samples.progress_values.append(samples.progress_values[-1])
    samples.stroke_width_values.append(samples.stroke_width_values[-1])
    samples.stroke_color_values.append(samples.stroke_color_values[-1])
    samples.opacity_values.append(samples.opacity_values[-1])
    return times


def _tl_explosion_path_markup(
    d_values: list[str],
    d_times: list[int],
    progress_values: list[float],
    progress_times: list[int],
    stroke_width_values: list[float],
    stroke_width_times: list[int],
    stroke_class_values: list[str],
    stroke_color_times: list[int],
    total_duration_ms: int,
) -> str:
    path_parts = [
        f'<path d="{d_values[0]}" fill="none" class="{stroke_class_values[0]}" '
        f'stroke-width="{_tl_num(stroke_width_values[0])}" stroke-linecap="square" '
        f'vector-effect="non-scaling-stroke" transform="scale({_tl_num(progress_values[0])})">'
    ]
    if len(d_values) > 1:
        path_parts.append(
            f'<animate attributeName="d" values="{";".join(d_values)}" '
            f'{_tl_key_times_attr(d_times, total_duration_ms)} '
            f'dur="{total_duration_ms}ms" repeatCount="indefinite" calcMode="discrete"/>'
        )

    path_parts.extend(
        [
            _tl_scalar_animate_transform(
                "scale", progress_values, progress_times, total_duration_ms
            ),
            f'<animate attributeName="stroke-width" '
            f'values="{";".join(_tl_num(value) for value in stroke_width_values)}" '
            f'{_tl_key_times_attr(stroke_width_times, total_duration_ms)} '
            f'dur="{total_duration_ms}ms" repeatCount="indefinite" calcMode="discrete"/>',
            f'<animate attributeName="class" '
            f'values="{";".join(stroke_class_values)}" '
            f'{_tl_key_times_attr(stroke_color_times, total_duration_ms)} '
            f'dur="{total_duration_ms}ms" repeatCount="indefinite" calcMode="discrete"/>',
            "</path>",
        ]
    )
    return "".join(path_parts)


def _tl_explosion_elements(
    frames: list[SvgTimelineFrame],
    context: RenderContext,
    total_duration_ms: int,
    stroke_palette: dict[str, str],
) -> list[str]:
    """Build animated explosion paths by reusing object slots across frames."""
    explosion_frames = [{explosion.id: explosion for explosion in frame.explosions} for frame in frames]
    slot_tracks = _tl_build_object_slot_tracks(explosion_frames)
    frame_times = [frame.time_ms for frame in frames]

    bullet_rgb = context.bullet_color
    background_rgb = context.background_color
    elements: list[str] = []

    for slot_track in slot_tracks:
        samples = _tl_sample_explosion_track(slot_track, context, bullet_rgb, background_rgb)
        if samples is None:
            continue

        times = _tl_extend_explosion_track_to_loop_end(samples, frame_times, total_duration_ms)

        d_times, d_values = _tl_compress_discrete_track(times, samples.path_values)
        d_times, d_values = _tl_pad_local_track(d_times, d_values, total_duration_ms)

        center_times, center_values = _tl_compress_discrete_points(times, samples.center_values)
        center_times, center_values = _tl_pad_local_track(center_times, center_values, total_duration_ms)

        progress_forced_indices = _tl_transition_forced_indices(samples.opacity_values)
        progress_times, progress_values = _tl_compress_linear_scalar_track(
            times,
            samples.progress_values,
            forced_indices=progress_forced_indices,
            eps=1e-12,
        )
        progress_times, progress_values = _tl_pad_local_track(
            progress_times, progress_values, total_duration_ms
        )

        stroke_width_times, stroke_width_values = _tl_compress_scalar_track(
            times, samples.stroke_width_values
        )
        stroke_width_times, stroke_width_values = _tl_pad_local_track(
            stroke_width_times, stroke_width_values, total_duration_ms
        )

        stroke_color_times, stroke_color_values = _tl_compress_discrete_track(
            times, samples.stroke_color_values
        )
        stroke_color_times, stroke_color_values = _tl_pad_local_track(
            stroke_color_times, stroke_color_values, total_duration_ms
        )

        opacity_times, opacity_values = _tl_compress_scalar_track(times, samples.opacity_values)
        opacity_times, opacity_values = _tl_pad_local_track(
            opacity_times, opacity_values, total_duration_ms
        )

        stroke_class_values = [stroke_palette[value] for value in stroke_color_values]
        path_markup = _tl_explosion_path_markup(
            d_values=d_values,
            d_times=d_times,
            progress_values=progress_values,
            progress_times=progress_times,
            stroke_width_values=stroke_width_values,
            stroke_width_times=stroke_width_times,
            stroke_class_values=stroke_class_values,
            stroke_color_times=stroke_color_times,
            total_duration_ms=total_duration_ms,
        )

        elements.append(
            f'<g opacity="{_tl_num(opacity_values[0])}" '
            f'transform="translate({_tl_num(center_values[0][0])} {_tl_num(center_values[0][1])})">'
            f'{_tl_point_animate_transform(center_values, center_times, total_duration_ms, discrete=True)}'
            f'<animate attributeName="opacity" '
            f'values="{";".join(_tl_num(value) for value in opacity_values)}" '
            f'{_tl_key_times_attr(opacity_times, total_duration_ms)} '
            f'dur="{total_duration_ms}ms" repeatCount="indefinite" calcMode="discrete"/>'
            f"{path_markup}</g>"
        )

    return elements


def _tl_ship_elements(
    frames: list[SvgTimelineFrame], context: RenderContext, total_duration_ms: int
) -> list[str]:
    y_top = context.get_cell_position(0.0, SHIP_POSITION_Y)[1]
    times = [frame.time_ms for frame in frames]
    x_values = [_tl_ship_center_x(context, frame.ship_x) for frame in frames]
    times, x_values = _tl_compress_linear_scalar_track(times, x_values, eps=1e-12)
    times, x_values = _tl_pad_local_track(times, x_values, total_duration_ms)
    values = ";".join(_tl_num(value) for value in x_values)
    key_times_attr = _tl_key_times_attr(times, total_duration_ms)

    animate_x = _tl_scalar_animate(
        attribute_name="x",
        values=values,
        key_times_attr=key_times_attr,
        total_duration_ms=total_duration_ms,
        discrete=False,
    )
    return [
        f'<g transform="translate(0 {_tl_num(y_top)})"><use href="#s" x="{_tl_num(x_values[0])}">'
        f"{animate_x}</use></g>"
    ]


def _tl_transition_forced_indices(values: list[float], threshold: float = 0.5) -> set[int]:
    if not values:
        return {0}

    forced = {0, len(values) - 1}
    for index in range(1, len(values)):
        prev_on = values[index - 1] >= threshold
        curr_on = values[index] >= threshold
        if prev_on == curr_on:
            continue
        forced.add(index - 1)
        forced.add(index)
    return forced


def _tl_has_distinct_floats(values: list[float], eps: float = 1e-9) -> bool:
    if not values:
        return False
    first = values[0]
    return any(abs(value - first) > eps for value in values[1:])


def _tl_has_distinct_points(points: list[_Point], eps: float = 1e-9) -> bool:
    if not points:
        return False
    first_x, first_y = points[0]
    return any(abs(x - first_x) > eps or abs(y - first_y) > eps for x, y in points[1:])


def _tl_scalar_animate(
    attribute_name: str,
    values: str,
    key_times_attr: str,
    total_duration_ms: int,
    discrete: bool = False,
) -> str:
    attrs = [
        f'attributeName="{attribute_name}"',
        f'values="{values}"',
    ]
    if key_times_attr:
        attrs.append(key_times_attr)
    attrs.extend(
        [
            f'dur="{total_duration_ms}ms"',
            'repeatCount="indefinite"',
        ]
    )
    if discrete:
        attrs.append('calcMode="discrete"')
    return f'<animate {" ".join(attrs)}/>'


def _tl_scalar_animate_transform(
    transform_type: str,
    values: list[float],
    times: list[int],
    total_duration_ms: int,
    discrete: bool = False,
) -> str:
    if not _tl_has_distinct_floats(values):
        return ""
    value_text = ";".join(_tl_num(value) for value in values)
    key_times_attr = _tl_key_times_attr(times, total_duration_ms)
    attrs = [
        'attributeName="transform"',
        f'type="{transform_type}"',
        f'values="{value_text}"',
    ]
    if key_times_attr:
        attrs.append(key_times_attr)
    attrs.extend(
        [
            f'dur="{total_duration_ms}ms"',
            'repeatCount="indefinite"',
        ]
    )
    if discrete:
        attrs.append('calcMode="discrete"')
    return f'<animateTransform {" ".join(attrs)}/>'


def _tl_point_animate_transform(
    points: list[_Point],
    times: list[int],
    total_duration_ms: int,
    discrete: bool = False,
) -> str:
    if not _tl_has_distinct_points(points):
        return ""
    value_text = ";".join(f"{_tl_num(x)} {_tl_num(y)}" for x, y in points)
    key_times_attr = _tl_key_times_attr(times, total_duration_ms)
    attrs = [
        'attributeName="transform"',
        'type="translate"',
        f'values="{value_text}"',
    ]
    if key_times_attr:
        attrs.append(key_times_attr)
    attrs.extend(
        [
            f'dur="{total_duration_ms}ms"',
            'repeatCount="indefinite"',
        ]
    )
    if discrete:
        attrs.append('calcMode="discrete"')
    return f'<animateTransform {" ".join(attrs)}/>'


def _tl_bullet_shape_elements(context: RenderContext) -> list[str]:
    bullet_rgb = context.bullet_color
    background_rgb = context.background_color
    step = context.cell_size + context.cell_spacing
    shapes: list[str] = []

    for i in range(BULLET_TRAILING_LENGTH):
        trail_y = (i + 1) * BULLET_TRAIL_SPACING * step
        fade = (i + 1) / BULLET_TRAILING_LENGTH / 2
        fill = _tl_blend_hex_over_background(bullet_rgb, background_rgb, fade)
        shapes.append(_tl_center_rect(0.0, trail_y, 0.5, 4.0, fill))

    for offset, fade in [(0.6, 0.3), (0.4, 0.4), (0.2, 0.5), (0.0, 1.0)]:
        fill = _tl_blend_hex_over_background(bullet_rgb, background_rgb, fade)
        shapes.append(_tl_center_rect(0.0, 0.0, 0.5 + offset, 4.0 + offset, fill))
    return shapes


def _tl_center_rect(
    cx: float, cy: float, rx: float, ry: float, fill: str
) -> str:
    x1 = cx - rx
    y1 = cy - ry
    x2 = cx + rx
    y2 = cy + ry
    left = math.floor(min(x1, x2))
    top = math.floor(min(y1, y2))
    right = math.floor(max(x1, x2))
    bottom = math.floor(max(y1, y2))
    width = max(1, right - left + 1)
    height = max(1, bottom - top + 1)
    return (
        f'<rect x="{left}" y="{top}" '
        f'width="{width}" height="{height}" '
        f'fill="{fill}"/>'
    )


def _tl_ship_symbol_elements(context: RenderContext) -> list[str]:
    ship = context.ship_color
    height = context.cell_size
    wing_width = 8

    anchor_x = 24
    anchor_y = 6
    canvas_w = 48
    canvas_h = 32
    center_x = anchor_x
    y_top = anchor_y

    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    draw.polygon(
        [
            (center_x - 2, y_top + height * 0.5),
            (center_x - wing_width, y_top + height * 0.8),
            (center_x - wing_width, y_top + height * 1),
            (center_x - 2, y_top + height * 0.7),
        ],
        fill=(*ship, 128),
    )
    draw.rectangle(
        [
            center_x - wing_width - 1,
            y_top + height * 0.5,
            center_x - wing_width,
            y_top + height * 1,
        ],
        fill=ship,
    )
    draw.polygon(
        [
            (center_x + 2, y_top + height * 0.5),
            (center_x + wing_width, y_top + height * 0.8),
            (center_x + wing_width, y_top + height * 1),
            (center_x + 2, y_top + height * 0.7),
        ],
        fill=(*ship, 128),
    )
    draw.rectangle(
        [
            center_x + wing_width,
            y_top + height * 0.5,
            center_x + wing_width + 1,
            y_top + height * 1,
        ],
        fill=ship,
    )
    draw.polygon(
        [
            (center_x, y_top),
            (center_x - 3, y_top + height * 0.7),
            (center_x, y_top + height),
            (center_x + 3, y_top + height * 0.7),
        ],
        fill=ship,
    )

    pixels = img.load()
    elements: list[str] = []
    for y in range(canvas_h):
        x = 0
        while x < canvas_w:
            _, _, _, alpha = pixels[x, y]
            if alpha == 0:
                x += 1
                continue

            start = x
            while x < canvas_w:
                _, _, _, next_alpha = pixels[x, y]
                if next_alpha != alpha:
                    break
                x += 1

            run_width = x - start
            local_x = start - anchor_x
            local_y = y - anchor_y

            if alpha >= 255:
                elements.append(
                    f'<rect x="{local_x}" y="{local_y}" width="{run_width}" height="1"/>'
                )
            else:
                elements.append(
                    f'<rect x="{local_x}" y="{local_y}" width="{run_width}" height="1" '
                    f'fill-opacity="{_tl_num(alpha / 255)}"/>'
                )
    return elements


def _tl_ship_center_x(context: RenderContext, ship_x: float) -> float:
    x, _ = context.get_cell_position(ship_x, SHIP_POSITION_Y)
    return x + context.cell_size / 2


def _tl_blend_hex_over_background(
    foreground_rgb: tuple[int, int, int],
    background_rgb: tuple[int, int, int],
    alpha: float,
) -> str:
    a = min(1.0, max(0.0, alpha))
    blended = (
        int(round(foreground_rgb[0] * a + background_rgb[0] * (1.0 - a))),
        int(round(foreground_rgb[1] * a + background_rgb[1] * (1.0 - a))),
        int(round(foreground_rgb[2] * a + background_rgb[2] * (1.0 - a))),
    )
    return _tl_hex(blended)


def _tl_assign_compact_names_by_count(
    counts: dict[_NameKey, int], reserved: set[str] | None = None
) -> dict[_NameKey, str]:
    if not counts:
        return {}

    ordered_keys = [key for key, _ in sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))]
    reserved_names = set() if reserved is None else set(reserved)
    index = 0
    names: dict[_NameKey, str] = {}

    for key in ordered_keys:
        while True:
            candidate = _to_compact_name(index)
            index += 1
            if candidate in reserved_names:
                continue
            names[key] = candidate
            break
    return names


def _tl_build_palette_class_maps(
    fill_counts: dict[str, int], stroke_counts: dict[str, int]
) -> tuple[dict[str, str], dict[str, str]]:
    combined_counts: dict[tuple[str, str], int] = {}
    for color, count in fill_counts.items():
        combined_counts[("fill", color)] = count
    for color, count in stroke_counts.items():
        combined_counts[("stroke", color)] = count

    combined_names = _tl_assign_compact_names_by_count(combined_counts)
    fill_palette = {color: combined_names[("fill", color)] for color in fill_counts}
    stroke_palette = {color: combined_names[("stroke", color)] for color in stroke_counts}
    return fill_palette, stroke_palette


def _tl_collect_enemy_fill_color_usage(
    frames: list[SvgTimelineFrame],
    context: RenderContext,
) -> dict[str, int]:
    """Collect approximate enemy color usage to assign compact class names."""
    enemies_by_id: dict[str, tuple[int, int]] = {}
    for enemy in frames[0].enemies:
        enemies_by_id[enemy.id] = (enemy.x, enemy.y)

    enemy_health_by_frame = [{enemy.id: enemy.health for enemy in frame.enemies} for frame in frames]
    color_counts: dict[str, int] = {}

    for enemy_id in sorted(enemies_by_id):
        health_series: list[int | None] = []
        for frame_map in enemy_health_by_frame:
            health_series.append(frame_map.get(enemy_id))

        initial_health = next((value for value in health_series if value is not None), None)
        if initial_health is None:
            continue

        fill_values: list[str] = [
            _tl_hex(context.enemy_colors.get(initial_health, context.enemy_colors[1]))
        ]
        previous: int | None = initial_health
        for health in health_series:
            if health is None:
                previous = None
                continue
            if previous is None:
                previous = health
                continue
            if health != previous:
                fill_values.append(_tl_hex(context.enemy_colors.get(health, context.enemy_colors[1])))
                previous = health

        color_counts[fill_values[0]] = color_counts.get(fill_values[0], 0) + 1
        if len(fill_values) > 1:
            for color in fill_values:
                color_counts[color] = color_counts.get(color, 0) + 1

    return color_counts


def _tl_collect_explosion_stroke_color_usage(
    frames: list[SvgTimelineFrame],
    context: RenderContext,
    total_duration_ms: int,
) -> dict[str, int]:
    explosion_frames = [{explosion.id: explosion for explosion in frame.explosions} for frame in frames]
    slot_tracks = _tl_build_object_slot_tracks(explosion_frames)
    frame_times = [frame.time_ms for frame in frames]

    bullet_rgb = context.bullet_color
    background_rgb = context.background_color
    color_counts: dict[str, int] = {}

    for slot_track in slot_tracks:
        first_active = next((state for state in slot_track if state is not None), None)
        if first_active is None:
            continue

        default_progress = _tl_explosion_progress(first_active)
        default_color = _tl_blend_hex_over_background(
            bullet_rgb, background_rgb, _tl_explosion_fade(default_progress)
        )

        stroke_color_values: list[str] = []
        current_color = default_color
        for explosion in slot_track:
            if explosion is not None:
                current_progress = _tl_explosion_progress(explosion)
                current_color = _tl_blend_hex_over_background(
                    bullet_rgb, background_rgb, _tl_explosion_fade(current_progress)
                )
            stroke_color_values.append(current_color)

        times = [*frame_times, total_duration_ms]
        stroke_color_values.append(stroke_color_values[-1])
        stroke_color_times, stroke_color_values = _tl_compress_discrete_track(times, stroke_color_values)
        stroke_color_times, stroke_color_values = _tl_pad_local_track(
            stroke_color_times, stroke_color_values, total_duration_ms
        )

        color_counts[stroke_color_values[0]] = color_counts.get(stroke_color_values[0], 0) + 1
        for color in stroke_color_values:
            color_counts[color] = color_counts.get(color, 0) + 1

    return color_counts


def _tl_palette_style(fill_palette: dict[str, str], stroke_palette: dict[str, str]) -> str:
    if not fill_palette and not stroke_palette:
        return ""

    rules: list[str] = []
    for color, class_name in sorted(fill_palette.items(), key=lambda item: item[1]):
        rules.append(f".{class_name}{{fill:{color}}}")
    for color, class_name in sorted(stroke_palette.items(), key=lambda item: item[1]):
        rules.append(f".{class_name}{{stroke:{color}}}")
    return "".join(rules)


def _tl_round_to(value: float, step: float) -> float:
    if step <= 0:
        return value
    return round(value / step) * step


def _tl_num_step(value: float, step: float) -> str:
    return _tl_num(_tl_round_to(value, step))


def _tl_watermark_element(width: int, height: int) -> str:
    font = ImageFont.load_default()
    left, top, right, bottom = font.getbbox(WATERMARK_TEXT)
    text_width = right - left
    text_height = bottom - top
    x = width - text_width - 5 + left
    y = height - text_height - 5 + top
    return (
        f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" '
        f'font-family="Aileron, sans-serif" font-size="10px" fill="#646464" '
        f'fill-opacity="{_tl_num(128/255)}">{WATERMARK_TEXT}</text>'
    )
