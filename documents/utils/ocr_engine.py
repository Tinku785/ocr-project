import os
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"

from paddleocr import PaddleOCR

# Initialize once (downloading models on first run — takes time)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_text(image_path):
    result = ocr.ocr(image_path)
    extracted = []
    if not result or not result[0]:
        return extracted
        
    if isinstance(result[0], dict) and 'rec_texts' in result[0]:
        texts = result[0]['rec_texts']
        scores = result[0]['rec_scores']
        for text, conf in zip(texts, scores):
            extracted.append({
                'text': text,
                'confidence': conf
            })
    else:
        for line in result[0]:
            text = line[1][0]
            confidence = line[1][1]
            extracted.append({
                'text': text,
                'confidence': confidence
            })
    return extracted