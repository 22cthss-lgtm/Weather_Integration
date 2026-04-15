# CWA Weather Chart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder `weather_chart` flow with the latest CWA surface weather chart and show it on the dashboard and existing image detail page.

**Architecture:** Extend `CWAService` with a dedicated weather chart resolver that parses `analysis.html` for the latest `FI04.png` URL and timestamp, then falls back to a cache-busted direct image URL if parsing fails. Wire the new fetch path into the existing `/api/images/latest?type=...` endpoint and add the new category to the dashboard while reusing the existing `/images/:type` page.

**Tech Stack:** Python, Flask, requests, unittest, React, React Router, Vite

---

### Task 1: Add backend failing tests for weather chart behavior

**Files:**
- Create: `backend/tests/test_weather_chart.py`
- Test: `backend/tests/test_weather_chart.py`

- [ ] **Step 1: Write the failing test**

```python
def test_resolve_weather_chart_image_url_parses_latest_image_from_html(self):
    html = '''
    <html>
      <body>
        <img src="/Data/fcst_img/FI04.png?t=2026041604-4">
      </body>
    </html>
    '''
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest backend.tests.test_weather_chart -v`
Expected: FAIL with missing `resolve_weather_chart_image_url` or missing API wiring for `weather_chart`

- [ ] **Step 3: Write minimal implementation**

```python
def resolve_weather_chart_image_url(self):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest backend.tests.test_weather_chart -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_weather_chart.py backend/src/services/cwa_service.py backend/src/jobs.py backend/src/api/images.py
git commit -m "feat: add cwa weather chart fetch flow"
```

### Task 2: Add frontend category for weather chart

**Files:**
- Modify: `frontend/src/pages/DashboardPage.jsx`

- [ ] **Step 1: Write the failing expectation mentally from current UI**

```jsx
{ key: "weather_chart", label: "CWA Surface Chart" }
```

- [ ] **Step 2: Update the dashboard category list**

```jsx
const categories = [
  ...
  { key: "weather_chart", label: "CWA Surface Chart" },
];
```

- [ ] **Step 3: Verify the existing `/images/:type` page can render the new payload without more routing changes**

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/DashboardPage.jsx
git commit -m "feat: show cwa weather chart on dashboard"
```
