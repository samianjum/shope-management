
def tenant_processor(request):
    return {'tenant': getattr(request, 'tenant', None)}

from chakki.models import ChakkiOrder
from django.db.models import Q

def chakki_counts(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return {}
    orders = ChakkiOrder.objects.all()
    pending_count = orders.filter(status='pending').count()
    ready_count = orders.filter(status='ready').count()
    partial_count = orders.filter(payment_status='partial').count()
    completed_count = orders.filter(status='completed').count()
    ready_orders = orders.filter(status='ready').order_by('-created_at')[:10]
    return {
        'pending_count': pending_count,
        'ready_count': ready_count,
        'partial_count': partial_count,
        'completed_count': completed_count,
        'ready_orders': ready_orders,
    }
