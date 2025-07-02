import os
import pytesseract
from PIL import Image
import pdfplumber
from werkzeug.utils import secure_filename
import re

# List of common health parameters to extract - more specific and smaller list
COMMON_PARAMETERS = [
    "Hemoglobin", "WBC", "RBC", "Platelet Count", "Hematocrit",
    "MCV", "MCH", "MCHC", "RDW", "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils",
    "Glucose", "HbA1c", "Total Cholesterol", "HDL Cholesterol", "LDL Cholesterol", "Triglycerides",
    "Urea", "Creatinine", "Uric Acid", "Sodium", "Potassium", "Chloride", "Calcium", "Phosphorus",
    "Bilirubin", "SGOT", "SGPT", "ALP", "GGT", "Total Protein", "Albumin", "TSH", "T3", "T4"
]

# Demographic fields to ignore
IGNORE_FIELDS = ["Name", "Patient Name", "Age", "Sex", "Gender", "Patient ID", "ID", "Date", "Reference", "Doctor", "Physician", "Lab", "Report", "Address", "Phone", "Email"]

PARAMETER_UNITS = {
    "Hemoglobin": "g/dL",
    "WBC": "10^3/µL",
    "RBC": "10^6/µL",
    "Platelet Count": "10^3/µL",
    "Hematocrit": "%",
    "MCV": "fL",
    "MCH": "pg",
    "MCHC": "g/dL",
    "RDW": "%",
    "Neutrophils": "%",
    "Lymphocytes": "%",
    "Monocytes": "%",
    "Eosinophils": "%",
    "Basophils": "%",
    "Glucose": "mg/dL",
    "HbA1c": "%",
    "Total Cholesterol": "mg/dL",
    "HDL Cholesterol": "mg/dL",
    "LDL Cholesterol": "mg/dL",
    "Triglycerides": "mg/dL",
    "Urea": "mg/dL",
    "Creatinine": "mg/dL",
    "Uric Acid": "mg/dL",
    "Sodium": "mmol/L",
    "Potassium": "mmol/L",
    "Chloride": "mmol/L",
    "Calcium": "mg/dL",
    "Phosphorus": "mg/dL",
    "Bilirubin": "mg/dL",
    "SGOT": "U/L",
    "SGPT": "U/L",
    "ALP": "U/L",
    "GGT": "U/L",
    "Total Protein": "g/dL",
    "Albumin": "g/dL",
    "TSH": "µIU/mL",
    "T3": "ng/dL",
    "T4": "µg/dL"
}

def normalize(s):
    return ' '.join(s.strip().lower().split())

NORMALIZED_PARAMETERS = set(normalize(p) for p in COMMON_PARAMETERS)
NORMALIZED_IGNORES = set(normalize(f) for f in IGNORE_FIELDS)

def save_upload_file(upload_file, destination):
    with open(destination, "wb") as buffer:
        buffer.write(upload_file.file.read())

def extract_text_from_image(file_path):
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return text

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    if not text:
        # fallback to OCR if no text layer
        from pdf2image import convert_from_path
        pages = convert_from_path(file_path)
        for page in pages:
            text += pytesseract.image_to_string(page)
    return text

def parse_parameters(text):
    print(f"DEBUG: Extracted text length: {len(text)}")
    print(f"DEBUG: First 500 chars: {text[:500]}")
    
    pattern = re.compile(r'([A-Za-z\s]+?)\s+(\d+(?:\.\d+)?)\s*([a-zA-Z/%μµ]*)\s*(?:\(?([\d.\-–/<> ]+)\)?)?')
    parameters = []
    matches_found = 0
    sorted_params = sorted(COMMON_PARAMETERS, key=len, reverse=True)
    for match in pattern.finditer(text):
        matches_found += 1
        name, value, unit, ref = match.groups()
        name_clean = ' '.join(name.strip().split())
        name_norm = normalize(name_clean)
        if name_norm in NORMALIZED_IGNORES:
            continue
        found_parameter = None
        for param in sorted_params:
            if param.lower() in name_norm:
                found_parameter = param
                break
        if found_parameter:
            # Flag abnormal values
            status = "unknown"
            try:
                val = float(value)
                if ref:
                    # Try to parse reference range like '13.5-17.5' or '< 200' or '> 40'
                    ref_clean = ref.replace('–', '-').replace('<', '').replace('>', '').strip()
                    if '-' in ref_clean:
                        low, high = [float(x) for x in ref_clean.split('-') if x.strip()]
                        if val < low:
                            status = "low"
                        elif val > high:
                            status = "high"
                        else:
                            status = "normal"
                    elif ref.strip().startswith('<'):
                        if val < float(ref_clean):
                            status = "normal"
                        else:
                            status = "high"
                    elif ref.strip().startswith('>'):
                        if val > float(ref_clean):
                            status = "normal"
                        else:
                            status = "low"
            except Exception:
                pass
            parameters.append({
                "name": found_parameter,
                "value": value.strip(),
                "unit": (unit.strip() if unit else PARAMETER_UNITS.get(found_parameter)),
                "reference_range": ref.strip() if ref else None,
                "status": status
            })
    return parameters 