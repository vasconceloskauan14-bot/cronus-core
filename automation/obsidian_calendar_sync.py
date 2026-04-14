from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import urllib.request


@dataclass
class CalendarEvent:
    uid: str
    summary: str
    description: str
    start_at: datetime
    end_at: datetime | None = None


def load_calendar_state(path: Path) -> dict:
    if not path.exists():
        return {"processed_events": {}, "last_sync_at": ""}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    data.setdefault("processed_events", {})
    data.setdefault("last_sync_at", "")
    return data


def save_calendar_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class ObsidianCalendarSync:
    def __init__(self, source: str, state_path: Path, window_days: int = 1):
        self.source = source.strip()
        self.state_path = state_path
        self.window_days = max(int(window_days), 0)

    def sync(self, research_callback) -> dict:
        if not self.source:
            raise RuntimeError("Nenhuma fonte de calendario configurada. Defina OBSIDIAN_CALENDAR_SOURCE com um arquivo .ics ou URL ICS.")

        calendar_text = self._read_source()
        events = self._parse_ics(calendar_text)
        target_events = self._select_relevant_events(events)
        state = load_calendar_state(self.state_path)

        results = []
        for event in target_events:
            query = self._extract_query(event)
            if not query:
                continue

            fingerprint = f"{event.uid}|{event.start_at.isoformat()}|{query}"
            if fingerprint in state["processed_events"]:
                results.append(
                    {
                        "event": event.summary,
                        "date": event.start_at.isoformat(timespec="minutes"),
                        "ok": True,
                        "skipped": True,
                        "reason": "Evento ja processado",
                    }
                )
                continue

            result = research_callback(
                query=query,
                folder=f"Memoria/Calendario/{event.start_at.strftime('%Y-%m-%d')}",
            )
            state["processed_events"][fingerprint] = {
                "summary": event.summary,
                "query": query,
                "processed_at": datetime.now().isoformat(timespec="seconds"),
                "note_path": result.get("note_relative_path", ""),
            }
            results.append(
                {
                    "event": event.summary,
                    "date": event.start_at.isoformat(timespec="minutes"),
                    "ok": True,
                    "query": query,
                    "note_path": result.get("note_relative_path", ""),
                }
            )

        state["last_sync_at"] = datetime.now().isoformat(timespec="seconds")
        if len(state["processed_events"]) > 300:
            items = list(state["processed_events"].items())[-300:]
            state["processed_events"] = dict(items)
        save_calendar_state(self.state_path, state)

        return {
            "ok": True,
            "source": self.source,
            "processed": len(results),
            "results": results,
            "last_sync_at": state["last_sync_at"],
        }

    def _read_source(self) -> str:
        if self.source.startswith(("http://", "https://")):
            req = urllib.request.Request(self.source, headers={"User-Agent": "ULTIMATE-CRONUS/1.0"})
            with urllib.request.urlopen(req, timeout=20) as response:
                return response.read().decode("utf-8", errors="ignore")

        path = Path(self.source)
        if not path.is_absolute():
            path = (Path(__file__).resolve().parent.parent / path).resolve()
        if not path.exists():
            raise RuntimeError(f"Calendario nao encontrado: {path}")
        return path.read_text(encoding="utf-8", errors="ignore")

    def _parse_ics(self, content: str) -> list[CalendarEvent]:
        unfolded_lines = []
        for raw_line in content.splitlines():
            if raw_line.startswith((" ", "\t")) and unfolded_lines:
                unfolded_lines[-1] += raw_line[1:]
            else:
                unfolded_lines.append(raw_line)

        events = []
        current: dict[str, str] | None = None
        for line in unfolded_lines:
            if line == "BEGIN:VEVENT":
                current = {}
                continue
            if line == "END:VEVENT":
                if current:
                    event = self._build_event(current)
                    if event:
                        events.append(event)
                current = None
                continue
            if current is None or ":" not in line:
                continue

            left, value = line.split(":", 1)
            key = left.split(";", 1)[0].upper()
            current[key] = value.strip()

        return events

    def _build_event(self, payload: dict[str, str]) -> CalendarEvent | None:
        start_raw = payload.get("DTSTART", "")
        if not start_raw:
            return None
        start_at = self._parse_datetime(start_raw)
        end_raw = payload.get("DTEND", "")
        end_at = self._parse_datetime(end_raw) if end_raw else None
        return CalendarEvent(
            uid=payload.get("UID", f"evento-{start_raw}"),
            summary=payload.get("SUMMARY", "").strip(),
            description=payload.get("DESCRIPTION", "").replace("\\n", "\n").strip(),
            start_at=start_at,
            end_at=end_at,
        )

    def _parse_datetime(self, value: str) -> datetime:
        value = value.strip()
        if len(value) == 8:
            return datetime.strptime(value, "%Y%m%d")
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ")
        return datetime.strptime(value, "%Y%m%dT%H%M%S")

    def _select_relevant_events(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        today = date.today()
        limit_date = today + timedelta(days=self.window_days)
        selected = []
        for event in events:
            event_date = event.start_at.date()
            if today <= event_date <= limit_date:
                selected.append(event)
        selected.sort(key=lambda item: item.start_at)
        return selected

    def _extract_query(self, event: CalendarEvent) -> str:
        summary = event.summary.strip()
        description = event.description.strip()
        markers = ("pesquisa:", "radar:", "research:")

        for marker in markers:
            if summary.casefold().startswith(marker):
                return summary[len(marker):].strip()

        for line in description.splitlines():
            lowered = line.casefold().strip()
            for marker in markers:
                if lowered.startswith(marker):
                    return line[len(marker):].strip()

        if any(keyword in summary.casefold() for keyword in ("editor", "edição", "edicao", "pesquisa", "pesquisar")):
            return summary

        return ""
