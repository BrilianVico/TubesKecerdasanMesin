from django.db import models
import random

class Product(models.Model):
    clothing_id = models.IntegerField(primary_key=True)
    division_name = models.CharField(max_length=255, null=True, blank=True)
    department_name = models.CharField(max_length=255, null=True, blank=True)
    class_name = models.CharField(max_length=255, null=True, blank=True)
    mock_name = models.CharField(max_length=255)
    mock_price = models.DecimalField(max_digits=6, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.mock_name:
            self.mock_name = f"Apparel {self.clothing_id} - {self.class_name or 'General'}"
        if not self.mock_price:
            self.mock_price = round(random.uniform(15.00, 120.00), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.mock_name

    @property
    def rating(self):
        from django.db.models import Avg
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 1) if avg_rating is not None else 0.0


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    age = models.PositiveIntegerField()
    title = models.CharField(max_length=255, null=True, blank=True)
    review_text = models.TextField()
    cleaned_review_text = models.TextField(blank=True, null=True)
    rating = models.IntegerField()
    recommended_ind = models.BooleanField()
    positive_feedback_count = models.PositiveIntegerField()

    def __str__(self):
        return f"Review for {self.product.mock_name} - {self.rating} Stars"
