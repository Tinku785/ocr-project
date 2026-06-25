import os
import csv
import pdfplumber
import pypdfium2 as pdfium  # Already in our requirements.txt!
from docx import Document as DocxDocument
from openpyxl import load_workbook

# Importing our OCR tools from the other files
from .preprocess import preprocess_image
from .ocr_engine import extract_text
from .validator import validate_text
import tempfile
import cv2

def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        return 'image'
    elif ext == '.pdf':
        return 'pdf'
    elif ext == '.docx':
        return 'docx'
    elif ext == '.xlsx':
        return 'xlsx'
    elif ext == '.csv':
        return 'csv'
    return 'unknown'


def extract_from_pdf(file_path):
    text = ''
    
    # 1. Open the PDF with pdfplumber for digital text
    with pdfplumber.open(file_path) as pdf:
        # Open with pypdfium2 in case we need to render scanned pages to images
        pdf_render = pdfium.PdfDocument(file_path)
        
        for page_idx, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            
            # Threshold check: If digital text is missing or extremely short (e.g., less than 10 characters),
            # it is highly likely an image, photo, or scanned page.
            if not page_text or len(page_text.strip()) < 10:
                try:
                    # 2. Render the specific scanned page to a high-res image (300 DPI)
                    pdfium_page = pdf_render[page_idx]
                    bitmap = pdfium_page.render(scale=300/72) # Standard conversion formula to 300 DPI
                    pil_img = bitmap.to_pil()
                    
                    # 3. Save to a temporary image file to feed your OpenCV/PaddleOCR pipeline
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        pil_img.save(tmp.name, format="JPEG")
                        tmp_path = tmp.name
                    
                    # 4. Apply your existing image preprocessing (Denoise, CLAHE, Deskew)
                    processed_img = preprocess_image(tmp_path)
                    
                    # Save preprocessed image back to a temporary file for PaddleOCR
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_proc:
                        cv2.imwrite(tmp_proc.name, processed_img)
                        tmp_proc_path = tmp_proc.name
                        
                    # 5. Extract text via PaddleOCR and validate confidence/characters
                    raw_items = extract_text(tmp_proc_path)
                    ocr_page_text = validate_text(raw_items)
                    
                    # Clean up temporary files
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    if os.path.exists(tmp_proc_path):
                        os.unlink(tmp_proc_path)
                        
                    if ocr_page_text.strip():
                        text += ocr_page_text + '\n'
                    else:
                        text += f"[Scanned Page {page_idx + 1}: No text could be detected via OCR]\n"
                        
                except Exception as ocr_error:
                    text += f"[Error processing page {page_idx + 1} with OCR: {str(ocr_error)}]\n"
            else:
                # Page is a normal digital page, use the extracted text directly
                text += page_text + '\n'
                
        pdf_render.close()
        
    return text.strip()


def extract_from_docx(file_path):
    doc = DocxDocument(file_path)
    lines = []
    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())
    # Also extract tables inside the docx
    for table in doc.tables:
        for row in table.rows:
            row_text = ' | '.join(
                cell.text.strip() for cell in row.cells if cell.text.strip()
            )
            if row_text:
                lines.append(row_text)
    return '\n'.join(lines)


def extract_from_xlsx(file_path):
    wb = load_workbook(file_path, data_only=True)
    lines = []
    for sheet in wb.worksheets:
        lines.append(f'Sheet: {sheet.title}')
        for row in sheet.iter_rows(values_only=True):
            row_text = ' | '.join(
                str(cell) for cell in row if cell is not None
            )
            if row_text.strip():
                lines.append(row_text)
    return '\n'.join(lines)


def extract_from_csv(file_path):
    lines = []
    with open(file_path, newline='', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            row_text = ' | '.join(cell.strip() for cell in row if cell.strip())
            if row_text:
                lines.append(row_text)
    return '\n'.join(lines)


def process_file(file_path, file_type):
    if file_type == 'pdf':
        return extract_from_pdf(file_path)
    elif file_type == 'docx':
        return extract_from_docx(file_path)
    elif file_type == 'xlsx':
        return extract_from_xlsx(file_path)
    elif file_type == 'csv':
        return extract_from_csv(file_path)
    return ''
