from functools import lru_cache

from google import genai
from google.genai import errors

from django.conf import settings


class GeminiServiceError(Exception):
    default_message = 'Gemini request failed. Please try again.'

    def __init__(self, message=None, status_code=500):
        self.message = message or self.default_message
        self.status_code = status_code
        super().__init__(self.message)


class MissingGeminiApiKey(GeminiServiceError):
    default_message = 'Gemini API key is missing. Add GEMINI_API_KEY to your .env file.'

    def __init__(self):
        super().__init__(self.default_message, status_code=500)


@lru_cache(maxsize=1)
def _client():
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        raise MissingGeminiApiKey()
    return genai.Client(api_key=api_key)


def _generate(prompt):
    try:
        response = _client().models.generate_content(
            model=getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash'),
            contents=prompt,
        )
        text = getattr(response, 'text', '') or ''
        if not text.strip():
            raise GeminiServiceError('Gemini returned an empty response.', 502)
        return text.strip()
    except MissingGeminiApiKey:
        raise
    except errors.APIError as exc:
        message = str(exc)
        lower_message = message.lower()
        if 'api key' in lower_message or 'permission' in lower_message:
            raise GeminiServiceError(
                'Gemini rejected the API key. Check GEMINI_API_KEY in .env.',
                401,
            ) from exc
        if 'quota' in lower_message or 'rate' in lower_message:
            raise GeminiServiceError(
                'Gemini quota or rate limit exceeded. Please try again later.',
                429,
            ) from exc
        raise GeminiServiceError(message, 502) from exc
    except Exception as exc:
        message = str(exc).lower()
        if 'connection' in message or 'network' in message or 'timeout' in message:
            raise GeminiServiceError(
                'Network error while contacting Gemini. Please check your connection.',
                503,
            ) from exc
        raise GeminiServiceError(str(exc), 500) from exc


def _format_history(history):
    if not history:
        return 'No previous messages.'
    lines = []
    for item in history[-12:]:
        role = item.get('role', 'user').title()
        content = item.get('content', '')
        lines.append(f'{role}: {content}')
    return '\n'.join(lines)


def chat_with_document(document_title, extracted_text, question, history=None):
    if not extracted_text or not extracted_text.strip():
        raise GeminiServiceError(
            'This document has no extracted text to chat with.',
            400,
        )

    prompt = f"""
You are an AI assistant for OCR documents.
Answer the user's question using only the DOCUMENT TEXT below.
Do not use outside knowledge.
If the answer is not present in the document, reply exactly:
"I could not find that answer in the selected document."
Keep the answer concise, and cite the relevant wording from the document when useful.

DOCUMENT TITLE:
{document_title}

DOCUMENT TEXT:
\"\"\"
{extracted_text}
\"\"\"

CHAT HISTORY FOR THIS DOCUMENT:
{_format_history(history)}

USER QUESTION:
{question}
"""
    return _generate(prompt)


def summarize_document(document_title, extracted_text, summary_type):
    if not extracted_text or not extracted_text.strip():
        raise GeminiServiceError(
            'This document has no extracted text to summarize.',
            400,
        )

    styles = {
        'short': 'Write a concise 3-5 sentence summary.',
        'detailed': 'Write a detailed structured summary with clear sections.',
        'bullets': 'Write a bullet-point summary using markdown bullets.',
        'takeaways': 'List the key takeaways as short actionable bullets.',
    }
    instruction = styles.get(summary_type, styles['short'])

    prompt = f"""
Summarize the OCR document below using only its text.
Do not add facts that are not present in the document.

DOCUMENT TITLE:
{document_title}

SUMMARY STYLE:
{instruction}

DOCUMENT TEXT:
\"\"\"
{extracted_text}
\"\"\"
"""
    return _generate(prompt)


def general_chat(message, history=None):
    prompt = f"""
You are a helpful AI assistant.

CHAT HISTORY:
{_format_history(history)}

USER MESSAGE:
{message}
"""
    return _generate(prompt)
