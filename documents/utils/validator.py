import re

def validate_text(extracted_items, min_confidence=0.7):
    validated_lines = []
    for item in extracted_items:
        # Skip low-confidence text
        if item['confidence'] < min_confidence:
            continue
        text = item['text'].strip()
        # Remove junk characters, keep letters/numbers/punctuation
        text = re.sub(r'[^\w\s\.\,\-\/\:\(\)\%]', '', text)
        if text:
            validated_lines.append(text)
    return '\n'.join(validated_lines)