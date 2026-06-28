from .utils.file_processor import get_file_type
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count
from django.db import transaction
from .models import Document
from .tasks import process_document

import os


@login_required
def upload_document(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        title = request.POST.get('title', 'Untitled').strip()

        if not uploaded_file:
            return render(request, 'documents/upload.html',
                        {'error': 'Please select a file.'})

        if uploaded_file.size > 20 * 1024 * 1024:
            return render(request, 'documents/upload.html',
                        {'error': 'File too large. Maximum is 20MB.'})

        file_type = get_file_type(uploaded_file.name)
        if file_type == 'unknown':
            return render(request, 'documents/upload.html',
                        {'error': 'Unsupported file type.'})

        doc = None
        try:
            doc = Document(title=title, file=uploaded_file,
                        file_type=file_type, status='pending')
            doc.save()

            transaction.on_commit(lambda: process_document.delay(doc.pk))
            messages.success(
                request,
                'Document uploaded. OCR processing will continue in the background.'
            )
            return redirect('document_detail', pk=doc.pk)

        except Exception as e:
            try:
                if doc and doc.pk:
                    if doc.file and os.path.exists(doc.file.path):
                        os.remove(doc.file.path)
                    doc.delete()
            except:
                pass
            return render(request, 'documents/upload.html', {
                'error': f'Error: {str(e)}'
            })

    return render(request, 'documents/upload.html')


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    return render(request, 'documents/detail.html', {'doc': doc})


@login_required
def search_documents(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = Document.objects.filter(
            extracted_text__icontains=query
        ).order_by('-uploaded_at')
    return render(request, 'documents/search.html', {
        'results': results,
        'query': query
    })


@login_required
def delete_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        # Delete the actual file from disk too
        if doc.file and os.path.exists(doc.file.path):
            os.remove(doc.file.path)
        doc.delete()
        return redirect('upload_document')
    return render(request, 'documents/confirm_delete.html', {'doc': doc})


@login_required
def edit_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        doc.title = request.POST.get('title', doc.title)
        doc.save()
        return redirect('document_detail', pk=doc.pk)
    return render(request, 'documents/edit.html', {'doc': doc})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'documents/login.html',
                          {'error': 'Invalid username or password.'})
    return render(request, 'documents/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    total_docs = Document.objects.count()

    doc_type = request.GET.get('type')

    if doc_type == 'word':
        recent_docs = Document.objects.filter(file_type='docx').order_by('-uploaded_at')[:50]
    elif doc_type == 'excel_csv':
        recent_docs = Document.objects.filter(file_type__in=['xlsx', 'csv']).order_by('-uploaded_at')[:50]
    elif doc_type:
        recent_docs = Document.objects.filter(file_type=doc_type).order_by('-uploaded_at')[:50]
    else:
        recent_docs = Document.objects.order_by('-uploaded_at')[:50]

    type_counts = Document.objects.values('file_type').annotate(count=Count('file_type'))
    type_data = {item['file_type']: item['count'] for item in type_counts}

    word_count = type_data.get('docx', 0)
    excel_csv_count = type_data.get('xlsx', 0) + type_data.get('csv', 0)

    return render(request, 'documents/dashboard.html', {
        'total_docs': total_docs,
        'recent_docs': recent_docs,
        'type_data': type_data,
        'word_count': word_count,
        'excel_csv_count': excel_csv_count,
    })


@login_required
def export_txt(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    response = HttpResponse(doc.extracted_text, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{doc.title}.txt"'
    return response


@login_required
def export_pdf(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    try:
        import io
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import simpleSplit

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        y = height - 40
        for line in doc.extracted_text.split('\n'):
            lines = simpleSplit(line, 'Helvetica', 12, width - 80)
            for l in lines:
                p.drawString(40, y, l)
                y -= 15
                if y < 40:
                    p.showPage()
                    p.setFont('Helvetica', 12)
                    y = height - 40
        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{doc.title}.pdf"'
        return response
    except ImportError:
        return HttpResponse("PDF export requires 'reportlab' to be installed.", status=501)


@login_required
def retry_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if doc.status in ['failed', 'done']:
        doc.status = 'pending'
        doc.progress = 0
        doc.extracted_text = ''
        doc.save(update_fields=['status', 'progress', 'extracted_text'])
        transaction.on_commit(lambda: process_document.delay(doc.pk))
        messages.success(request, 'Document reprocessing has started.')
    else:
        messages.warning(request, 'Document is already being processed.')
    return redirect('document_detail', pk=doc.pk)
