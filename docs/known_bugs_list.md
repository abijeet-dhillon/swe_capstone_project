# Known Bugs List

## Review Scope

- Inspected product-facing behavior across the Electron frontend (`frontend/src/renderer/src`), generated portfolio frontend (`portfolio-template/src`), and FastAPI routers (`src/api/routers`, `src/insights/api.py`, `src/projects/api.py`).
- Mapped and traced flows for: dashboard/home navigation, upload + consent, project list/detail/edit/remove, filtering/sorting/search, resume and portfolio generation, skills timeline/progression displays, public/private mode behavior, and visible notices/errors/empty states.
- Compared user-facing implementation against documented milestone/API expectations in `README.md` and `docs/api/API_REFERENCE.md`.

## Confirmed Bugs

### Bug 1: Projects view is capped at 50 results with no pagination UI

**Area:** Projects list filtering/search  
**Issue:** The frontend hardcodes `limit: 50` and `offset: 0` for every filter request and provides no next/previous/page controls.  
**When it occurs:** Any project query where total matches exceed 50.  
**User-visible impact:** Users can see “X found” totals above 50 but cannot access records beyond the first 50 results.  
**Likely type:** incomplete feature implementation  
**Priority:** low  
**Evidence:** `frontend/src/renderer/src/ProjectsView.tsx` (fixed `limit: 50, offset: 0` in `buildFilter`; line ~113; toolbar has no pagination controls; lines ~293-347), `src/api/routers/filter.py` (request model supports `limit`/`offset`; lines ~98-126), `src/insights/project_filter.py` (SQL pagination implemented; lines ~316-325).

### Bug 2: Resume edit/customization endpoint is not surfaced in the UI

**Area:** Resume generation and customization flow  
**Issue:** Backend supports editing resume bullets (`POST /resume/{id}/edit`), but frontend provides no editable bullets UI and no API wrapper for that route.  
**When it occurs:** After resume content exists and user wants to customize bullet text before final output.  
**User-visible impact:** Resume bullets are view-only in the app; users cannot perform documented resume bullet edits from the product UI.  
**Likely type:** missing UI wiring  
**Priority:** medium  
**Evidence:** `README.md` (milestone includes `POST /resume/{id}/edit`; line 76), `src/api/routers/resume.py` (edit endpoint implemented; lines ~367-378), `frontend/src/renderer/src/api.ts` (resume section includes `getResume`, `generateResume`, `generateResumePdf` only, no resume edit call; lines ~432-492), `frontend/src/renderer/src/components/DetailPanel.tsx` (resume bullets rendered read-only; lines ~126-134).

### Bug 3: Portfolio customization is only partially exposed from the frontend

**Area:** Portfolio edit/customization flow  
**Issue:** Frontend edit modal only updates project name/tagline/description/type/complexity/summary via `/projects/{id}` patch; portfolio-specific editable fields like `key_features` and `is_collaborative` are not editable from UI despite backend support.  
**When it occurs:** User wants to refine portfolio feature bullets or collaboration flag before generating/viewing portfolio outputs.  
**User-visible impact:** Users cannot access full portfolio customization capabilities described by API/requirements from the app interface.  
**Likely type:** missing UI wiring  
**Priority:** medium  
**Evidence:** `frontend/src/renderer/src/ProjectsView.tsx` (editable fields limited to six entries; lines ~35-42 and modal fields ~546-603), `frontend/src/renderer/src/api.ts` (`ProjectEditRequest` excludes `key_features`/`is_collaborative`; lines ~88-94), `src/api/routers/portfolio.py` (`POST /portfolio/{project_id}/edit` accepts `key_features` and `is_collaborative`; lines ~566-591).

### Bug 4: Portfolio detail sections in frontend depend on fields omitted by default portfolio API response

**Area:** Project detail/expanded cards (portfolio preview)  
**Issue:** Frontend tries to render `key_features` and `evolution`, but default `GET /portfolio/{id}` response does not include those fields unless template-specific paths are used.  
**When it occurs:** Opening project details or expanded project cards expecting feature list/timeline metadata.  
**User-visible impact:** Key sections are frequently missing/empty even when portfolio data exists, making detail panels look incomplete.  
**Likely type:** backend-frontend mismatch  
**Priority:** medium  
**Evidence:** `frontend/src/renderer/src/api.ts` (`getPortfolio` maps `raw.key_features` and `raw.evolution`; lines ~401-421), `frontend/src/renderer/src/ProjectsView.tsx` (renders Key Features/Timeline conditionally; lines ~678-687 and ~713-724), `frontend/src/renderer/src/components/DetailPanel.tsx` (renders Key Features block; lines ~115-123), `src/api/routers/portfolio.py` (default response contains summary/description/key_skills/key_metrics but not `key_features` or `evolution`; lines ~535-543, return at ~563).

### Bug 5: Manual upload path bypasses .zip validation in browser mode

**Area:** Upload/import flow (manual path entry)  
**Issue:** Manual path submission accepts any non-empty path and skips the `.zip` extension validation enforced in drag/drop and file picker flows.  
**When it occurs:** Using browser-mode “Use Path” input instead of selecting/dropping a ZIP.  
**User-visible impact:** Users can proceed with invalid paths despite “Accepts .zip files only,” causing avoidable late-stage API errors.  
**Likely type:** validation gap  
**Priority:** low  
**Evidence:** `frontend/src/renderer/src/components/UploadZone.tsx` (`handleManualSubmit` calls `pickFile` without zip extension check; lines ~189-194), same file declares `.zip` acceptance in other flows and UI text (“Accepts .zip files only”; line ~243).

### Bug 6: Non-AI runs still populate the AI analysis view with local output

**Area:** Analysis results display / AI analysis tab  
**Issue:** The dedicated “AI Analysis” tab is populated from general project payload fields (portfolio/resume/ranking) even when LLM is disabled, so the tab title overstates what generated the content.  
**When it occurs:** User disables AI-enhanced analysis (`llm_consent = false`) and then opens analysis output that is labeled as AI.  
**User-visible impact:** Users may incorrectly assume the shown analysis was LLM-generated when it is actually local fallback output.  
**Likely type:** backend-frontend mismatch  
**Priority:** low  
**Evidence:** In `feat/llm-analysis-tab`, `frontend/src/renderer/src/components/DetailPanel.tsx` adds an explicit `AI Analysis` tab and labels like “AI Summary” (lines ~93-105 and ~228-233). That tab calls `getAIAnalysis()` (`frontend/src/renderer/src/api.ts` lines ~431-468), which reads from `/projects/{id}` payload fields `portfolio_item.summary`, `resume_item.bullets`, and `global_insights.project_ranking.top_summaries` (lines ~433-449), not from `llm_summaries`. Backend upload computes `use_llm` (`src/api/routers/projects.py` line ~446) but does not return it in the upload response payload (lines ~493-501), so UI cannot distinguish mode. Pipeline only creates `llm_summaries` when `use_llm` is true (`src/pipeline/orchestrator.py` lines ~368-372), while ranking summaries are always generated in step 7 and persisted (`src/pipeline/orchestrator.py` lines ~374-377, `src/project/top_summary.py` lines ~172-218, `src/insights/storage.py` lines ~2668-2680).
