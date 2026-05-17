# AGENTS.md

## Scope
These instructions apply to the entire repository unless a deeper `AGENTS.md` overrides them.

## Project Overview
- This project generates smart charts and related images for PowerPoint content.
- Backend stack: `FastAPI` with a pipeline-oriented architecture.
- Frontend stack: `Vue 3` + `Vite` in `frontend/`.
- Primary docs live in `README.md` and `docs/`.

## Repository Layout
- `app.py`: main backend startup entry.
- `backend/`: pipeline, PPT parsing, chart generation, image clients, PPT write-back.
- `frontend/`: Vue application and Vite config.
- `tests/`: automated tests.
- `docs/`: design notes, reports, and prompt-engineering references.

## Working Guidelines
- Keep changes minimal and targeted to the user request.
- Preserve the existing split between backend and frontend responsibilities.
- Favor fixing root causes over adding one-off workarounds.
- Reuse existing modules and naming patterns before introducing new files or abstractions.
- Update `README.md` or relevant docs when behavior, setup, or workflows materially change.

## Backend Conventions
- Keep API behavior aligned with the documented routes such as `/api/health`, `/api/process`, `/api/demo-chart`, and `/api/slide-preview`.
- Prefer small, composable helpers inside existing backend modules instead of duplicating pipeline logic.
- Maintain graceful fallbacks for external model/image providers when touching semantic or image generation flows.

## Frontend Conventions
- Keep the frontend compatible with `Vue 3` and the current `Vite` setup.
- Prefer incremental UI changes over large structural rewrites unless requested.
- Preserve existing flows for upload, preview, chart/image generation, progress, and logs.

## Testing and Validation
- For backend-focused changes, start with the smallest relevant test, such as `python -m unittest tests.test_pipeline` when applicable.
- For frontend changes, use the existing `frontend/package.json` scripts such as `npm run build` when validation is needed.
- Do not fix unrelated failing tests unless the user asks.

## Documentation
- Keep user-facing instructions concise and consistent with the current startup commands in `README.md`.
- If adding new environment variables or external-service behavior, document them near the related setup section.

## Notes for Future Agents
- Read `README.md` first for current architecture and workflow context.
- Check `docs/` before making larger product or architecture assumptions.
- If adding nested conventions for a subdirectory, place a more specific `AGENTS.md` there.

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `AMROUTE/PPT-Smart-Chart-Generator`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default mattpocock/skills triage label vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo: use root `CONTEXT.md` and `docs/adr/` for domain language and architecture decisions. See `docs/agents/domain.md`.
