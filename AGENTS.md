# Event Stream Viewer - Implementation Guide

## Architecture

Single-container application with FastAPI backend serving both API and static frontend files.

### Components

1. **Backend (FastAPI)**
   - Async HTTP server
   - MongoDB integration via PyMongo (synchronous driver)
   - HTTP Basic Authentication middleware
   - SSE (Server-Sent Events) for real-time updates
   - Static file serving for built frontend

2. **Frontend (Vue 3)**
   - Single-page application
   - Real-time updates via EventSource (SSE)
   - Filtering and pagination
   - Modal for JSON payload viewing

3. **Database (MongoDB)**
   - External service (not in container)
   - Single collection for events
   - Natural sorting by _id (descending)

## Data Flow

### Event Ingestion
1. External system POSTs to `/api/events` with Basic Auth
2. FastAPI validates credentials
3. Event stored in MongoDB with timestamp
4. All connected SSE clients notified
5. Response returned with event ID

### Event Display
1. Frontend loads initial page via GET `/api/events`
2. SSE connection established to `/api/events/stream`
3. New events pushed to frontend in real-time
4. Frontend updates UI if on page 1 and filters match

### Filtering & Pagination
1. User applies filters (companyId, storeId, entity)
2. Frontend requests filtered page from API
3. MongoDB query with filters and pagination
4. Results displayed in table

## API Endpoints

### POST /api/events
**Auth**: Required (HTTP Basic)
**Body**:
```json
{
  "companyId": "string",
  "storeId": "string",
  "entity": "string",
  "event": "string",
  "payload": {}
}
```
**Response**: `{"id": "string"}`

### GET /api/events
**Query Params**:
- `page` (int, default: 1)
- `companyId` (string, optional)
- `storeId` (string, optional)
- `entity` (string, optional)

**Response**:
```json
{
  "events": [...],
  "total": 100,
  "page": 1,
  "pages": 2
}
```

### GET /api/events/stream
**SSE Stream**: Pushes new events as they arrive
**Format**: `data: {JSON}\n\n`

## Database Schema

**Collection**: `events`

```javascript
{
  _id: ObjectId,           // Auto-generated, used for sorting
  companyId: String,       // Filter field
  storeId: String,         // Filter field
  entity: String,          // Filter field (Menu, Check, etc.)
  event: String,           // Event type (Updated, Closed, etc.)
  payload: Object,         // Full event data
  timestamp: ISODate       // UTC timestamp
}
```

**Indexes**: None required initially (natural _id index sufficient for demo)

## Authentication

HTTP Basic Authentication via Authorization header:
- Header: `Authorization: Basic base64(username:password)`
- Credentials from URL: `https://user:pass@domain.com/api/events`
- Validated on POST /api/events only

## Real-time Updates (SSE)

**Server Side**:
- Maintains set of asyncio.Queue objects (one per client)
- On new event, pushes to all queues
- Handles client disconnection cleanup
- Sends keepalive every 30s

**Client Side**:
- EventSource connects to `/api/events/stream`
- Receives events via `onmessage`
- Filters events client-side before adding to UI
- Only updates if on page 1

## Frontend Structure

**App.vue** - Single component containing:
- Event table with timestamp, entity, event columns
- Filter inputs (companyId, storeId, entity)
- Pagination controls
- Modal for JSON payload display
- SSE connection management

**State Management**:
- `events` - Current page of events
- `filters` - Active filter values
- `page` - Current page number
- `total` - Total event count
- `pages` - Total page count
- `selectedEvent` - Event for modal display

## Build Process

**Multi-stage Docker build**:
1. Stage 1 (Node): Build Vue frontend to static files
2. Stage 2 (Python): Copy backend + static files, install deps
3. Single image with everything

**Local Development**:
- Frontend: Vite dev server with proxy to backend
- Backend: Uvicorn with auto-reload

## Deployment

**Environment Variables**:
- Set in `.env` file or container environment
- Required: MONGO_URI, AUTH_USER, AUTH_PASS
- Optional: DB_NAME, COLLECTION_NAME

**Container**:
- Exposes port 8000
- Serves both API and frontend
- Connects to external MongoDB

## Performance Considerations

- PyMongo (synchronous MongoDB driver) for simple, reliable operations
- SSE more efficient than WebSockets for one-way push
- Pagination limits memory usage (50 events/page)
- No indexes needed initially (10 events/sec)
- Client-side filtering for real-time updates reduces server load

## Future Enhancements

If needed for scale:
- Add MongoDB indexes on filter fields
- Implement event retention/archival
- Add connection pooling configuration
- Rate limiting on POST endpoint
- Metrics/monitoring endpoints
