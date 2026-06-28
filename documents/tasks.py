import logging
import os
import tempfile

from celery import shared_task

from .models import Document

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_document(self, document_id):
    try:
        doc = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        return

    doc.status = 'processing'
    doc.progress = 0
    doc.save(update_fields=['status', 'progress'])

    try:
        file_path = doc.file.path

        if doc.file_type == 'image':
            import cv2
            from .utils.ocr_engine import extract_text
            from .utils.preprocess import preprocess_image
            from .utils.validator import validate_text

            doc.progress = 10
            doc.save(update_fields=['progress'])

            processed = preprocess_image(file_path)

            doc.progress = 40
            doc.save(update_fields=['progress'])

            tmp_fd, tmp_path = tempfile.mkstemp(suffix='.jpg')
            os.close(tmp_fd)
            try:
                cv2.imwrite(tmp_path, processed)
                raw_items = extract_text(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            doc.progress = 80
            doc.save(update_fields=['progress'])

            extracted_text = validate_text(raw_items)
        else:
            from .utils.file_processor import process_file

            doc.progress = 10
            doc.save(update_fields=['progress'])

            extracted_text = process_file(file_path, doc.file_type, doc_id=doc.pk)

        if not extracted_text.strip():
            extracted_text = '[No text could be extracted from this document]'

        doc.extracted_text = extracted_text
        doc.status = 'done'
        doc.progress = 100
        doc.save(update_fields=['extracted_text', 'status', 'progress'])
    except Exception as exc:
        # Log the real error server-side — do NOT expose internal details to users.
        logger.error(
            'OCR processing failed for document %s: %s',
            document_id, exc, exc_info=True,
        )
        doc.extracted_text = '[OCR processing failed. Please try uploading the document again.]'
        doc.status = 'failed'
        doc.progress = 0
        doc.save(update_fields=['extracted_text', 'status', 'progress'])
        raise

