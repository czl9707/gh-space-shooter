"""XML entity minification helpers for SVG timelines."""

import re

from ._svg_shared import _to_compact_name


_XML_ATTR_VALUE_RE = re.compile(r'\s[a-zA-Z_:][-\w:.]*="([^"]*)"')
_XML_PREDEFINED_ENTITIES = {"lt", "gt", "amp", "apos", "quot"}
_VALUES_ATTR = "values"
_KEY_TIMES_ATTR = "keyTimes"


def _tl_entity_minify(svg_markup: str) -> str:
    if not svg_markup:
        return svg_markup

    counts: dict[str, int] = {}
    for match in _XML_ATTR_VALUE_RE.finditer(svg_markup):
        value = match.group(1)
        counts[value] = counts.get(value, 0) + 1

    if not counts:
        return svg_markup

    ordered_values = sorted(
        counts.items(),
        key=lambda item: (
            -(item[1] * len(item[0])),
            -item[1],
            -len(item[0]),
            item[0],
        ),
    )

    selected: list[tuple[str, str]] = []
    used_names = set(_XML_PREDEFINED_ENTITIES)
    name_index = 0
    for value, count in ordered_values:
        if count < 2:
            continue

        name, next_index = _tl_next_available_entity_name(name_index, used_names)

        entity_ref = f"&{name};"
        definition = f'<!ENTITY {name} "{value}">'
        savings = count * (len(value) - len(entity_ref)) - len(definition)
        if savings <= 0:
            continue
        used_names.add(name)
        name_index = next_index
        selected.append((name, value))

    if not selected:
        minimized = svg_markup
    else:
        # Build a single regex matching all selected values in attribute context
        # and replace in one pass instead of N sequential str.replace() calls.
        value_to_entity = {value: f"&{name};" for name, value in selected}
        escaped_values = [re.escape(value) for _, value in selected]
        # Sort by length descending so longer values match first
        escaped_values.sort(key=len, reverse=True)
        bulk_pattern = re.compile(r'="(' + "|".join(escaped_values) + r')"')
        minimized = bulk_pattern.sub(
            lambda m: f'="{value_to_entity[m.group(1)]}"', svg_markup
        )

    for _ in range(20):
        name, next_index = _tl_next_available_entity_name(name_index, used_names)
        best_prefix = _tl_best_prefix_entity_candidate(minimized, name)
        if best_prefix is None:
            break
        attribute, prefix = best_prefix
        pattern = re.compile(rf'(\s{attribute}="){re.escape(prefix)}')
        minimized, replacements = pattern.subn(
            lambda match: f'{match.group(1)}&{name};',
            minimized,
        )
        if replacements < 2:
            continue
        used_names.add(name)
        name_index = next_index
        selected.append((name, prefix))

    if not selected:
        return svg_markup

    entity_definitions = "".join(f'<!ENTITY {name} "{value}">' for name, value in selected)
    doctype = f"<!DOCTYPE svg [{entity_definitions}]>"
    xml_decl_match = re.match(r"^\<\?xml[^>]+\?\>", minimized)
    if xml_decl_match is None:
        return f"{doctype}{minimized}"
    xml_decl = xml_decl_match.group(0)
    rest = minimized[len(xml_decl) :]
    return f"{xml_decl}{doctype}{rest}"


def _tl_next_available_entity_name(
    name_index: int,
    used_names: set[str],
) -> tuple[str, int]:
    current = name_index
    while True:
        candidate = _to_compact_name(current)
        current += 1
        if candidate in used_names:
            continue
        return candidate, current


def _tl_best_prefix_entity_candidate(svg_markup: str, name: str) -> tuple[str, str] | None:
    attribute_value_counts: dict[tuple[str, str], int] = {}
    for attribute, value in _tl_iter_prefix_attribute_values(svg_markup):
        if "&" in value or ";" not in value:
            continue
        key = (attribute, value)
        attribute_value_counts[key] = attribute_value_counts.get(key, 0) + 1

    if not attribute_value_counts:
        return None

    prefix_counts: dict[tuple[str, str], int] = {}
    for (attribute, value), occurrence_count in attribute_value_counts.items():
        semicolon_positions: list[int] = []
        search_start = 0
        for _ in range(320):
            position = value.find(";", search_start)
            if position < 0:
                break
            semicolon_positions.append(position)
            search_start = position + 1

        if len(semicolon_positions) < 5:
            continue

        for position in semicolon_positions[3:]:
            if position < 30:
                continue
            prefix = value[:position]
            key = (attribute, prefix)
            prefix_counts[key] = prefix_counts.get(key, 0) + occurrence_count

    if not prefix_counts:
        return None

    entity_ref = f"&{name};"
    best_key: tuple[str, str] | None = None
    best_savings = 0
    for key, count in prefix_counts.items():
        if count < 2:
            continue
        _, prefix = key
        definition = f'<!ENTITY {name} "{prefix}">'
        savings = count * (len(prefix) - len(entity_ref)) - len(definition)
        if savings <= 0:
            continue
        if savings > best_savings:
            best_savings = savings
            best_key = key

    return best_key


def _tl_iter_prefix_attribute_values(svg_markup: str) -> list[tuple[str, str]]:
    values_marker = f'{_VALUES_ATTR}="'
    key_times_marker = f'{_KEY_TIMES_ATTR}="'
    values_marker_len = len(values_marker)
    key_times_marker_len = len(key_times_marker)

    entries: list[tuple[str, str]] = []
    search_start = 0
    while True:
        values_pos = svg_markup.find(values_marker, search_start)
        key_times_pos = svg_markup.find(key_times_marker, search_start)
        if values_pos < 0 and key_times_pos < 0:
            break

        if values_pos >= 0 and (key_times_pos < 0 or values_pos < key_times_pos):
            attribute = _VALUES_ATTR
            attr_pos = values_pos
            marker_len = values_marker_len
        else:
            attribute = _KEY_TIMES_ATTR
            attr_pos = key_times_pos
            marker_len = key_times_marker_len

        if attr_pos <= 0 or not svg_markup[attr_pos - 1].isspace():
            search_start = attr_pos + 1
            continue

        value_start = attr_pos + marker_len
        value_end = svg_markup.find('"', value_start)
        if value_end < 0:
            break
        entries.append((attribute, svg_markup[value_start:value_end]))
        search_start = value_end + 1

    return entries
