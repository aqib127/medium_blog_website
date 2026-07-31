from django.contrib import admin
from .models import ReadingHistory

@admin.register(ReadingHistory)
class ReadingHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'last_read_at', 'read_count')