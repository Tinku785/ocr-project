# Intelligent Document Processing and OCR Automation System

An OCR-based document processing system built for IOCL (Indian Oil Corporation Limited) internship project.

## Features
- Upload documents via web interface (Image, PDF, DOCX, XLSX, CSV)
- Image preprocessing using OpenCV (noise reduction, deskewing, thresholding, contrast enhancement)
- Text extraction using PaddleOCR
- Data validation using confidence checks and Regex
- Store extracted text in MySQL database
- Background OCR processing with Celery
- AI Assistant with Google Gemini for document chat, summaries, and general chat
- Search and retrieve documents

## Tech Stack
- Python 3.11
- Django
- OpenCV
- PaddleOCR
- MySQL
- Celery + Redis
- Google Gemini API (`google-genai`)
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
Add your free Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

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
Start Redis first. If you have Docker:
```bash
docker run --name ocr-redis -p 6379:6379 -d redis:7
```

In one terminal, start the Celery worker:
```bash
venv\Scripts\activate
celery -A ocr_project worker --loglevel=info --pool=solo
```

In another terminal, start Django:
```bash
python manage.py runserver
```

Open browser at `http://127.0.0.1:8000/`
Open the AI Assistant at `http://127.0.0.1:8000/ai/`

Uploaded documents are saved immediately with `Pending` status. The Celery
worker changes them to `Processing`, then `Done` or `Failed` after OCR
finishes. If the worker is not running, new uploads will remain `Pending`.

## AI Assistant
- Chat with Document: select a processed OCR document and ask questions from its extracted text only.
- Summarize Document: generate short, detailed, bullet-point, or key takeaway summaries.
- General AI Chat: use Gemini without document context.
- Chat history is stored in the Django session and separated per document.

If Gemini returns an authentication, quota, empty-document, or network error,
the UI shows a user-friendly message without affecting OCR features.

## Supported File Types
| Format | Description |
|--------|-------------|
| JPG, PNG | Scanned document images |
| PDF | Digital and scanned PDFs |
| DOCX | Microsoft Word documents |
| XLSX | Microsoft Excel spreadsheets |
| CSV | Comma separated data files |
