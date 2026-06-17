from django.urls import path
from . import views

app_name = 'agentic_brain'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('analyze/<int:product_id>/', views.AnalyzeProductView.as_view(), name='analyze_product'),
]
