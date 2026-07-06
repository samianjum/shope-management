
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from .models import ChakkiCustomer, ChakkiOrder, ChakkiSetting
from expenses.models import Expense

@login_required

def dashboard(request, **kwargs):
    tenant = request.tenant
    # Auto-ready pending orders
    pending_orders = ChakkiOrder.objects.filter(status='pending')
    for order in pending_orders:
        if order.ready_time and order.ready_time <= timezone.now():
            order.status = 'ready'
            order.save()
            messages.info(request, f"Order #{order.id} for {order.customer.name} is READY!")

    orders = ChakkiOrder.objects.all()
    pending = orders.filter(status='pending')
    ready = orders.filter(status='ready')
    completed = orders.filter(status='completed')
    partial_orders = orders.filter(payment_status='partial')
    unpaid_orders = orders.filter(payment_status='unpaid')

    # Counts for sidebar/header
    pending_count = pending.count()
    ready_count = ready.count()
    partial_count = partial_orders.count()
    completed_count = completed.count()

    # Ready orders list for notifications
    ready_orders = ready.order_by('-created_at')[:10]

    # Expenses & loans (keep for now, but we may not display them on dashboard)
    expenses = Expense.objects.all()
    total_expenses = sum(e.amount for e in expenses)
    total_given = sum(e.amount for e in expenses if e.is_credit and not e.is_repaid)
    total_taken = sum(e.amount for e in expenses if e.category == 'taken_loan' and not e.is_repaid)
    total_income = sum(o.total_amount for o in completed if o.payment_status == 'paid')
    net_profit = total_income - total_expenses

    recent_orders = orders.order_by('-created_at')[:10]
    context = {
        'pending': pending_count,
        'ready': ready_count,
        'completed': completed_count,
        'partial': partial_count,
        'pending_count': pending_count,
        'ready_count': ready_count,
        'partial_count': partial_count,
        'completed_count': completed_count,
        'ready_orders': ready_orders,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'total_pending_value': sum(o.total_amount for o in pending),
        'total_given': total_given,
        'total_taken': total_taken,
        'recent_orders': recent_orders,
        'tenant': tenant,
    }
    template = 'mobile/chakki_dashboard.html' if request.mobile else 'desktop/chakki_dashboard.html'
    return render(request, template, context)

@login_required
def add_order(request, **kwargs):
    setting, _ = ChakkiSetting.objects.get_or_create(id=1)
    if request.method == 'POST':
        # Create customer
        cust = ChakkiCustomer.objects.create(
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address')
        )
        total_kg = Decimal(request.POST.get('total_kg'))
        cleaning = request.POST.get('cleaning') == 'on'
        time_type = request.POST.get('time_type')
        time_value = int(request.POST.get('time_value', 0))
        ready_time = timezone.now()
        if time_type == 'minutes':
            ready_time += timezone.timedelta(minutes=time_value)
        elif time_type == 'hours':
            ready_time += timezone.timedelta(hours=time_value)
        elif time_type == 'days':
            ready_time += timezone.timedelta(days=time_value)
        order = ChakkiOrder.objects.create(
            customer=cust,
            total_kg=total_kg,
            is_cleaning_done=cleaning,
            ready_time=ready_time,
            status='pending'
        )
        # Calculate charges
        order.save()  # triggers calculation
        messages.success(request, f"Order #{order.id} created! Ready at {ready_time.strftime('%I:%M %p')}")
        return redirect('chakki_dashboard', schema_name=request.tenant.schema_name)

    template = 'mobile/add_order.html' if request.mobile else 'desktop/add_order.html'
    return render(request, template, {'setting': setting})

@login_required
def calculate_order(request, **kwargs):
    # AJAX endpoint to calculate charges dynamically
    if request.method == 'POST':
        total_kg = Decimal(request.POST.get('total_kg', 0))
        cleaning = request.POST.get('cleaning') == 'true'
        setting, _ = ChakkiSetting.objects.get_or_create(id=1)
        grinding_charges = total_kg * setting.grinding_rate
        cleaning_charges = total_kg * setting.cleaning_rate if cleaning else 0
        total_amount = grinding_charges + cleaning_charges
        return JsonResponse({
            'grinding_charges': float(grinding_charges),
            'cleaning_charges': float(cleaning_charges),
            'total_amount': float(total_amount)
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required

def order_list(request, order_type, **kwargs):
    # Generic order list view for pending, ready, partial, completed
    tenant = request.tenant
    orders = ChakkiOrder.objects.all()
    if order_type == 'pending':
        orders = orders.filter(status='pending')
    elif order_type == 'ready':
        orders = orders.filter(status='ready')
    elif order_type == 'partial':
        orders = orders.filter(payment_status='partial')
    elif order_type == 'completed':
        orders = orders.filter(status='completed')
    else:
        orders = orders.all()

    # Search/filter
    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(
            Q(customer__name__icontains=search) |
            Q(customer__phone__icontains=search) |
            Q(id__icontains=search)
        )

    context = {
        'orders': orders.order_by('-created_at'),
        'order_type': order_type,
        'tenant': tenant,
    }
    template = f'mobile/order_list.html' if request.mobile else f'desktop/order_list.html'
    return render(request, template, context)

@login_required
def order_detail(request, order_id, **kwargs):
    order = get_object_or_404(ChakkiOrder, id=order_id)
    if request.method == 'POST' and 'payment_amount' in request.POST:
        # Add payment
        amount = Decimal(request.POST.get('payment_amount', 0))
        if amount > 0:
            order.amount_paid += amount
            if order.amount_paid > order.total_amount:
                order.amount_paid = order.total_amount
            order.save()
            messages.success(request, f"Payment of ₹{amount} added. Remaining: ₹{order.remaining_amount}")
        return redirect('order_detail', schema_name=request.tenant.schema_name, order_id=order.id)

    context = {
        'order': order,
        'tenant': request.tenant,
    }
    template = 'mobile/order_detail.html' if request.mobile else 'desktop/order_detail.html'
    return render(request, template, context)

@login_required
def complete_order(request, order_id, **kwargs):
    order = get_object_or_404(ChakkiOrder, id=order_id)
    # Ensure fully paid
    if order.remaining_amount > 0:
        messages.error(request, "Order cannot be completed until full payment is received.")
        return redirect('order_detail', schema_name=request.tenant.schema_name, order_id=order.id)
    if order.status != 'completed':
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        messages.success(request, f"Order #{order.id} Completed!")
    return redirect('chakki_dashboard', schema_name=request.tenant.schema_name)

@login_required
def generate_transcript(request, order_id, **kwargs):
    order = get_object_or_404(ChakkiOrder, id=order_id)
    # Render HTML template
    context = {'order': order, 'tenant': request.tenant}
    html_string = render_to_string('desktop/transcript.html', context)
    # Generate PDF (using WeasyPrint) or just show HTML for print
    # For simplicity, we'll return a printable HTML page
    return render(request, 'desktop/transcript.html', context)

@login_required
def settings_view(request, **kwargs):
    setting, _ = ChakkiSetting.objects.get_or_create(id=1)
    if request.method == 'POST':
        setting.grinding_rate = Decimal(request.POST.get('grinding_rate'))
        setting.cleaning_rate = Decimal(request.POST.get('cleaning_rate'))
        setting.save()
        messages.success(request, "Rates updated!")
        return redirect('chakki_dashboard', schema_name=request.tenant.schema_name)
    template = 'mobile/settings.html' if request.mobile else 'desktop/settings.html'
    return render(request, template, {'setting': setting})
