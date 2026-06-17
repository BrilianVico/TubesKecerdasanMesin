from django.urls import path
from .views import DashboardView, AnalyzeProductView

app_name = 'agentic_brain'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('analyze/<int:product_id>/', AnalyzeProductView.as_view(), name='analyze_product'),
]
