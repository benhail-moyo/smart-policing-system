# Smart Policing System - Agent Configuration

## Project Overview
This is a community-focused smart policing system with NLP-powered incident triage for Zimbabwe, supporting English, Shona, and Ndebele languages.

## Project Structure
- **Backend**: Flask-based API with NLP triage service using Google Gemini API
- **Frontend**: Next.js React application for community incident reporting
- **Database**: PostgreSQL with PostGIS for geospatial data
- **ML Components**: NLP triage, routing algorithms, hotspot analysis

## Key Configuration Files

### Environment Setup
- `.env` - Root environment file for Gemini API key
- `.env.backend` - Backend-specific environment variables
- `.env.example` - Template for environment variables
- `docker-compose.yml` - Docker orchestration

### Important: Gemini API Key Setup
The NLP triage engine requires a Google Gemini API key to function properly. Without it, the system falls back to keyword-based classification.

**To enable full NLP triage:**
1. Get API key from: https://makersuite.google.com/app/apikey
2. Add to `.env` file: `GEMINI_API_KEY=your_actual_api_key`
3. Docker Compose will automatically load this variable

## Build and Run Commands

### Using Docker Compose (Recommended)
```bash
docker-compose up --build
```

### Backend Only
```bash
cd backend
pip install -r requirements.txt
python init_db.py
flask run
```

### Frontend Only
```bash
cd frontend
npm install
npm run dev
```

## NLP Triage System

### How It Works
1. User submits incident description
2. Language detection (English, Shona, Ndebele)
3. Keyword pre-scan for HIGH severity signals
4. Gemini API classification (if API key available)
5. Keyword override if LLM misses HIGH severity
6. Confidence threshold check
7. Returns structured triage result

### Fallback Behavior
- If Gemini API key is missing or API fails, system uses keyword-based classification
- Keyword fallback is conservative (prefers false negatives over false positives)
- Supports multi-language keywords for Zimbabwe context

### Severity Levels
- **HIGH**: Weapons, assault in progress, murder, rape, immediate threats
- **MEDIUM**: Property crime, drug activity, fraud, past assault
- **LOW**: Suspicious behavior, noise complaints, minor disputes

## API Endpoints

### Incident Reporting
- `POST /api/v1/incidents/` - Submit incident (auto-triaged)
- `GET /api/v1/incidents/` - List incidents (filtered by user role)
- `GET /api/v1/incidents/<id>` - Get single incident
- `GET /api/v1/incidents/stats` - Dashboard statistics

### Other Services
- Authentication: `/api/v1/auth/`
- Patrol management: `/api/v1/patrol/`
- Hotspot analysis: `/api/v1/hotspots/`
- Command center: `/api/v1/command/`

## Recent Changes (August 2026)

### UI Updates
- Removed manual severity selection from community report form
- Separated date and time input fields for better UX
- Severity now automatically determined by NLP engine

### Backend Updates
- Modified incident creation to always use NLP triage severity
- Removed override capability for manual severity input
- Enhanced Gemini API key configuration in docker-compose

### Configuration Updates
- Added GEMINI_API_KEY to environment configuration
- Updated docker-compose.yml to load API key from environment
- Added comprehensive comments in .env files for setup guidance

## Testing
Integration tests are available in `backend/tests/` directory.

## Security Notes
- Never commit actual API keys to repository
- Use environment variables for sensitive configuration
- JWT authentication required for most endpoints
- Community users can only see their own incidents
