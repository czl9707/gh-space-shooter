"""Regression tests for SVG provider internals and structural output behavior."""

from gh_space_shooter.game.svg_timeline import BulletFrameState, SvgTimelineFrame
from gh_space_shooter.output import SvgOutputProvider
from gh_space_shooter.output._svg_entity_minifier import _tl_entity_minify
from gh_space_shooter.output._svg_tracks import (
    _tl_build_object_slot_tracks,
    _tl_compress_linear_scalar_track,
    _tl_compress_points_with_forced,
    _tl_compress_scalar_track,
    _tl_pad_local_track,
)


def test_track_compression_preserves_endpoints_and_monotonic_times() -> None:
    times, values = _tl_compress_scalar_track([0, 10, 20, 30], [1.0, 1.0, 2.0, 2.0])
    padded_times, padded_values = _tl_pad_local_track(times, values, duration_ms=30)

    assert padded_times[0] == 0
    assert padded_times[-1] == 30
    assert padded_values[0] == 1.0
    assert padded_values[-1] == 2.0
    assert all(padded_times[i] <= padded_times[i + 1] for i in range(len(padded_times) - 1))


def test_linear_scalar_track_compression_preserves_turn_points() -> None:
    times, values = _tl_compress_linear_scalar_track(
        [0, 10, 20, 30, 40],
        [0.0, 1.0, 2.0, 3.0, 3.0],
    )
    assert times == [0, 30, 40]
    assert values == [0.0, 3.0, 3.0]



def test_point_compression_with_forced_indices_keeps_ends() -> None:
    points, times = _tl_compress_points_with_forced(
        points=[(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)],
        times=[0, 10, 20],
        forced_indices={0, 2},
    )

    assert points[0] == (0.0, 0.0)
    assert points[-1] == (2.0, 2.0)
    assert times[0] == 0
    assert times[-1] == 20


def test_slot_tracks_can_avoid_same_frame_slot_reuse() -> None:
    frame_maps = [
        {"a": (0, 0)},
        {"b": (10, 10)},  # replacement in the immediate next frame
    ]
    tracks = _tl_build_object_slot_tracks(frame_maps, reuse_slots_within_frame=False)

    # Slot 0 must fully end before slot 1 starts; this avoids visible teleport
    # when linear interpolation is used for motion tracks.
    assert tracks[0] == [(0, 0), None]
    assert tracks[1] == [None, (10, 10)]


def test_entity_minifier_only_applies_when_savings_positive() -> None:
    svg_with_short_values = '<?xml version="1.0"?><svg><g x="0"/><g x="0"/></svg>'
    unchanged = _tl_entity_minify(svg_with_short_values)

    assert unchanged == svg_with_short_values

    long_values = "1;2;3;4;5;6;7;8;9;10;11;12"
    svg_with_repeated_long_values = (
        '<?xml version="1.0"?><svg>'
        f'<g values="{long_values}"/><g values="{long_values}"/></svg>'
    )
    minimized = _tl_entity_minify(svg_with_repeated_long_values)

    assert "<!DOCTYPE svg [" in minimized
    assert "&" in minimized and ";" in minimized
    assert minimized != svg_with_repeated_long_values


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

    result = provider.encode(iter(frames), frame_duration=25)
    assert len(result) < 7000
