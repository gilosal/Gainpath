# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

*Add reusable patterns discovered during development here.*

---

## US-101: Add field-level validation and status transition guards to Pydantic schemas — COMPLETED

### Files Changed
- `backend/app/schemas/session.py` — Added `SessionStatus`, `SessionType`, `SetType`, `BodySide`, `Feeling` enums; `validate_status_transition()` function; `VALID_STATUS_TRANSITIONS` dict; constrained numeric fields with `ge=0`; added `use_enum_values=True` to `SessionLogUpdate`
- `backend/app/schemas/user.py` — Added `WeightUnit`, `DistanceUnit` enums; replaced bare `str` fields with `Literal` constraints on `running_goal_race`, `running_fitness_level`, `available_equipment`, `weight_training_goal`, `mobility_goal`, `mobility_experience`
- `backend/app/schemas/__init__.py` — Exported new enums and `validate_status_transition`
- `backend/app/routers/sessions.py` — Added status transition validation before setattr; excluded `id` from setattr update loops
- `backend/app/routers/profile.py` — Excluded `id` from setattr update loop
- `backend/app/routers/offline.py` — Excluded `id` from complete_session setattr loop
- `backend/tests/test_sessions.py` — Updated to use enum types; added `TestStatusTransitionValidator` and `TestSetattrExcludesId` classes
- `backend/tests/test_session_completion_pipeline.py` — Updated to use `SessionStatus` enum; added id-exclusion test
- `backend/tests/test_critical_paths.py` — Updated gap tests to expect validation errors instead of arbitrary-string acceptance; added id-exclusion assertion for offline sync

### Validation Added
1. **Status enum**: `SessionStatus` enum (planned/in_progress/completed/skipped) on `SessionLogUpdate.status` and `SessionLogRead.status`
2. **Session type enum**: `SessionType` enum (running/lifting/mobility) on `SessionLogCreate.session_type` and `SessionLogRead.session_type`
3. **Status transition guards**: `validate_status_transition()` prevents invalid transitions (e.g., completed→planned). Called from router before setattr.
4. **Immutable `id` excluded**: All setattr update loops (sessions, sets, profile, offline complete_session) now `pop("id", None)`
5. **Enum constraints**: `SetType`, `Feeling`, `BodySide` enums on set/feedback schemas
6. **Numeric range guards**: `ge=0` on distance/duration/pace/tonnage/weight/reps fields
7. **UserProfileUpdate constraints**: `Literal` types on goal/equipment/experience fields; `WeightUnit`/`DistanceUnit` enums

### All 129 tests pass ✓

