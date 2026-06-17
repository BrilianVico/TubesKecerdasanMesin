import json
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from ml_engine.services import SentimentInferenceService
from .state import ProductAnalysisState

# Initialize the LLM
# Note: Ensure OPENAI_API_KEY is defined in your root .env file!
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

def collect_reviews(state: ProductAnalysisState) -> ProductAnalysisState:
    """
    Fetches up to 20 raw reviews from the database for the given product.
    """
    from products.models import Review
    product_id = state.get("product_id")
    
    # Query up to 20 reviews to save LLM tokens and ensure fast execution
    reviews = Review.objects.filter(product_id=product_id).values_list('review_text', flat=True)[:20]
    
    # Convert queryset to list
    simulated_reviews = list(reviews)
    
    # Fallback if no reviews found
    if not simulated_reviews:
        simulated_reviews = ["No user reviews available for this product yet."]
        
    return {"raw_reviews": simulated_reviews}

def analyze_sentiment(state: ProductAnalysisState) -> ProductAnalysisState:
    """
    Passes raw reviews through our local Random Forest ML Engine.
    """
    raw_reviews = state.get("raw_reviews", [])
    service = SentimentInferenceService()
    
    ml_sentiments = []
    for review in raw_reviews:
        result = service.predict_sentiment(review)
        ml_sentiments.append({
            "text": review,
            "sentiment": result.get("sentiment"),
            "confidence": result.get("confidence")
        })
        
    return {"ml_sentiments": ml_sentiments}

def compare_products(state: ProductAnalysisState) -> ProductAnalysisState:
    """
    Fetches a competitor product and its reviews, then runs Sentiment Analysis.
    """
    from products.models import Product, Review
    from ml_engine.services import SentimentInferenceService
    from django.db.models import Avg
    
    product_id = state.get("product_id")
    try:
        main_product = Product.objects.get(clothing_id=product_id)
        # Find a competitor in the same class
        competitor = Product.objects.filter(class_name=main_product.class_name).exclude(clothing_id=product_id).first()
    except Product.DoesNotExist:
        competitor = None
        
    if not competitor:
        return {
            "competitor_data": {"id": None, "name": "No Competitor Found", "price": 0, "rating": 0},
            "competitor_raw_reviews": [],
            "competitor_ml_sentiments": []
        }
        
    # Fetch reviews
    reviews = Review.objects.filter(product_id=competitor.clothing_id).values_list('review_text', flat=True)[:20]
    competitor_reviews = list(reviews)
    if not competitor_reviews:
        competitor_reviews = ["No reviews for competitor."]
        
    service = SentimentInferenceService()
    competitor_ml_sentiments = []
    for review in competitor_reviews:
        result = service.predict_sentiment(review)
        competitor_ml_sentiments.append({
            "text": review,
            "sentiment": result.get("sentiment"),
            "confidence": result.get("confidence")
        })
        
    return {
        "competitor_data": {
            "id": competitor.clothing_id,
            "name": competitor.mock_name,
            "price": str(competitor.mock_price),
            "rating": competitor.reviews.aggregate(Avg('rating'))['rating__avg'] or 4.5
        },
        "competitor_raw_reviews": competitor_reviews,
        "competitor_ml_sentiments": competitor_ml_sentiments
    }

def generate_insights(state: ProductAnalysisState) -> ProductAnalysisState:
    """
    Uses an LLM to extract specific pros and cons from the reviews and their ML sentiments.
    Now also compares against the competitor.
    """
    ml_sentiments = state.get("ml_sentiments", [])
    competitor_ml_sentiments = state.get("competitor_ml_sentiments", [])
    competitor_data = state.get("competitor_data", {})
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert product analyst. Based on the main product's reviews and a competitor's reviews (both with ML sentiment classifications), extract a concise list of 'pros' and 'cons' for the MAIN product. Explicitly highlight where the main product wins or loses against the competitor. Format your response exactly as a JSON object with keys 'pros' and 'cons', each containing a list of strings."),
        ("user", "Main Product Sentiments:\n{sentiments}\n\nCompetitor ({competitor_name}) Sentiments:\n{competitor_sentiments}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "sentiments": ml_sentiments,
        "competitor_name": competitor_data.get("name", "Competitor"),
        "competitor_sentiments": competitor_ml_sentiments
    })
    
    try:
        # Strip potential markdown blocks
        cleaned_response = response.content.replace("```json", "").replace("```", "").strip()
        insights = json.loads(cleaned_response)
    except Exception:
        insights = {"pros": ["Could not parse pros"], "cons": ["Could not parse cons"]}
        
    return {"product_insights": insights}

def make_decision(state: ProductAnalysisState) -> ProductAnalysisState:
    """
    Generates a final, reasoned recommendation narrative.
    """
    insights = state.get("product_insights", {})
    competitor_data = state.get("competitor_data", {})
    from products.models import Product
    from django.db.models import Avg
    main_product = Product.objects.get(clothing_id=state.get("product_id"))
    main_rating = main_product.reviews.aggregate(Avg('rating'))['rating__avg'] or 4.5
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Agentic Brain of an e-commerce platform. Generate a final, definitive 2-3 sentence recommendation weighing the main product against the competitor based on price, rating, and extracted pros/cons. State clearly which one is the better buy."),
        ("user", "Main Product: Price ${main_price}, Rating {main_rating}\nCompetitor: Price ${comp_price}, Rating {comp_rating}\n\nMain Product Pros: {pros}\nMain Product Cons: {cons}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "main_price": main_product.mock_price,
        "main_rating": main_rating,
        "comp_price": competitor_data.get("price", "N/A"),
        "comp_rating": competitor_data.get("rating", "N/A"),
        "pros": insights.get("pros", []),
        "cons": insights.get("cons", [])
    })
    
    return {"final_recommendation": response.content}
