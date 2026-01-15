Here is a complete API schema and specification to support full CRUD operations for managing the Museum Prioritization Dataset. This RESTful API is designed for flexibility, extensibility, and strong data validation, and is suitable for use in a travel planner, cultural explorer platform, or institutional data service.

---

# 🎯 API Specification: Museum Prioritization Dataset

* API Base URL (example): `https://api.museum-prioritizer.com/v1`
* Data Format: JSON
* Authentication: OAuth 2.0 (Bearer Token recommended)
* Rate Limiting: 1000 requests/day per user (configurable)
* Versioning: Path-based (`/v1/`)

---

## 🔁 Core Resource

### Resource Name: `Museum`

Base path: `/museums`

---

## 📘 Data Model: Museum

| Field                    | Type              | Required   | Description                                                       |
| ------------------------ | ----------------- | ---------- | ----------------------------------------------------------------- |
| id                       | UUID              | Yes (auto) | Unique museum identifier                                          |
| name                     | String            | Yes        | Official museum name                                              |
| website_url              | String            | No         | Full URL of the museum homepage                                   |
| country                  | String            | Yes        | ISO country name (e.g., "USA")                                    |
| state                    | String            | No         | U.S. state or Canadian province (full name)                       |
| city                     | String            | Yes        | Museum’s city                                                     |
| type                     | String (Enum)     | Yes        | Type: `Art`, `History`, `Science`, `Mixed`, `Specialty`           |
| time_needed              | String (Enum)     | No         | `Quick stop`, `Half day`, `Full day`                              |
| reputation               | String (Enum)     | No         | `Local`, `Regional`, `National`, `International`                  |
| collection_tier          | String (Enum)     | No         | `Small`, `Moderate`, `Strong`, `Flagship`                         |
| impressionism_strength   | String (Enum)     | No         | `None`, `Minor`, `Moderate`, `Strong`, `Flagship`                 |
| modern_strength          | String (Enum)     | No         | `None`, `Minor`, `Moderate`, `Strong`, `Flagship`                 |
| primary_art_focus        | String            | No         | Dominant art period or collection strength (e.g. `Impressionism`) |
| historical_context_score | Integer           | No         | 1–5 rating of interpretive strength                               |
| priority_score           | Float             | No         | Computed score (lower = better)                                   |
| nearby_museum_count      | Integer           | No         | Count of other museums in the same city on your list              |
| notes                    | String            | No         | Freeform field for travel insights or caveats                     |
| created_at               | ISO8601 Timestamp | Yes (auto) | Created timestamp                                                 |
| updated_at               | ISO8601 Timestamp | Yes (auto) | Last updated timestamp                                            |

---

## 🧾 Endpoints

### GET /museums

Retrieve a paginated list of museums with optional filters.

🔸 Query Parameters:

* `city`, `state`, `country`
* `type`, `reputation`, `collection_tier`
* `min_priority_score`, `max_priority_score`
* `limit`, `offset`

🔸 Response: `200 OK`

```json
{
  "total": 3,
  "results": [
    {
      "id": "17b36a93-b323-41bb-b6f4-ffc0dbfd2f73",
      "name": "Art Institute of Chicago",
      "city": "Chicago",
      "state": "Illinois",
      "country": "USA",
      "type": "Art",
      "reputation": "International",
      "collection_tier": "Flagship",
      "priority_score": 1.2
    }
  ]
}
```

---

### GET /museums/{id}

Retrieve full detail of a single museum.

🔸 Response: `200 OK`

```json
{
  "id": "17b36a93-b323-41bb-b6f4-ffc0dbfd2f73",
  "name": "Art Institute of Chicago",
  "website_url": "https://www.artic.edu",
  "country": "USA",
  "state": "Illinois",
  "city": "Chicago",
  "type": "Art",
  "time_needed": "Full day",
  "reputation": "International",
  "collection_tier": "Flagship",
  "impressionism_strength": "Flagship",
  "modern_strength": "Strong",
  "primary_art_focus": "Impressionism",
  "historical_context_score": 5,
  "priority_score": 1.2,
  "nearby_museum_count": 3,
  "notes": "Must-see Impressionist rooms.",
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

---

### POST /museums

Create a new museum record.

🔸 Request Body:

```json
{
  "name": "Museum of Modern Art",
  "city": "New York",
  "state": "New York",
  "country": "USA",
  "type": "Art",
  "website_url": "https://www.moma.org",
  "time_needed": "Full day",
  "reputation": "International",
  "collection_tier": "Flagship",
  "impressionism_strength": "Moderate",
  "modern_strength": "Flagship",
  "primary_art_focus": "Modern",
  "historical_context_score": 4,
  "nearby_museum_count": 4,
  "notes": "Dense modern collection with global focus."
}
```

🔸 Response: `201 Created`

---

### PUT /museums/{id}

Update an existing museum (full overwrite).

🔸 Request Body: Same as POST
🔸 Response: `200 OK`

---

### PATCH /museums/{id}

Partial update of selected fields.

🔸 Request Body Example:

```json
{
  "historical_context_score": 5,
  "notes": "Added new Impressionist galleries in 2026."
}
```

🔸 Response: `200 OK`

---

### DELETE /museums/{id}

Delete a museum.

🔸 Response: `204 No Content`

---

## ⚙️ Priority Score Recalculation (Optional)

You may expose an internal or external recalculation endpoint if using dynamic score rules.

POST /museums/recalculate-scores
Trigger re-evaluation of all museum scores (e.g., after algorithm change).
🔸 Admin-only
🔸 Response: `202 Accepted`

---

## 🔐 Authentication

Use OAuth 2.0 bearer tokens for all endpoints. Roles may include:

* `admin` — Full read/write/delete access
* `editor` — Can create and update records
* `viewer` — Read-only access

---
