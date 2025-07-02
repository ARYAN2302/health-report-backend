# Health Lab Report Backend

This is the FastAPI backend for the Health Lab Report Dashboard project.

## Features
- User authentication (JWT)
- File upload (PDF/image) with OCR and parameter extraction
- SQLite database for user data and reports
- AI health insights using Cohere API
- CORS and environment variable support for production

## Deployment
- Recommended: Deploy on [Render.com](https://render.com/)
- Set environment variables:
  - `COHERE_API_KEY` (your Cohere API key)
  - `FRONTEND_ORIGIN` (your frontend URL, e.g. https://your-frontend.vercel.app)
  - `VERCEL_URL` (your Vercel domain, e.g. your-frontend.vercel.app)
- Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`

## Local Development
- Install dependencies: `pip install -r requirements.txt`
- Run: `uvicorn main:app --reload`

## API Endpoints
- `/register` - Register a new user
- `/login` - Login and get JWT
- `/upload_report` - Upload a health report
- `/reports` - List user reports
- `/report/{id}` - Get report details
- `/analyze` - Get AI health insight

---

For more details, see the frontend repo or contact the maintainer. 