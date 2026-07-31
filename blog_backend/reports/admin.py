from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'target_type', 'target_id', 'status', 'created_at')
    list_filter = ('status', 'target_type')