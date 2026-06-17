from django.core.management.base import BaseCommand
from ml_engine.services import SentimentInferenceService

class Command(BaseCommand):
    help = 'Tests the SentimentInferenceService with dummy reviews.'

    def handle(self, *args, **options):
        # Initialize the singleton service
        service = SentimentInferenceService()
        
        # Define test strings simulating user reviews
        test_reviews = [
            "The material is wonderful, fits perfectly and looks elegant!",
            "Terrible quality, the stitching came undone after one wash and it's completely unwearable.",
            "It's okay, nothing special but serves its purpose well enough.",
            "I absolutely love this dress! The color is so vibrant and I got many compliments."
        ]

        self.stdout.write(self.style.SUCCESS("--- Testing ML Sentiment Inference ---"))

        for idx, text in enumerate(test_reviews, 1):
            result = service.predict_sentiment(text)
            
            # Formatting the output nicely
            self.stdout.write(f"\nTest Case #{idx}:")
            self.stdout.write(f"Input Text   : {text}")
            
            # Color code the sentiment output
            sentiment = result.get('sentiment')
            if sentiment == 'Positive':
                sentiment_display = self.style.SUCCESS(sentiment)
            elif sentiment == 'Negative':
                sentiment_display = self.style.ERROR(sentiment)
            else:
                sentiment_display = self.style.WARNING(sentiment)
                
            self.stdout.write(f"Predicted    : {sentiment_display}")
            self.stdout.write(f"Confidence   : {result.get('confidence', 0.0):.4f}")
            
        self.stdout.write(self.style.SUCCESS("\n--- Inference Test Complete ---"))
