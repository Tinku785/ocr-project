# Intelligent Document Processing and OCR Automation System

An OCR-based document processing system built for IOCL (Indian Oil Corporation Limited) internship project.

## Team Members
- Gyan Ankur Das
- Jyotirmoy Das
- Bitopan Sarmah
- Tinku Moni Kaushik
- Baidurjya Bharadwaz
- Priyam Basistha

## Features
- Upload documents via web interface (Image, PDF, DOCX, XLSX, CSV)
- Image preprocessing using OpenCV (noise reduction, deskewing, thresholding, contrast enhancement)
- Text extraction using PaddleOCR
- Data validation using confidence checks and Regex
- Store extracted text in MySQL database
- Search and retrieve documents

## Tech Stack
- Python 3.11
- Django
- OpenCV
- PaddleOCR
- MySQL
- Bootstrap 5

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/GyanAnkurDas/ocr-project.git
cd ocr-project
```

### 2. Create virtual environment
```bash
py -3.11 -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
copy .env.example .env
```
Open `.env` and fill in your MySQL password.

### 5. Create MySQL database
Open MySQL and run:
```sql
CREATE DATABASE ocr_db;
```

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Start the server
```bash
python manage.py runserver
```

Open browser at `http://127.0.0.1:8000/`

## Supported File Types
| Format | Description |
|--------|-------------|
| JPG, PNG | Scanned document images |
| PDF | Digital and scanned PDFs |
| DOCX | Microsoft Word documents |
| XLSX | Microsoft Excel spreadsheets |
| CSV | Comma separated data files |