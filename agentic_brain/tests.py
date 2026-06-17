from django.test import TestCase
from products.models import Product, Review
from agentic_brain.nodes import compare_products
from agentic_brain.state import ProductAnalysisState

class AgenticBrainTestCase(TestCase):
    def setUp(self):
        # Create test products
        self.product1 = Product.objects.create(
            clothing_id=1,
            class_name="Sweaters",
            mock_name="Apparel 1",
            mock_price=50.00
        )
        self.product2 = Product.objects.create(
            clothing_id=2,
            class_name="Sweaters",
            mock_name="Apparel 2",
            mock_price=60.00
        )
        
        # Create reviews for product1
        Review.objects.create(
            product=self.product1,
            age=30,
            title="Good",
            review_text="Very good sweater",
            rating=5,
            recommended_ind=True,
            positive_feedback_count=0
        )
        Review.objects.create(
            product=self.product1,
            age=35,
            title="Okay",
            review_text="Just okay",
            rating=3,
            recommended_ind=True,
            positive_feedback_count=0
        )

        # Create reviews for product2
        Review.objects.create(
            product=self.product2,
            age=40,
            title="Excellent",
            review_text="Excellent competitor sweater",
            rating=4,
            recommended_ind=True,
            positive_feedback_count=0
        )

    def test_product_rating_property(self):
        # Product 1 should have average rating of (5+3)/2 = 4.0
        self.assertEqual(self.product1.rating, 4.0)
        # Product 2 should have average rating of 4.0
        self.assertEqual(self.product2.rating, 4.0)

    def test_compare_products_node(self):
        state = ProductAnalysisState(
            product_id=self.product1.clothing_id,
            raw_reviews=[],
            ml_sentiments=[],
            competitor_data={},
            competitor_raw_reviews=[],
            competitor_ml_sentiments=[],
            product_insights={},
            final_recommendation=""
        )
        # Call the compare_products node
        result = compare_products(state)
        self.assertIn("competitor_data", result)
        self.assertEqual(result["competitor_data"]["id"], self.product2.clothing_id)
        self.assertEqual(result["competitor_data"]["rating"], 4.0)

    def test_analyze_product_view_saves_record(self):
        from unittest.mock import patch
        from agentic_brain.models import AnalysisRecord
        
        # Mocking the graph stream to simulate output of each node
        mock_stream_data = [
            {"collect_reviews": {"raw_reviews": ["good product"]}},
            {"analyze_sentiment": {"ml_sentiments": [{"text": "good product", "sentiment": "Positive", "confidence": 0.99}]}},
            {"compare_products": {
                "competitor_data": {"id": self.product2.clothing_id, "name": "Apparel 2", "price": "60.00", "rating": 4.0},
                "competitor_raw_reviews": ["Excellent competitor sweater"],
                "competitor_ml_sentiments": [{"text": "Excellent competitor sweater", "sentiment": "Positive", "confidence": 0.98}]
            }},
            {"generate_insights": {"product_insights": {"pros": ["Fits well"], "cons": ["None"]}}},
            {"make_decision": {"final_recommendation": "Buy product 1"}}
        ]
        
        with patch("agentic_brain.views.agentic_brain_graph.stream", return_value=mock_stream_data):
            from django.test import RequestFactory
            from agentic_brain.views import AnalyzeProductView
            
            factory = RequestFactory()
            request = factory.get(f"/analyze/{self.product1.clothing_id}/?ajax=true", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            
            view = AnalyzeProductView.as_view()
            response = view(request, product_id=self.product1.clothing_id)
            
            # Consume the streaming content to trigger record creation
            content = b"".join(response.streaming_content).decode("utf-8")
            
            # Check if record is created successfully in DB without raising DB error
            self.assertEqual(AnalysisRecord.objects.count(), 1)
            record = AnalysisRecord.objects.first()
            self.assertEqual(record.product_id, self.product1.clothing_id)
            self.assertEqual(record.competitor_id, self.product2.clothing_id)
            self.assertEqual(record.pros, ["Fits well"])
            self.assertEqual(record.cons, ["None"])
            self.assertEqual(record.final_recommendation, "Buy product 1")

