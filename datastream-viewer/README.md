# Event Stream Viewer

Real-time event collection and visualization application for data stream integrations.

## Features

- HTTP endpoint to receive events via POST requests
- Real-time UI updates using Server-Sent Events (SSE)
- Pagination (50 events per page)
- Filtering by companyId, storeId, and entity type
- View full JSON payload for each event
- HTTP Basic Authentication
- Single Docker container deployment

## Quick Start

### Using Docker

1. Create `.env` file:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your MongoDB URI and credentials
```

2. Build and run:
```bash
docker build -t datastream-viewer .
docker run -p 8000:8000 --env-file backend/.env datastream-viewer
```

3. Access the UI at `http://localhost:8000`

### Local Development

#### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend dev server runs on `http://localhost:5173` with API proxy to backend.

## Usage

### Sending Events

POST events to the endpoint with Basic Auth:

```bash
curl -X POST https://user:pass@your-domain.com/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "companyId": "comp123",
    "storeId": "store456",
    "entity": "Menu",
    "event": "Updated",
    "payload": {"key": "value"}
  }'
```

### API Endpoints

- `POST /api/events` - Receive events (requires auth)
- `GET /api/events?page=1&companyId=X&storeId=Y&entity=Z` - List events with filters
- `GET /api/events/stream` - SSE stream for real-time updates
- `GET /health` - Health check

## Configuration

Environment variables (backend/.env):

- `MONGO_URI` - MongoDB connection string (default: mongodb://localhost:27017)
- `DB_NAME` - Database name (default: datastream)
- `COLLECTION_NAME` - Collection name (default: events)
- `AUTH_USER` - Basic auth username (default: admin)
- `AUTH_PASS` - Basic auth password (default: admin)

## Data Model

Events are stored with the following structure:

```json
{
  "_id": "ObjectId",
  "companyId": "string",
  "storeId": "string",
  "entity": "string",
  "event": "string",
  "payload": {},
  "timestamp": "ISODate"
}
```

Events are sorted by `_id` in descending order (newest first).

## Production Deployment

1. Set strong credentials in `.env`
2. Use HTTPS/TLS termination (reverse proxy)
3. Configure MongoDB with appropriate retention policies
4. Monitor container logs and MongoDB performance

## Tech Stack

- Backend: FastAPI (Python)
- Frontend: Vue 3 + Vite
- Database: MongoDB
- Real-time: Server-Sent Events (SSE)
