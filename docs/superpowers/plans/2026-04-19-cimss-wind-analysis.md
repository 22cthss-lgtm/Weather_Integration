# CIMSS Wind Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CIMSS wind analysis integration that fetches the latest currently available West Pacific wind shear and 850mb vorticity images, exposes them as a grouped image payload, and renders them on the dashboard and detail page.

**Architecture:** Reuse the existing grouped-image pattern used by the NSIDC sea ice feature. A new backend service resolves the current CIMSS source page, validates the current direct image URLs, derives `Image Time` from GIF content when possible and falls back to `Last-Modified`, then stores two child image records that are aggregated by the images API for frontend display.

**Tech Stack:** Flask, requests, unittest, React, Vite

---

### Task 1: Backend Tests

**Files:**
- Create: `backend/tests/test_cimss.py`

- [ ] Write failing tests for CIMSS source resolution and grouped API payload.
- [ ] Run `python -m unittest backend.tests.test_cimss` from `backend` and confirm the new tests fail for missing implementation.

### Task 2: Backend Implementation

**Files:**
- Create: `backend/src/services/cimss_service.py`
- Modify: `backend/src/services/registry.py`
- Modify: `backend/src/jobs.py`
- Modify: `backend/src/api/images.py`

- [ ] Implement `CIMSSService` with no-cache requests, current-page validation, GIF time resolution, and two payload emitters.
- [ ] Add grouped fetch wiring and `/api/images/latest?type=cimss_wind_analysis` serialization using wind shear as the primary image.
- [ ] Run `python -m unittest backend.tests.test_cimss` from `backend` and confirm the tests pass.

### Task 3: Frontend Integration

**Files:**
- Modify: `frontend/src/pages/DashboardPage.jsx`
- Modify: `frontend/src/pages/ImagePage.jsx`

- [ ] Add a `CIMSS / Wind Analysis` dashboard card that links to `/images/cimss_wind_analysis`.
- [ ] Render the grouped CIMSS detail page with wind shear and 850mb vorticity entries in order.

### Task 4: Verification

**Files:**
- No code changes expected.

- [ ] Run `python -m unittest backend.tests.test_cimss` from `backend`.
- [ ] If frontend has no test harness, verify by static inspection and report that limitation explicitly.
