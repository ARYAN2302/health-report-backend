import os
import models
import schemas
import database
import auth
import utils
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
import requests

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

COHERE_API_KEY = os.environ.get("COHERE_API_KEY")

origins = [
    os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000"),
    "http://127.0.0.1:3000"
]
if os.environ.get("VERCEL_URL"):
    origins.append(f"https://{os.environ['VERCEL_URL']}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=database.engine)

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = auth.get_user(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload_report", response_model=schemas.Report)
def upload_report(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    filename = utils.secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    utils.save_upload_file(file, file_path)
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        text = utils.extract_text_from_image(file_path)
    elif filename.lower().endswith('.pdf'):
        text = utils.extract_text_from_pdf(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    parameters = utils.parse_parameters(text)
    report = models.Report(filename=filename, user_id=current_user.id, extracted_text=text)
    db.add(report)
    db.commit()
    db.refresh(report)
    for param in parameters:
        db_param = models.Parameter(report_id=report.id, **param)
        db.add(db_param)
    db.commit()
    db.refresh(report)
    return report

@app.get("/reports", response_model=List[schemas.Report])
def get_reports(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    reports = db.query(models.Report).filter(models.Report.user_id == current_user.id).order_by(models.Report.upload_time.desc()).all()
    return reports

@app.get("/report/{report_id}", response_model=schemas.Report)
def get_report(report_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    report = db.query(models.Report).filter(models.Report.id == report_id, models.Report.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@app.post("/analyze")
def analyze(parameters: list = Body(...)):
    prompt = "Give a brief, plain-English health insight for these lab results:\n"
    for p in parameters:
        prompt += f"{p['name']}: {p['value']} {p.get('unit', '')} (ref: {p.get('reference_range', 'N/A')})\n"
    response = requests.post(
        "https://api.cohere.ai/v1/generate",
        headers={
            "Authorization": f"Bearer {COHERE_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "command",
            "prompt": prompt,
            "max_tokens": 100,
            "temperature": 0.5
        }
    )
    result = response.json()
    return {"insight": result.get("generations", [{}])[0].get("text", "No insight generated.")} 