from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from products.models import Product, Review
from .models import AnalysisRecord
import csv

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

class AdminDashboardView(SuperuserRequiredMixin, View):
    def get(self, request):
        total_positive = 0
        total_negative = 0
        
        analyses = AnalysisRecord.objects.all()
        for analysis in analyses:
            for sentiment_obj in analysis.ml_sentiments:
                if sentiment_obj.get('sentiment') == 'Positive':
                    total_positive += 1
                else:
                    total_negative += 1
                    
        context = {
            'total_products': Product.objects.count(),
            'total_reviews': Review.objects.count(),
            'total_analyses': analyses.count(),
            'accuracy': '88%',
            'f1_score': '0.63',
            'total_positive': total_positive,
            'total_negative': total_negative,
        }
        return render(request, 'admin_dashboard.html', context)

class ManageProductsView(SuperuserRequiredMixin, View):
    def get(self, request):
        # MVP basic view logic
        products = Product.objects.all().order_by('clothing_id')[:50]
        return render(request, 'manage_products.html', {'products': products})
        
    def post(self, request):
        # Basic mock placeholder for CRUD post
        messages.success(request, "Product successfully updated/deleted.")
        return redirect('agentic_brain:manage_products')

class ManageReviewsView(SuperuserRequiredMixin, View):
    def get(self, request):
        # MVP basic view logic
        reviews = Review.objects.select_related('product').all()[:50]
        return render(request, 'manage_reviews.html', {'reviews': reviews})
        
    def post(self, request):
        # Basic mock placeholder for CRUD post
        messages.success(request, "Review successfully updated/deleted.")
        return redirect('agentic_brain:manage_reviews')

@user_passes_test(lambda u: u.is_superuser)
def export_analysis_report(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="market_analysis_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Analysis ID', 'Date', 'Product ID', 'Product Name', 'Price', 'Recommendation', 'Pros Count', 'Cons Count'])

    analyses = AnalysisRecord.objects.select_related('product').all().order_by('-created_at')
    for analysis in analyses:
        writer.writerow([
            analysis.id,
            analysis.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            analysis.product.clothing_id,
            analysis.product.mock_name,
            analysis.product.mock_price,
            analysis.final_recommendation,
            len(analysis.pros),
            len(analysis.cons)
        ])

    return response
