# MLTC Enumerator

A full-stack application with Next.js frontend and FastAPI backend.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)

### Running the Application

#### Production Mode
```bash
./start.sh
```

#### Development Mode (with hot reloading)

Option 1 - Run from project root (recommended):
```bash
./start-dev.sh
```

Option 2 - Run from frontend directory:
```bash
cd frontend
./start-dev.sh
```

Both options will start both the frontend and backend services with hot reloading.

### Services

- **Frontend**: Next.js application running on [http://localhost:3000](http://localhost:3000)
- **Backend**: FastAPI application running on [http://localhost:8000](http://localhost:8000)
- **API Documentation**: Available at [http://localhost:8000](http://localhost:8000)

### API Routing

The frontend is configured to automatically route any requests to `/api/*` to the backend service running on port 8000. This allows you to make API calls from your frontend code like:

```javascript
// This will be routed to http://localhost:8000/ping
fetch('/api/ping')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Development

### Project Structure
```
├── frontend/          # Next.js frontend application
├── backend/           # FastAPI backend application
├── docker-compose.yml # Production docker compose
├── docker-compose.dev.yml # Development docker compose
├── start.sh          # Production start script
└── start-dev.sh      # Development start script
```

### Manual Development Setup

If you prefer to run the services manually without Docker:

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker Commands

#### Stop all services
```bash
docker-compose down
```

#### View logs
```bash
docker-compose logs -f
```

#### Rebuild services
```bash
docker-compose up --build
```

## Environment Configuration

### Production
- Frontend runs in production mode with optimized builds
- Backend runs with standard uvicorn server

### Development
- Frontend runs with hot reloading enabled
- Backend runs with `--reload` flag for automatic restarts
- Code changes are reflected immediately without rebuilding containers 

## System Description
This is the general outline of how the system works.

On the backend, there are three main endpoints.

- `/context` - The context endpoints generates preliminary attacker profiles, entrypoints, and assets in the system based on the textual description of the DFD. Further, it the user can provide "hints" to the system in order to guide the initial enumeration.
- `/generate` - After the user verifies the initial enumeration by editing existing descriptions, removing irrelevant ones, and adding important aspects that the initial enumeration missed, they send the updated context to the generate endpoint.
- `/iterate` - This will be a separate prompting system that uses Tree-of-Thought (ToT) prompting methods to send back potential iterations to the user interface where the user can then choose which modifications seem most likely to improve the system and then the user can choose to continue the iteration process.

On the frontend the user accomplishes the manual modifications described above.