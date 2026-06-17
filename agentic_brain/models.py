from django.db import models
from products.models import Product

class AnalysisRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='analyses')
    competitor = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='competitor_analyses')
    ml_sentiments = models.JSONField(default=list)
    competitor_ml_sentiments = models.JSONField(default=list)
    pros = models.JSONField(default=list)
    cons = models.JSONField(default=list)
    final_recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.product.mock_name} at {self.created_at}"
