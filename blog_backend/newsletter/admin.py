from django.contrib import admin
from .models import NewsletterSubscriber, NewsletterSendLog


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_confirmed', 'is_active', 'confirmed_at', 'created_at')
    list_filter = ('is_confirmed', 'is_active', 'source')
    search_fields = ('email', 'name')
    readonly_fields = ('unsubscribe_token', 'confirmed_at', 'unsubscribed_at', 'last_email_sent_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False  # Prevent manual creation


@admin.register(NewsletterSendLog)
class NewsletterSendLogAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sent_to_count', 'failed_count', 'status', 'sent_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        return False
