# MuseumSpark API

**Last updated:** 2026-01-15  
**Status:** Canonical API specification for MuseumSpark.  
**Authority**: This document implements the requirements defined in [MasterRequirements.md](MasterRequirements.md), which is the authoritative product specification written by the Product Owner.

This document defines the HTTP API surface for:

- **Walker Art Reciprocal museum dataset access** (browse/search/filter)
- **User personalization** (accounts, favorites, visited)
- **Trip planning** (optional; can start as “lists” and evolve into “trips”)
- **Administrative data curation** (museum CRUD; role-gated)

It is designed to align with:

- `Documentation/MasterRequirements.md` (authoritative product requirements and scoring algorithm)
- `data/index/walker-reciprocal.csv` (seed roster of reciprocal museums)
- `data/schema/museum.schema.json` (authoritative museum record model)
- `Documentation/DataSetDesign.md` (dataset methodology + scoring)
- `Documentation/ApplicationArchitecture.md` (deployment + components)

---

## 1. Conventions

### 1.1 Base URL

MuseumSpark is intended to be served from a **single origin** (SPA + API), hosted on a single Azure Windows VM.

- **Base path:** `/api/v1`
- **Content type:** `application/json`

Examples:
- `https://<your-domain>/api/v1/museums`
- `https://<your-domain>/api/v1/auth/login`

### 1.2 Versioning

- Path-based versioning: `/api/v1/...`

### 1.3 Pagination

List endpoints support:
- `limit` (default 50, max 200)
- `offset` (default 0)

Response envelope:

```json
{ "total": 0, "results": [] }
```

### 1.4 Sorting

List endpoints MAY support:
- `sort` (e.g., `priority_score`, `museum_name`)
- `order` (`asc` or `desc`)

Default: `priority_score asc` (lower = better), then `museum_name asc`.

---

## 2. Authentication and Authorization

### 2.1 Authentication method

MuseumSpark uses **JWT bearer tokens** (OAuth2-style; typical FastAPI pattern).

- Public read endpoints (museum browsing) MAY be anonymous.
- Personalization and admin operations require authentication.

### 2.2 Roles

Role-based access is supported via claims in the JWT:

- `viewer` — read-only (authenticated)
- `editor` — can create/update museum records
- `admin` — full read/write/delete + maintenance endpoints

---

## 3. Core Resource: Museum

### 3.1 Data model

The Museum model MUST align with the JSON Schema:

- `data/schema/museum.schema.json`

When the API returns a museum record, field names and types should match the schema.

### 3.2 GET /museums

Retrieve a paginated list of museums with optional filters.

Query parameters (selected):

- Text: `q` (partial match on `museum_name`)
- Location: `city`, `state_province`, `country`
- Classification: `primary_domain`, `museum_type`, `audience_focus`, `status`, `best_season`
- Quality: `reputation`, `collection_tier`, `min_confidence`
- Art/scoring: `min_priority_score`, `max_priority_score`, `min_impressionist_strength`, `min_modern_contemporary_strength`, `min_historical_context_score`, `min_exhibitions_curatorial_authority`, `min_collection_based_strength`, `primary_art`, `is_scored`
- Travel: `time_needed`, `min_estimated_visit_minutes`, `max_estimated_visit_minutes`
- Pagination: `limit`, `offset`

Response: `200 OK`

```json
{
  "total": 3,
  "results": [
    {
      "museum_id": "usa-il-chicago-art-institute-of-chicago",
      "museum_name": "Art Institute of Chicago",
      "city": "Chicago",
      "state_province": "Illinois",
      "country": "USA",
      "primary_domain": "Art",
      "reputation": 0,
      "collection_tier": 0,
      "priority_score": -2.5,
      "is_scored": true
    }
  ]
}
```

### 3.3 GET /museums/{museum_id}

Retrieve full detail of a single museum.

Response: `200 OK`

---

## 4. User Accounts and Personalization

These endpoints support P3 features (favorites/visited) and enable authenticated actions.

### 4.1 POST /auth/register

Create a user account.

- Anonymous
- Response: `201 Created`

### 4.2 POST /auth/login

Authenticate and receive tokens.

- Anonymous
- Response: `200 OK`

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### 4.3 GET /me

Return the authenticated user profile.

- Requires auth
- Response: `200 OK`

### 4.4 Favorites / Visited

Minimal, simple-to-implement endpoints:

- `POST /me/favorites/{museum_id}`
- `DELETE /me/favorites/{museum_id}`
- `GET /me/favorites`

- `POST /me/visited/{museum_id}`
- `DELETE /me/visited/{museum_id}`
- `GET /me/visited`

---

## 5. Trip Planning (Optional, Evolves from Lists)

The original architecture documents include trips/itineraries saved per user. This can be introduced after museum discovery/search is solid.

### 5.1 Trips

- `GET /trips` (requires auth)
- `POST /trips` (requires auth)
- `GET /trips/{trip_id}` (requires auth)
- `PUT /trips/{trip_id}` (requires auth)
- `PATCH /trips/{trip_id}` (requires auth)
- `DELETE /trips/{trip_id}` (requires auth)

### 5.2 Itinerary generation (AI)

AI endpoints MUST be server-side (never call OpenAI from the browser).

- `POST /trips/{trip_id}/itinerary/generate`
- `POST /trips/{trip_id}/itinerary/refine`

Responses should be structured and version-stamped (model, prompt version), even if minimal.

---

## 6. Admin: Museum CRUD (Role-gated)

Admin endpoints manage the museum dataset.

Two acceptable patterns:

1) Reuse `/museums` endpoints but require `editor/admin` for writes.
2) Use an explicit admin namespace: `/admin/museums`.

For clarity, this spec uses the admin namespace.

### 6.1 POST /admin/museums

Create a new museum record.

- Requires role: `editor` or `admin`
- Request body: Museum schema fields
- Response: `201 Created`

### 6.2 PUT /admin/museums/{museum_id}

Full overwrite update.

- Requires role: `editor` or `admin`
- Response: `200 OK`

### 6.3 PATCH /admin/museums/{museum_id}

Partial update.

- Requires role: `editor` or `admin`
- Response: `200 OK`

### 6.4 DELETE /admin/museums/{museum_id}

Delete a museum.

- Requires role: `admin`
- Response: `204 No Content`

### 6.5 POST /admin/museums/recalculate-scores

Trigger a priority score recalculation.

- Requires role: `admin`
- Response: `202 Accepted`

---

## 7. Error Handling

Standard error format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request body is invalid",
    "details": []
  }
}
```

Suggested HTTP status usage:
- `400` invalid request
- `401` unauthenticated
- `403` unauthorized
- `404` not found
- `409` conflict (duplicate ID)
- `422` validation error (FastAPI default)

---

## 8. Consistency Rules (Non-negotiable)

- Museum field names/types MUST match `data/schema/museum.schema.json`.
- Priority scoring behavior MUST match `Documentation/MasterRequirements.md` (authoritative product requirements).
- Priority scoring implementation details in `Documentation/DataSetDesign.md` MUST align with MasterRequirements.md.
- Public read endpoints MUST NOT require auth for basic browsing (unless explicitly changed across the docs).
- AI endpoints MUST be server-side and rate-limited.
- Reputation field MUST use integer scale (0=International, 1=National, 2=Regional, 3=Local), not string values.
- Non-art museums MUST have `is_scored: false` and `priority_score: null`.
