import os
import random
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Product, Review

class Command(BaseCommand):
    help = 'Loads Womens E-Commerce Clothing Reviews dataset into the database with NLP preprocessing'

    def preprocess_text(self, text, stop_words, stemmer):
        if pd.isna(text):
            return ""
        # Lowercase
        text = str(text).lower()
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords and non-alphabetic tokens, then stem
        cleaned_tokens = [
            stemmer.stem(token) for token in tokens
            if token.isalpha() and token not in stop_words
        ]
        return " ".join(cleaned_tokens)

    def handle(self, *args, **options):
        # Ensure NLTK data is downloaded
        self.stdout.write('Downloading NLTK resources...')
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        nltk.download('stopwords', quiet=True)
        
        stop_words = set(stopwords.words('english'))
        stemmer = PorterStemmer()

        # 1. Extract
        file_path = os.path.join(settings.BASE_DIR, 'data', 'raw', 'Womens Clothing E-Commerce Reviews.csv')
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Dataset not found at {file_path}'))
            return
            
        self.stdout.write('Loading dataset...')
        df = pd.read_csv(file_path, index_col=0)

        # 2. Transform
        initial_len = len(df)
        df = df.dropna(subset=['Review Text'])
        self.stdout.write(f'Dropped {initial_len - len(df)} rows missing Review Text.')

        self.stdout.write('Applying NLP preprocessing to Review Text...')
        df['Cleaned Review Text'] = df['Review Text'].apply(
            lambda x: self.preprocess_text(x, stop_words, stemmer)
        )

        # Extract unique products
        # 'Clothing ID', 'Division Name', 'Department Name', 'Class Name'
        unique_products = df[['Clothing ID', 'Division Name', 'Department Name', 'Class Name']].drop_duplicates(subset=['Clothing ID'])
        
        products_to_create = []
        for _, row in unique_products.iterrows():
            clothing_id = row['Clothing ID']
            class_name = str(row['Class Name']) if pd.notna(row['Class Name']) else 'General'
            mock_name = f"Apparel {clothing_id} - {class_name}"
            mock_price = round(random.uniform(15.00, 120.00), 2)
            
            product = Product(
                clothing_id=clothing_id,
                division_name=row['Division Name'] if pd.notna(row['Division Name']) else None,
                department_name=row['Department Name'] if pd.notna(row['Department Name']) else None,
                class_name=row['Class Name'] if pd.notna(row['Class Name']) else None,
                mock_name=mock_name,
                mock_price=mock_price
            )
            products_to_create.append(product)

        # 3. Load Products
        self.stdout.write('Inserting products...')
        Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(products_to_create)} products.'))

        # Retrieve product dictionary for fast lookup
        product_dict = {p.clothing_id: p for p in Product.objects.all()}

        # Transform and Load Reviews
        self.stdout.write('Preparing reviews...')
        reviews_to_create = []
        for _, row in df.iterrows():
            product = product_dict.get(row['Clothing ID'])
            if not product:
                continue
                
            review = Review(
                product=product,
                age=row['Age'],
                title=row['Title'] if pd.notna(row['Title']) else None,
                review_text=row['Review Text'],
                cleaned_review_text=row['Cleaned Review Text'],
                rating=row['Rating'],
                recommended_ind=bool(row['Recommended IND']),
                positive_feedback_count=row['Positive Feedback Count']
            )
            reviews_to_create.append(review)

        self.stdout.write('Inserting reviews...')
        # Bulk create in chunks to avoid memory issues
        batch_size = 5000
        for i in range(0, len(reviews_to_create), batch_size):
            Review.objects.bulk_create(reviews_to_create[i:i+batch_size])
            
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(reviews_to_create)} reviews.'))
