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

def generate_insights(state: ProductAnalysisState) -> ProductAnalysisState:
    """
    Uses an LLM to extract specific pros and cons from the reviews and their ML sentiments.
    """
    ml_sentiments = state.get("ml_sentiments", [])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert product analyst. Based on the following user reviews and their machine learning sentiment classifications, extract a concise list of 'pros' and 'cons'. Format your response exactly as a JSON object with keys 'pros' and 'cons', each containing a list of strings."),
        ("user", "Reviews and Sentiments:\n{sentiments}")
    ])
    
    chain = prompt | llm
    
    # In a production setting with complex schemas, LangChain structured outputs are recommended.
    response = chain.invoke({"sentiments": ml_sentiments})
    
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
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Agentic Brain of an e-commerce platform. Based on these extracted pros and cons, write a final, engaging, 2-3 sentence recommendation for this product. Be objective."),
        ("user", "Pros: {pros}\nCons: {cons}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "pros": insights.get("pros", []),
        "cons": insights.get("cons", [])
    })
    
    return {"final_recommendation": response.content}
