import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from documents.models import Document

from .services.gemini import (
    GeminiServiceError,
    chat_with_document,
    general_chat,
    summarize_document,
)


logger = logging.getLogger(__name__)


MAX_HISTORY_MESSAGES = 30


def _done_documents():
    return Document.objects.filter(
        status='done',
    ).exclude(
        extracted_text='',
    ).order_by('-uploaded_at')


def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return {}


def _history_key(mode, document_id=None):
    if mode == 'document':
        return f'ai_assistant_document_{document_id}'
    return 'ai_assistant_general'


def _get_history(request, mode, document_id=None):
    return request.session.get(_history_key(mode, document_id), [])


def _save_history(request, mode, history, document_id=None):
    request.session[_history_key(mode, document_id)] = history[-MAX_HISTORY_MESSAGES:]
    request.session.modified = True


def _error_response(exc):
    if isinstance(exc, GeminiServiceError):
        return JsonResponse({'error': exc.message}, status=exc.status_code)
    if isinstance(exc, Http404):
        return JsonResponse({'error': 'Document not found.'}, status=404)
    return JsonResponse({'error': 'Unexpected server error.'}, status=500)


@login_required
def assistant_page(request):
    return render(request, 'ai_assistant/assistant.html', {
        'documents': _done_documents(),
    })


@login_required
@require_GET
def history(request):
    mode = request.GET.get('mode', 'general')
    document_id = request.GET.get('document_id')
    if mode == 'document' and not document_id:
        return JsonResponse({'error': 'Select a document first.'}, status=400)
    return JsonResponse({
        'history': _get_history(request, mode, document_id),
    })


@login_required
@require_POST
def chat(request):
    data = _json_body(request)
    mode = data.get('mode', 'general')
    message = (data.get('message') or '').strip()
    document_id = data.get('document_id')

    if not message:
        return JsonResponse({'error': 'Enter a message first.'}, status=400)

    try:
        if mode == 'document':
            if not document_id:
                return JsonResponse({'error': 'Select a document first.'}, status=400)

            doc = get_object_or_404(Document, pk=document_id, status='done')
            conversation_history = _get_history(request, 'document', doc.pk)
            answer = chat_with_document(
                doc.title,
                doc.extracted_text,
                message,
                conversation_history,
            )
            conversation_history.extend([
                {'role': 'user', 'content': message},
                {'role': 'assistant', 'content': answer},
            ])
            _save_history(request, 'document', conversation_history, doc.pk)
        else:
            conversation_history = _get_history(request, 'general')

            docs = _done_documents()[:10]
            documents_list = []
            for d in docs:
                snippet = d.extracted_text[:300]
                if len(d.extracted_text) > 300:
                    snippet += '...'
                documents_list.append(
                    f"Document ID: {d.pk}\n"
                    f"Title: {d.title}\n"
                    f"Uploaded: {d.uploaded_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Content Snippet: {snippet}\n"
                    "---"
                )
            
            answer = general_chat(message, conversation_history, documents_list)
            conversation_history.extend([
                {'role': 'user', 'content': message},
                {'role': 'assistant', 'content': answer},
            ])
            _save_history(request, 'general', conversation_history)

        return JsonResponse({'answer': answer, 'history': conversation_history})
    except (GeminiServiceError, Http404) as exc:
        return _error_response(exc)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid document selection.'}, status=400)
    except Exception as exc:
        logger.exception('Unexpected assistant chat failure.')
        return _error_response(exc)


@login_required
@require_POST
def summarize(request):
    data = _json_body(request)
    document_id = data.get('document_id')
    summary_type = data.get('summary_type', 'short')

    if not document_id:
        return JsonResponse({'error': 'Select a document first.'}, status=400)

    try:
        doc = get_object_or_404(Document, pk=document_id, status='done')
        summary = summarize_document(
            doc.title,
            doc.extracted_text,
            summary_type,
        )
        conversation_history = _get_history(request, 'document', doc.pk)
        conversation_history.extend([
            {'role': 'user', 'content': f'Summarize this document: {summary_type}'},
            {'role': 'assistant', 'content': summary},
        ])
        _save_history(request, 'document', conversation_history, doc.pk)
        return JsonResponse({'summary': summary, 'history': conversation_history})
    except (GeminiServiceError, Http404) as exc:
        return _error_response(exc)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid document selection.'}, status=400)
    except Exception as exc:
        logger.exception('Unexpected assistant summarize failure.')
        return _error_response(exc)


@login_required
@require_POST
def clear_history(request):
    data = _json_body(request)
    mode = data.get('mode', 'general')
    document_id = data.get('document_id')

    if mode == 'document' and not document_id:
        return JsonResponse({'error': 'Select a document first.'}, status=400)

    request.session.pop(_history_key(mode, document_id), None)
    request.session.modified = True
    return JsonResponse({'ok': True})
