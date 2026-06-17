from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from products.models import Product
from .graph import agentic_brain_graph

from django.db.models import Avg

class DashboardView(View):
    def get(self, request):
        department_query = request.GET.get('department')
        class_query = request.GET.get('class')
        
        # Fetch distinct options for the dropdowns
        departments = Product.objects.values_list('department_name', flat=True).distinct().order_by('department_name')
        classes = Product.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
        
        product_list = Product.objects.annotate(avg_rating=Avg('reviews__rating'))
        
        is_filtered = False
        if department_query and department_query != 'all':
            product_list = product_list.filter(department_name=department_query)
            is_filtered = True
        
        if class_query and class_query != 'all':
            product_list = product_list.filter(class_name=class_query)
            is_filtered = True
            
        if is_filtered:
            # Limit results so we don't overwhelm the DOM
            products = product_list.order_by('clothing_id')[:24]
        else:
            # Show top featured items by default
            products = product_list.order_by('-avg_rating')[:8]
            
        context = {
            'products': products,
            'departments': [d for d in departments if d],
            'classes': [c for c in classes if c],
            'selected_department': department_query or 'all',
            'selected_class': class_query or 'all',
            'is_filtered': is_filtered
        }
        return render(request, 'dashboard.html', context)

from django.http import JsonResponse, StreamingHttpResponse
import json
import time

class AnalyzeProductView(View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        
        # Check if this is an AJAX/Fetch request for the actual analysis
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
            competitor_id_str = request.GET.get('competitor_id')
            
            def generate_stream():
                initial_state = {"product_id": product.clothing_id}
                if competitor_id_str:
                    try:
                        initial_state["competitor_id"] = int(competitor_id_str)
                    except ValueError:
                        pass
                        
                merged_state = dict(initial_state)

                
                try:
                    # Stream through the LangGraph execution
                    for output in agentic_brain_graph.stream(initial_state):
                        for node_name, state_update in output.items():
                            # Merge the updates into our local state tracking
                            merged_state.update(state_update)
                            
                            # Yield the status event
                            event_data = {
                                "type": "status",
                                "node": node_name
                            }
                            yield f"data: {json.dumps(event_data)}\n\n"
                            
                    # Execution finished. Yield the final payload event.
                    from django.db.models import Avg
                    payload_data = {
                        "type": "complete",
                        "payload": {
                            "insights": merged_state.get("product_insights", {}),
                            "recommendation": merged_state.get("final_recommendation", ""),
                            "ml_sentiments": merged_state.get("ml_sentiments", []),
                            "main_product_data": {
                                "name": product.mock_name,
                                "price": str(product.mock_price),
                                "rating": float(product.reviews.aggregate(Avg('rating'))['rating__avg'] or 4.5)
                            },
                            "competitor_data": merged_state.get("competitor_data", {})
                        }
                    }
                    yield f"data: {json.dumps(payload_data)}\n\n"
                    
                    # Save historical record
                    from .models import AnalysisRecord
                    competitor_data = merged_state.get("competitor_data", {})
                    AnalysisRecord.objects.create(
                        product_id=merged_state.get("product_id"),
                        competitor_id=competitor_data.get("id") if competitor_data and competitor_data.get("id") else None,
                        ml_sentiments=merged_state.get("ml_sentiments", []),
                        competitor_ml_sentiments=merged_state.get("competitor_ml_sentiments", []),
                        pros=merged_state.get("product_insights", {}).get("pros", []),
                        cons=merged_state.get("product_insights", {}).get("cons", []),
                        final_recommendation=merged_state.get("final_recommendation", "")
                    )
                    
                except Exception as e:
                    error_data = {
                        "type": "error",
                        "message": str(e)
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"

            return StreamingHttpResponse(generate_stream(), content_type='text/event-stream')
            
        # Initial page load: render the empty shell waiting for user interaction
        from django.db.models import Avg
        competitors = Product.objects.filter(class_name=product.class_name).exclude(clothing_id=product.clothing_id).annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')[:20]
        context = {
            'product': product,
            'competitors': competitors,
        }
        return render(request, 'analysis_result.html', context)
