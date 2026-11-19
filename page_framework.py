"""Reusable rendering framework for gas meter point information sections."""

from dataclasses import dataclass, field
from datetime import date, datetime
from html import escape
from typing import Any, Iterable


@dataclass
class Field:
    label: str
    value: Any
    tooltip: str | None = None


@dataclass
class Section:
    """Section state is data, no_data, or failed; failures remain visible."""

    title: str
    state: str
    fields: list[Field] = field(default_factory=list)
    records: list[dict[str, Any]] = field(default_factory=list)
    record_fields: list[tuple[str, str, str | None]] = field(default_factory=list)
    start_key: str = "start_date"
    end_key: str = "end_date"


def _parse_date(value: Any) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def is_current_record(record: dict[str, Any], today: date | None = None,
                      start_key: str = "start_date", end_key: str = "end_date") -> bool:
    """Apply inclusive start/end dates; a missing end date remains current."""
    today = today or date.today()
    start_value = record.get(start_key)
    end_value = record.get(end_key)
    # Records without date fields are ordinary current data, not history.
    if start_value is None and end_value is None:
        return True
    start = _parse_date(start_value)
    end = _parse_date(end_value)
    if start is None:
        return False
    return start <= today and (end is None or today <= end)


def order_current_and_historical(records: Iterable[dict[str, Any]], today: date | None = None,
                                 start_key: str = "start_date", end_key: str = "end_date"):
    """Return current records, then historical records newest to oldest."""
    today = today or date.today()
    current, historical = [], []
    for record in records:
        target = current if is_current_record(record, today, start_key, end_key) else historical
        target.append(record)
    historical.sort(key=lambda row: _parse_date(row.get(start_key)) or date.min, reverse=True)
    return current, historical


def _field_markup(field: Field, section_id: str, index: int) -> str:
    value = "" if field.value is None else str(field.value)
    tooltip = ""
    if field.tooltip:
        tooltip_id = f"{section_id}-tip-{index}"
        tooltip = (f' <span class="tooltip" tabindex="0" aria-label="More information" '
                   f'aria-describedby="{tooltip_id}">i</span>'
                   f'<span class="tooltip-text" role="tooltip" id="{tooltip_id}">'
                   f'{escape(field.tooltip)}</span>')
    return f"<dt>{escape(field.label)}{tooltip}</dt><dd>{escape(value)}</dd>"


def _fields_markup(fields: list[Field], section_id: str) -> str:
    values = [f for f in fields if f.value is not None and str(f.value).strip()]
    if not values:
        return ""
    return '<dl class="field-list">' + "".join(
        _field_markup(item, section_id, i) for i, item in enumerate(values)
    ) + "</dl>"


def _record_markup(record: dict[str, Any], record_fields: list[tuple[str, str, str | None]],
                   section_id: str, index: int) -> str:
    fields = [Field(label, record.get(key), tooltip) for key, label, tooltip in record_fields]
    content = _fields_markup(fields, f"{section_id}-record-{index}")
    return f'<article class="record">{content}</article>' if content else ""


def render_section(section: Section, index: int, today: date | None = None) -> str:
    if section.state == "no_data":
        return ""
    section_id = f"section-{index}"
    if section.state == "failed":
        content = '<p class="error" role="alert">Failed to load data</p>'
    elif section.state == "data":
        if section.records:
            current, historical = order_current_and_historical(
                section.records, today, section.start_key, section.end_key
            )
            current_markup = "".join(
                _record_markup(row, section.record_fields, section_id, i)
                for i, row in enumerate(current)
            )
            historic_markup = "".join(
                _record_markup(row, section.record_fields, section_id + "-history", i)
                for i, row in enumerate(historical)
            )
            history = (f'<details class="history"><summary>Show historical records '
                       f'({len(historical)})</summary>{historic_markup}</details>'
                       if historical else "")
            content = current_markup + history
        else:
            content = _fields_markup(section.fields, section_id)
        if not content:
            return ""
    else:
        raise ValueError(f"Unknown section state: {section.state}")
    return (f'<section class="info-section"><details open><summary>{escape(section.title)}'
            f'</summary><div class="section-content">{content}</div></details></section>')


def render_information_page(mprn: str, sections: Iterable[Section], today: date | None = None) -> str:
    content = "".join(render_section(section, i, today) for i, section in enumerate(sections))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meter Information — {escape(str(mprn))}</title><style>
:root{{--ink:#172b4d;--blue:#005ea8;--border:#b1b4b6;--pale:#f3f2f1;--error:#b42318}}
*{{box-sizing:border-box}}body{{font:1rem/1.5 system-ui,sans-serif;max-width:64rem;margin:1.5rem auto;padding:0 1rem;color:var(--ink);overflow-wrap:anywhere}}
a{{color:var(--blue)}}h1{{font-size:clamp(1.5rem,5vw,2rem)}}
.info-section{{border:1px solid var(--border);margin:1rem 0;background:white}}
.info-section>details>summary{{cursor:pointer;font-size:1.15rem;font-weight:700;padding:.85rem 1rem;background:var(--pale)}}
.section-content{{padding:.5rem 1rem 1rem}}.field-list{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2fr);gap:.45rem 1rem;margin:.5rem 0}}
dt{{font-weight:700}}dd{{margin:0;min-width:0;overflow-wrap:anywhere}}.record{{padding:.6rem 0;border-bottom:1px solid #d8d8d8}}
.record:last-child{{border-bottom:0}}.history{{margin-top:.75rem;border-top:1px solid var(--border);padding-top:.65rem}}
.history>summary{{cursor:pointer;color:var(--blue);font-weight:700}}.error{{padding:.75rem;border-left:4px solid var(--error);background:#fff2f0}}
.tooltip{{display:inline-flex;align-items:center;justify-content:center;border:1px solid currentColor;border-radius:50%;width:1.15rem;height:1.15rem;font-size:.8rem;cursor:help;position:relative}}
.tooltip-text{{display:none;position:absolute;z-index:2;max-width:min(20rem,85vw);padding:.6rem;background:#172b4d;color:white;border-radius:.2rem;font-weight:400}}
.tooltip:hover+.tooltip-text,.tooltip:focus+.tooltip-text{{display:block}}
@media(max-width:360px){{body{{padding:0 .6rem;margin:1rem auto}}.field-list{{grid-template-columns:1fr;gap:.1rem}}dd{{margin-bottom:.55rem}}.info-section>details>summary{{padding:.7rem}}.section-content{{padding:.5rem .7rem}}}}
</style></head><body><p><a href="/">Search another MPRN</a></p><h1>Meter Information</h1>
<p><strong>MPRN:</strong> {escape(str(mprn))}</p>{content}</body></html>"""
