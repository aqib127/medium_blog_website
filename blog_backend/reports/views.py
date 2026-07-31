from rest_framework import viewsets, permissions
from .models import Report
from .serializers import ReportSerializer

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own reports; staff can see all
        if self.request.user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(reporter=self.request.user)