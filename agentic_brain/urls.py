from django.urls import path
from .views import DashboardView, AnalyzeProductView
from .admin_views import AdminDashboardView, ManageProductsView, ManageReviewsView, export_analysis_report

app_name = 'agentic_brain'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('analyze/<int:product_id>/', AnalyzeProductView.as_view(), name='analyze_product'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-dashboard/products/', ManageProductsView.as_view(), name='manage_products'),
    path('admin-dashboard/reviews/', ManageReviewsView.as_view(), name='manage_reviews'),
    path('admin-dashboard/export/', export_analysis_report, name='export_analysis_report'),
]
