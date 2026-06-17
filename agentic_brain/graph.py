from langgraph.graph import StateGraph, START, END
from .state import ProductAnalysisState
from .nodes import collect_reviews, analyze_sentiment, compare_products, generate_insights, make_decision

# 1. Initialize the StateGraph with our TypedDict
workflow = StateGraph(ProductAnalysisState)

# 2. Add Nodes
workflow.add_node("collect_reviews", collect_reviews)
workflow.add_node("analyze_sentiment", analyze_sentiment)
workflow.add_node("compare_products", compare_products)
workflow.add_node("generate_insights", generate_insights)
workflow.add_node("make_decision", make_decision)

# 3. Define Edges (The execution flow)
workflow.add_edge(START, "collect_reviews")
workflow.add_edge("collect_reviews", "analyze_sentiment")
workflow.add_edge("analyze_sentiment", "compare_products")
workflow.add_edge("compare_products", "generate_insights")
workflow.add_edge("generate_insights", "make_decision")
workflow.add_edge("make_decision", END)

# 4. Compile the Graph
agentic_brain_graph = workflow.compile()
