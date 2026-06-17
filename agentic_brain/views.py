from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from products.models import Product
from .graph import agentic_brain_graph

class DashboardView(View):
    def get(self, request):
        # Fetch all products
        product_list = Product.objects.all().order_by('clothing_id')
        
        # Paginate (20 per page)
        paginator = Paginator(product_list, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'dashboard.html', {'page_obj': page_obj})

class AnalyzeProductView(View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        
        # Initialize LangGraph state
        initial_state = {"product_id": product.clothing_id}
        
        # Execute the agentic brain graph
        try:
            final_state = agentic_brain_graph.invoke(initial_state)
        except Exception as e:
            # Handle potential LLM or parsing errors gracefully
            final_state = {
                "product_insights": {"pros": ["Error processing AI insights"], "cons": [str(e)]},
                "final_recommendation": "Sorry, the Agentic Brain encountered an error.",
                "ml_sentiments": []
            }
            
        context = {
            'product': product,
            'insights': final_state.get('product_insights', {}),
            'recommendation': final_state.get('final_recommendation', ''),
            'ml_sentiments': final_state.get('ml_sentiments', [])
        }
        
        return render(request, 'analysis_result.html', context)
