from rest_framework import viewsets, permissions
from .models import ReadingHistory
from .serializers import ReadingHistorySerializer

class ReadingHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReadingHistory.objects.filter(user=self.request.user).order_by('-last_read_at')

    def perform_create(self, serializer):
        serializer.save()