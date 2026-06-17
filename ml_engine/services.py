import os
import joblib
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from django.conf import settings

class SentimentInferenceService:
    """
    Singleton service to handle Machine Learning inference using the Random Forest model.
    Loads the serialized .pkl models into memory exactly ONCE on app startup.
    """
    _instance = None
    _rf_model = None
    _tfidf_vectorizer = None
    _is_loaded = False
    _stemmer = None
    _stop_words = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentimentInferenceService, cls).__new__(cls)
        return cls._instance

    def load_models(self):
        """Loads the serialized models and NLTK resources from the artifacts directory if not already loaded."""
        if not self._is_loaded:
            # Safe NLTK downloads
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
                
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except LookupError:
                nltk.download('punkt_tab', quiet=True)

            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords', quiet=True)

            self._stemmer = PorterStemmer()
            self._stop_words = set(stopwords.words('english'))

            artifacts_dir = os.path.join(settings.BASE_DIR, 'ml_engine', 'artifacts')
            rf_path = os.path.join(artifacts_dir, 'rf_model.pkl')
            tfidf_path = os.path.join(artifacts_dir, 'tfidf_vectorizer.pkl')

            try:
                self._rf_model = joblib.load(rf_path)
                self._tfidf_vectorizer = joblib.load(tfidf_path)
                self._is_loaded = True
                print("ML Models and NLTK resources successfully loaded into memory.")
            except Exception as e:
                print(f"Error loading ML models: {e}")

    def _preprocess_text(self, text: str) -> str:
        """
        Cleans and preprocesses the raw input text to match the format the models were trained on.
        - Lowercases
        - Removes non-alphabetic characters
        - Tokenizes
        - Removes stopwords
        - Stems using PorterStemmer
        """
        text = text.lower()
        # Keep only alphabetic characters
        text = re.sub(r'[^a-z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and apply stemming
        cleaned_tokens = [self._stemmer.stem(word) for word in tokens if word not in self._stop_words]
        
        return ' '.join(cleaned_tokens)

    def predict_sentiment(self, text: str) -> dict:
        """
        Predicts sentiment for a given raw text string.
        Returns a dictionary with sentiment label and confidence score.
        """
        if not self._is_loaded:
            self.load_models()
            
        if not text or not isinstance(text, str):
            return {"sentiment": "Unknown", "confidence": 0.0, "error": "Invalid input text"}

        try:
            # 1. Preprocess the raw text to match training format
            cleaned_text = self._preprocess_text(text)
            
            # 2. Transform the text using the TF-IDF vectorizer
            text_features = self._tfidf_vectorizer.transform([cleaned_text])
            
            # 3. Predict class and probabilities
            prediction = self._rf_model.predict(text_features)[0]
            probabilities = self._rf_model.predict_proba(text_features)[0]
            
            # For a binary model: 1 = Recommended (Positive), 0 = Not Recommended (Negative)
            sentiment_label = "Positive" if prediction == 1 else "Negative"
            
            # The confidence is the probability of the predicted class
            confidence = probabilities[1] if prediction == 1 else probabilities[0]

            return {
                "sentiment": sentiment_label,
                "confidence": round(float(confidence), 4)
            }
        except Exception as e:
            return {"sentiment": "Error", "confidence": 0.0, "error": str(e)}
