from django.contrib import admin
from django.utils.html import format_html
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    # columns shown in the document list
    list_display = ['id', 'title', 'file_type_badge', 'status_badge',
                    'uploaded_at', 'text_preview', 'file_link']

    # filters on the right sidebar
    list_filter = ['file_type', 'status', 'uploaded_at']

    # search bar at the top
    search_fields = ['title', 'extracted_text']

    # fields that cannot be edited
    readonly_fields = ['uploaded_at', 'file_type', 'status',
                       'extracted_text', 'file_preview']

    # order by latest first
    ordering = ['-uploaded_at']

    # how many documents per page
    list_per_page = 20

    # field layout inside each document
    fieldsets = (
        ('Document Info', {
            'fields': ('title', 'file_type', 'status', 'uploaded_at')
        }),
        ('File', {
            'fields': ('file', 'file_preview')
        }),
        ('Extracted Text', {
            'fields': ('extracted_text',)
        }),
    )

    # colored file type badge
    def file_type_badge(self, obj):
        colors = {
            'pdf':   '#dc3545',
            'image': '#ffc107',
            'docx':  '#0d6efd',
            'xlsx':  '#198754',
            'csv':   '#6c757d',
        }
        color = colors.get(obj.file_type, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color, obj.file_type.upper()
        )
    file_type_badge.short_description = 'Type'

    # colored status badge
    def status_badge(self, obj):
        colors = {
            'done':       '#198754',
            'processing': '#0dcaf0',
            'pending':    '#6c757d',
            'failed':     '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    # short preview of extracted text
    def text_preview(self, obj):
        if obj.extracted_text:
            return obj.extracted_text[:60] + '...' if len(obj.extracted_text) > 60 else obj.extracted_text
        return '—'
    text_preview.short_description = 'Text Preview'

    # clickable link to original file
    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download</a>',
                obj.file.url
            )
        return '—'
    file_link.short_description = 'File'

    # image preview inside document detail
    def file_preview(self, obj):
        if obj.file and obj.file_type == 'image':
            return format_html(
                '<img src="{}" style="max-height:300px;max-width:100%;">',
                obj.file.url
            )
        elif obj.file:
            return format_html(
                '<a href="{}" target="_blank">Open File</a>',
                obj.file.url
            )
        return '—'
    file_preview.short_description = 'Preview'