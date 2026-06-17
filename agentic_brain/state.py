from typing import TypedDict, List, Dict, Any

class ProductAnalysisState(TypedDict):
    product_id: int
    competitor_id: int
    raw_reviews: List[str]
    ml_sentiments: List[Dict[str, Any]]
    
    # Competitor Fields
    competitor_data: Dict[str, Any]
    competitor_raw_reviews: List[str]
    competitor_ml_sentiments: List[Dict[str, Any]]
    
    product_insights: Dict[str, List[str]]
    final_recommendation: str
