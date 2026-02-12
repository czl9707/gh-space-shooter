"""XML entity minification helpers for SVG timelines."""

import re

from ._svg_shared import _to_compact_name


_XML_ATTR_VALUE_RE = re.compile(r'\s[a-zA-Z_:][-\w:.]*="([^"]*)"')
_XML_ATTR_RE = re.compile(r'\s([a-zA-Z_:][-\w:.]*)="([^"]*)"')
_XML_PREDEFINED_ENTITIES = {"lt", "gt", "amp", "apos", "quot"}
_XML_PREFIX_ENTITY_ATTRS = {"keyTimes", "values"}


def _tl_entity_minify(svg_markup: str) -> str:
    if not svg_markup:
        return svg_markup

    values = _XML_ATTR_VALUE_RE.findall(svg_markup)
    if not values:
        return svg_markup

    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1

    ordered_values = sorted(
        counts.keys(),
        key=lambda value: (
            -(counts[value] * len(value)),
            -counts[value],
            -len(value),
            value,
        ),
    )

    selected: list[tuple[str, str]] = []
    used_names = set(_XML_PREDEFINED_ENTITIES)
    name_index = 0
    for value in ordered_values:
        count = counts[value]
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
    prefix_counts: dict[tuple[str, str], int] = {}
    for attribute, value in _XML_ATTR_RE.findall(svg_markup):
        if attribute not in _XML_PREFIX_ENTITY_ATTRS:
            continue
        if "&" in value or ";" not in value:
            continue
        tokens = value.split(";")
        if len(tokens) < 6:
            continue

        token_limit = min(len(tokens) - 1, 320)
        parts: list[str] = []
        for index in range(token_limit):
            parts.append(tokens[index])
            if index < 3:
                continue
            prefix = ";".join(parts)
            if len(prefix) < 30:
                continue
            key = (attribute, prefix)
            prefix_counts[key] = prefix_counts.get(key, 0) + 1

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
