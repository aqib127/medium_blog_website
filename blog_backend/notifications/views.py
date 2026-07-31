from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.read_at = request.data.get('read_at') or timezone.now()
        notification.save(update_fields=['read_at'])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['put'])
    def read_all(self, request):
        count = self.get_queryset().filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response({'marked_read': count})