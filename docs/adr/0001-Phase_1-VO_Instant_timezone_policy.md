# ADR 0001: Timezone policy for Instant

## Status
Accepted

## Context
Clinical timelines, audit trails, and time-based queries require consistent and comparable timestamps. Python `datetime` values can be timezone-naive or timezone-aware. Naive timestamps are ambiguous and can be misinterpreted depending on the environment (server locale, developer machine, etc.), leading to incorrect ordering and grouping of clinical events.

## Decision
We introduce a domain Value Object `Instant` that:
- Rejects timezone-naive `datetime` values.
- Accepts timezone-aware `datetime` values.
- Normalizes stored timestamps to UTC.

## Consequences
### Positive
- All timestamps in the domain are comparable and consistent.
- Avoids subtle bugs caused by local timezone assumptions and DST transitions.
- Simplifies persistence and querying (store and compare in UTC).

### Negative / Trade-offs
- Callers must provide timezone-aware datetimes (parsing must be explicit at boundaries).
- Display formatting must be handled in the presentation layer (localization).

## Alternatives considered
1. Accept timezone-aware datetimes and keep their original timezone
   - Rejected: mixed timezones increase complexity in serialization and debugging.
2. Accept naive datetimes assuming a default timezone (e.g., Europe/Madrid)
   - Rejected: introduces silent data corruption for data originating from other systems/timezones.

