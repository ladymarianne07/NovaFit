# NovaFitness API Documentation

## Overview

RESTful API for private pilot fitness tracking application. Designed for ~10 users over 6 months with local deployment and zero cloud costs.

## Base URL
- Development: `http://localhost:8000`
- With tunnel: `https://your-tunnel-url.ngrok.io` (or Cloudflare Tunnel)

## Authentication

All endpoints except registration, login, and health checks require Bearer token authentication.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## Endpoints

### Authentication

#### POST `/auth/register`
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": null
}
```

#### POST `/auth/login`
Login and receive JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST `/auth/logout`
Logout (client-side token invalidation).

Since JWT tokens are stateless, logout is handled by the client removing the token from storage.

**Response (200):**
```json
{
  "message": "Logout successful",
  "instruction": "Remove the access token from your client storage"
}
```

### User Management

#### GET `/users/me`
Get current user profile.

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T10:00:00Z"
}
```

#### PUT `/users/me`
Update current user profile.

**Request:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

### Events/Activities

#### POST `/events/`
Create a new event.

**Request:**
```json
{
  "event_type": "workout",
  "title": "Morning Run",
  "description": "5km run in the park",
  "data": {
    "distance": 5.0,
    "duration": 30,
    "calories": 300,
    "route": "Park Loop"
  },
  "event_timestamp": "2024-01-01T07:00:00Z"
}
```

**Response (201):**
```json
{
  "id": 1,
  "user_id": 1,
  "event_type": "workout",
  "title": "Morning Run",
  "description": "5km run in the park",
  "data": {
    "distance": 5.0,
    "duration": 30,
    "calories": 300,
    "route": "Park Loop"
  },
  "event_timestamp": "2024-01-01T07:00:00Z",
  "created_at": "2024-01-01T07:05:00Z",
  "is_deleted": false
}
```

#### GET `/events/`
Get user events with optional filtering.

**Query Parameters:**
- `event_type` (optional): Filter by event type
- `start_date` (optional): ISO datetime, events after this date
- `end_date` (optional): ISO datetime, events before this date
- `limit` (optional, 1-100): Number of events to return (default: 50)
- `offset` (optional): Number of events to skip (default: 0)

**Example:** `/events/?event_type=workout&limit=10&offset=0`

**Response (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "event_type": "workout",
    "title": "Morning Run",
    "description": "5km run",
    "data": {"distance": 5.0, "calories": 300},
    "event_timestamp": "2024-01-01T07:00:00Z",
    "created_at": "2024-01-01T07:05:00Z",
    "is_deleted": false
  }
]
```

#### GET `/events/{event_id}`
Get specific event by ID.

#### PUT `/events/{event_id}`
Update event (limited fields for data integrity).

**Request:**
```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

#### DELETE `/events/{event_id}`
Soft delete event (sets `is_deleted = true`).

#### GET `/events/stats/summary`
Get event statistics for current user.

**Response (200):**
```json
{
  "total_events": 25,
  "event_types": {
    "workout": 15,
    "meal": 8,
    "weight": 2
  },
  "date_range": {
    "first_event": "2024-01-01T00:00:00Z",
    "last_event": "2024-01-15T00:00:00Z"
  }
}
```

### Health & Status

#### GET `/`
Basic health check.

#### GET `/health`
Detailed health status.

## Event Types & Data Examples

### Workout Event
```json
{
  "event_type": "workout",
  "title": "Morning Run",
  "data": {
    "type": "running",
    "distance": 5.0,
    "duration": 30,
    "calories": 300,
    "pace": "6:00",
    "heart_rate_avg": 150
  }
}
```

### Meal Event
```json
{
  "event_type": "meal",
  "title": "Breakfast",
  "data": {
    "calories": 400,
    "protein": 20,
    "carbs": 45,
    "fat": 15,
    "foods": ["oatmeal", "banana", "almond milk"]
  }
}
```

### Weight Event
```json
{
  "event_type": "weight",
  "title": "Weekly Weigh-in",
  "data": {
    "weight": 70.5,
    "unit": "kg",
    "body_fat": 15.2
  }
}
```

### Sleep Event
```json
{
  "event_type": "sleep",
  "title": "Night Sleep",
  "data": {
    "duration": 8.5,
    "quality": "good",
    "bedtime": "22:30",
    "wake_time": "07:00"
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Event not found"
}
```

### 409 Conflict
```json
{
  "detail": "Email already registered"
}
```

## Security Considerations

1. **JWT Tokens**: 1-year expiration (persistent sessions until manual logout)
2. **Password Hashing**: bcrypt with salt
3. **CORS**: Configured for PWA origins
4. **Data Isolation**: Users can only access their own data
5. **SQL Injection Protection**: SQLAlchemy ORM handles parameterization
6. **Input Validation**: Pydantic schemas validate all inputs

**Note**: Tokens are set to expire after 1 year to provide persistent sessions for PWA users. Users stay logged in until they manually log out or clear their browser data.

## Database Migration Notes

**SQLite → PostgreSQL Migration Path:**

1. Export data from SQLite:
   ```python
   # Export script (create when needed)
   python -m app.scripts.export_data
   ```

2. Change `DATABASE_URL` in config to PostgreSQL:
   ```
   DATABASE_URL=postgresql://user:pass@localhost/novafitness
   ```

3. Run database initialization:
   ```bash
   python -m app.db.init_db
   ```

4. Import data:
   ```python
   python -m app.scripts.import_data
   ```

The codebase is designed for this migration with zero code changes - just configuration updates.