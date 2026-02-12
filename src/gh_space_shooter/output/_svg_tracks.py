"""Timeline track compression helpers for SVG output."""

from typing import TypeVar

from ._svg_shared import _tl_num_key_time


_TrackValue = TypeVar("_TrackValue")
_PoolId = TypeVar("_PoolId", int, str)
_PoolValue = TypeVar("_PoolValue")


def _tl_compress_points_with_forced(
    points: list[tuple[float, float]],
    times: list[int],
    forced_indices: set[int],
    eps: float = 1e-6,
) -> tuple[list[tuple[float, float]], list[int]]:
    if len(points) <= 2:
        return points, times

    keep: list[int] = [0]
    for i in range(1, len(points) - 1):
        if i in forced_indices:
            keep.append(i)
            continue
        t0, t1, t2 = times[i - 1], times[i], times[i + 1]
        if t1 == t0 or t2 == t1:
            keep.append(i)
            continue
        dx1 = (points[i][0] - points[i - 1][0]) / (t1 - t0)
        dy1 = (points[i][1] - points[i - 1][1]) / (t1 - t0)
        dx2 = (points[i + 1][0] - points[i][0]) / (t2 - t1)
        dy2 = (points[i + 1][1] - points[i][1]) / (t2 - t1)
        if abs(dx1 - dx2) > eps or abs(dy1 - dy2) > eps:
            keep.append(i)
    keep.append(len(points) - 1)

    return [points[i] for i in keep], [times[i] for i in keep]


def _tl_compress_discrete_points(
    times: list[int], points: list[tuple[float, float]]
) -> tuple[list[int], list[tuple[float, float]]]:
    if not times or not points or len(times) != len(points):
        return [0], [(0.0, 0.0)]

    compact_times = [times[0]]
    compact_points = [points[0]]
    for i in range(1, len(points)):
        if times[i] == compact_times[-1]:
            compact_points[-1] = points[i]
            continue
        if points[i] == compact_points[-1]:
            continue
        compact_times.append(times[i])
        compact_points.append(points[i])
    return compact_times, compact_points


def _tl_compress_discrete_track(
    times: list[int], values: list[str]
) -> tuple[list[int], list[str]]:
    if not times or not values or len(times) != len(values):
        return [0], [values[0] if values else "#000000"]

    compact_times = [times[0]]
    compact_values = [values[0]]
    for i in range(1, len(values)):
        if times[i] == compact_times[-1]:
            compact_values[-1] = values[i]
            continue
        if values[i] == compact_values[-1]:
            continue
        compact_times.append(times[i])
        compact_values.append(values[i])
    return compact_times, compact_values


def _tl_build_object_slot_tracks(
    frame_maps: list[dict[_PoolId, _PoolValue]],
    reuse_slots_within_frame: bool = True,
) -> list[list[_PoolValue | None]]:
    slot_tracks: list[list[_PoolValue | None]] = []
    active_slots: dict[_PoolId, int] = {}
    free_slots: list[int] = []

    for frame_index, frame_map in enumerate(frame_maps):
        current_ids = set(frame_map.keys())

        if reuse_slots_within_frame:
            ended_ids = [object_id for object_id in active_slots if object_id not in current_ids]
            for object_id in ended_ids:
                free_slots.append(active_slots.pop(object_id))
            free_slots.sort()

        for object_id in sorted(current_ids, key=lambda value: str(value)):
            if object_id in active_slots:
                continue
            if free_slots:
                slot_index = free_slots.pop(0)
            else:
                slot_index = len(slot_tracks)
                slot_tracks.append([None] * frame_index)
            active_slots[object_id] = slot_index

        for track in slot_tracks:
            track.append(None)

        for object_id, payload in frame_map.items():
            slot_tracks[active_slots[object_id]][-1] = payload

        if not reuse_slots_within_frame:
            ended_ids = [object_id for object_id in active_slots if object_id not in current_ids]
            for object_id in ended_ids:
                free_slots.append(active_slots.pop(object_id))
            free_slots.sort()

    return slot_tracks


def _tl_compress_scalar_track(
    times: list[int], values: list[float], eps: float = 1e-9
) -> tuple[list[int], list[float]]:
    if not times or not values or len(times) != len(values):
        return [0], [0.0]

    compact_times = [times[0]]
    compact_values = [values[0]]
    for i in range(1, len(values)):
        time_ms = times[i]
        value = values[i]
        if time_ms == compact_times[-1]:
            compact_values[-1] = value
            continue
        if abs(value - compact_values[-1]) <= eps:
            continue
        compact_times.append(time_ms)
        compact_values.append(value)

    return compact_times, compact_values


def _tl_compress_linear_scalar_track(
    times: list[int],
    values: list[float],
    forced_indices: set[int] | None = None,
    eps: float = 1e-9,
) -> tuple[list[int], list[float]]:
    if not times or not values or len(times) != len(values):
        return [0], [0.0]

    if len(times) <= 2:
        return list(times), list(values)

    forced = forced_indices or set()
    keep = [0]
    for i in range(1, len(values) - 1):
        if i in forced:
            keep.append(i)
            continue

        t0, t1, t2 = times[i - 1], times[i], times[i + 1]
        if t1 == t0 or t2 == t1:
            keep.append(i)
            continue

        slope_1 = (values[i] - values[i - 1]) / (t1 - t0)
        slope_2 = (values[i + 1] - values[i]) / (t2 - t1)
        if abs(slope_1 - slope_2) > eps:
            keep.append(i)

    keep.append(len(values) - 1)
    return [times[i] for i in keep], [values[i] for i in keep]


def _tl_pad_local_track(
    times: list[int], values: list[_TrackValue], duration_ms: int
) -> tuple[list[int], list[_TrackValue]]:
    if not times or not values or len(times) != len(values):
        raise ValueError("Local track requires matched time/value samples")

    padded_times = list(times)
    padded_values = list(values)
    if padded_times[0] > 0:
        padded_times.insert(0, 0)
        padded_values.insert(0, padded_values[0])
    if padded_times[-1] < duration_ms:
        padded_times.append(duration_ms)
        padded_values.append(padded_values[-1])
    elif padded_times[-1] > duration_ms:
        padded_times[-1] = duration_ms
    merged_times = [padded_times[0]]
    merged_values = [padded_values[0]]
    for index in range(1, len(padded_times)):
        if padded_times[index] == merged_times[-1]:
            merged_values[-1] = padded_values[index]
            continue
        merged_times.append(padded_times[index])
        merged_values.append(padded_values[index])

    return merged_times, merged_values


def _tl_key_times(times: list[int], total_duration_ms: int) -> str:
    if total_duration_ms <= 0:
        return "0;1"
    return ";".join(_tl_num_key_time(time / total_duration_ms) for time in times)


def _tl_key_times_attr(times: list[int], total_duration_ms: int) -> str:
    if len(times) == 2 and times[0] == 0 and times[1] == total_duration_ms:
        return ""
    return f'keyTimes="{_tl_key_times(times, total_duration_ms)}"'


def _tl_has_distinct_values(values: list[_TrackValue]) -> bool:
    if not values:
        return False
    first = values[0]
    return any(value != first for value in values[1:])
