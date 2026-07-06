#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

BASE_DIR = os.getcwd()

def write_file(path, content):
    path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created/Updated: {path}")

def delete_file(path):
    path = os.path.join(BASE_DIR, path)
    if os.path.exists(path):
        os.remove(path)
        print(f"🗑️ Deleted: {path}")

def main():
    print("🚀 Rebuilding Chakki module with full features...")

    # -----------------------------
    # 1. Update models.py
    # -----------------------------
    chakki_models = '''
from django.db import models
from django.utils import timezone
from decimal import Decimal

class ChakkiCustomer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ChakkiSetting(models.Model):
    grinding_rate = models.DecimalField(max_digits=10, decimal_places=2, default=10.0, help_text="Per KG")
    cleaning_rate = models.DecimalField(max_digits=10, decimal_places=2, default=5.0, help_text="Per KG")

    def __str__(self):
        return f"Grind: {self.grinding_rate}, Clean: {self.cleaning_rate}"

class ChakkiOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]
    customer = models.ForeignKey(ChakkiCustomer, on_delete=models.CASCADE)
    total_kg = models.DecimalField(max_digits=10, decimal_places=2)
    grinding_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cleaning_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_cleaning_done = models.BooleanField(default=False)
    ready_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def remaining_amount(self):
        return self.total_amount - self.amount_paid

    def save(self, *args, **kwargs):
        setting, _ = ChakkiSetting.objects.get_or_create(id=1)
        self.grinding_charges = self.total_kg * setting.grinding_rate
        self.cleaning_charges = self.total_kg * setting.cleaning_rate if self.is_cleaning_done else 0
        self.total_amount = self.grinding_charges + self.cleaning_charges
        # Determine payment status
        if self.amount_paid == 0:
            self.payment_status = 'unpaid'
        elif self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
            self.amount_paid = self.total_amount
        else:
            self.payment_status = 'partial'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name}"
'''
    write_file("chakki/models.py", chakki_models)

    # -----------------------------
    # 2. Update views.py
    # -----------------------------
    chakki_views = '''
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
    total_income = sum(o.total_amount for o in completed if o.payment_status == 'paid')
    total_pending_value = sum(o.total_amount for o in pending)
    partial_orders = orders.filter(payment_status='partial')
    unpaid_orders = orders.filter(payment_status='unpaid')

    # Expenses & loans
    expenses = Expense.objects.all()
    total_expenses = sum(e.amount for e in expenses)
    total_given = sum(e.amount for e in expenses if e.is_credit and not e.is_repaid)
    total_taken = sum(e.amount for e in expenses if e.category == 'taken_loan' and not e.is_repaid)
    net_profit = total_income - total_expenses

    recent_orders = orders.order_by('-created_at')[:10]
    context = {
        'pending': pending.count(),
        'ready': ready.count(),
        'completed': completed.count(),
        'partial': partial_orders.count(),
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_pending_value': total_pending_value,
        'total_given': total_given,
        'total_taken': total_taken,
        'net_profit': net_profit,
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
    # Generic order list view for pending, partial, completed
    tenant = request.tenant
    orders = ChakkiOrder.objects.all()
    if order_type == 'pending':
        orders = orders.filter(status='pending')
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
'''
    write_file("chakki/views.py", chakki_views)

    # -----------------------------
    # 3. Update urls.py
    # -----------------------------
    chakki_urls = '''
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='chakki_dashboard'),
    path('add/', views.add_order, name='add_order'),
    path('calculate/', views.calculate_order, name='calculate_order'),
    path('orders/<str:order_type>/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('transcript/<int:order_id>/', views.generate_transcript, name='generate_transcript'),
    path('settings/', views.settings_view, name='chakki_settings'),
]
'''
    write_file("chakki/urls.py", chakki_urls)

    # -----------------------------
    # 4. Templates
    # -----------------------------
    # Desktop templates
    desktop_base = '''
<!DOCTYPE html>
<html>
<head><title>{% block title %}SaaS System{% endblock %}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>body{padding-top:20px; background:#f8f9fa;} .sidebar{background:#343a40; min-height:100vh;}</style>
</head>
<body>
<div class="container-fluid">
<div class="row">
<div class="col-md-2 sidebar text-white p-3">
    <h4>{{ tenant.name|default:"SaaS" }}</h4>
    <hr>
    <a href="/portal/{{ tenant.schema_name }}/dashboard/" class="text-white d-block">🏠 Dashboard</a>
    <a href="/portal/{{ tenant.schema_name }}/chakki/" class="text-white d-block">🌾 Chakki</a>
    <a href="/portal/{{ tenant.schema_name }}/expenses/" class="text-white d-block">💰 Expenses</a>
    <a href="/portal/{{ tenant.schema_name }}/chakki/settings/" class="text-white d-block">⚙️ Settings</a>
    <a href="/portal/{{ tenant.schema_name }}/logout/" class="text-white d-block mt-5">🚪 Logout</a>
</div>
<div class="col-md-10 p-4">
    {% if messages %}{% for m in messages %}<div class="alert alert-info">{{ m }}</div>{% endfor %}{% endif %}
    {% block content %}{% endblock %}
</div>
</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''
    write_file("templates/desktop/base.html", desktop_base)

    # Chakki Dashboard
    chakki_dashboard_desktop = '''
{% extends "desktop/base.html" %}
{% block content %}
<div class="d-flex justify-content-between">
    <h2>🌾 Chakki Dashboard</h2>
    <div>
        <a href="/portal/{{ tenant.schema_name }}/chakki/add/" class="btn btn-primary">+ New Order</a>
        <a href="/portal/{{ tenant.schema_name }}/chakki/settings/" class="btn btn-secondary">⚙️ Rates</a>
    </div>
</div>
<div class="row mt-3">
    <div class="col-md-3"><div class="card p-3"><h5>Pending</h5><h2>{{ pending }}</h2><a href="/portal/{{ tenant.schema_name }}/chakki/orders/pending/" class="btn btn-sm btn-outline-primary">View</a></div></div>
    <div class="col-md-3"><div class="card p-3 bg-warning"><h5>Ready</h5><h2>{{ ready }}</h2><a href="/portal/{{ tenant.schema_name }}/chakki/orders/pending/" class="btn btn-sm btn-outline-dark">View</a></div></div>
    <div class="col-md-3"><div class="card p-3 bg-info"><h5>Partial Paid</h5><h2>{{ partial }}</h2><a href="/portal/{{ tenant.schema_name }}/chakki/orders/partial/" class="btn btn-sm btn-outline-dark">View</a></div></div>
    <div class="col-md-3"><div class="card p-3 bg-success text-white"><h5>Completed</h5><h2>{{ completed }}</h2><a href="/portal/{{ tenant.schema_name }}/chakki/orders/completed/" class="btn btn-sm btn-outline-light">View</a></div></div>
</div>
<div class="row mt-3">
    <div class="col-md-4"><div class="card p-3"><h6>Total Income</h6><h4>₹{{ total_income }}</h4></div></div>
    <div class="col-md-4"><div class="card p-3"><h6>Total Expenses</h6><h4>₹{{ total_expenses }}</h4></div></div>
    <div class="col-md-4"><div class="card p-3"><h6>Net Profit</h6><h4>₹{{ net_profit }}</h4></div></div>
</div>
<div class="row mt-2">
    <div class="col-md-6"><div class="card p-3"><h6>Pending Value</h6><h4>₹{{ total_pending_value }}</h4></div></div>
    <div class="col-md-3"><div class="card p-3"><h6>Loans Given</h6><h4>₹{{ total_given }}</h4></div></div>
    <div class="col-md-3"><div class="card p-3"><h6>Loans Taken</h6><h4>₹{{ total_taken }}</h4></div></div>
</div>
<h4 class="mt-4">Recent Orders</h4>
<table class="table table-bordered">
    <tr><th>ID</th><th>Customer</th><th>KG</th><th>Total</th><th>Paid</th><th>Status</th><th>Ready</th><th>Action</th></tr>
    {% for o in recent_orders %}
    <tr>
        <td>{{ o.id }}</td><td>{{ o.customer.name }}</td><td>{{ o.total_kg }}</td><td>₹{{ o.total_amount }}</td><td>₹{{ o.amount_paid }}</td>
        <td>
            {% if o.status == 'ready' %}<span class="badge bg-warning">Ready</span>
            {% elif o.status == 'completed' %}<span class="badge bg-success">Done</span>
            {% else %}<span class="badge bg-secondary">Pending</span>{% endif %}
            {% if o.payment_status == 'partial' %}<span class="badge bg-info">Partial</span>{% endif %}
        </td>
        <td>{{ o.ready_time|date:"d M H:i" }}</td>
        <td><a href="/portal/{{ tenant.schema_name }}/chakki/order/{{ o.id }}/" class="btn btn-sm btn-primary">View</a></td>
    </tr>
    {% endfor %}
</table>
{% endblock %}
'''
    write_file("templates/desktop/chakki_dashboard.html", chakki_dashboard_desktop)

    # Add Order with live calculation and confirmation modal
    add_order_desktop = '''
{% extends "desktop/base.html" %}
{% block content %}
<h2>Add Order</h2>
<form method="post" id="orderForm">
    {% csrf_token %}
    <div class="row">
        <div class="col-md-6">
            <h5>Customer Details</h5>
            <div class="mb-2"><label>Name *</label><input name="name" class="form-control" required></div>
            <div class="mb-2"><label>Phone</label><input name="phone" class="form-control"></div>
            <div class="mb-2"><label>Address</label><input name="address" class="form-control"></div>
        </div>
        <div class="col-md-6">
            <h5>Order Details</h5>
            <div class="mb-2"><label>Total KG *</label><input name="total_kg" id="total_kg" class="form-control" type="number" step="0.1" required></div>
            <div class="mb-2"><input type="checkbox" name="cleaning" id="cleaning" value="on"> <label for="cleaning">Cleaning Done</label></div>
            <div class="mb-2"><label>Ready in</label>
                <input type="number" name="time_value" class="form-control" placeholder="e.g. 2" value="1">
                <select name="time_type" class="form-control"><option value="minutes">Minutes</option><option value="hours" selected>Hours</option><option value="days">Days</option></select>
            </div>
        </div>
    </div>
    <div class="row mt-3">
        <div class="col-md-4"><div class="card p-2"><h6>Grinding Charges</h6><h4 id="grinding_display">₹0.00</h4></div></div>
        <div class="col-md-4"><div class="card p-2"><h6>Cleaning Charges</h6><h4 id="cleaning_display">₹0.00</h4></div></div>
        <div class="col-md-4"><div class="card p-2 bg-info"><h6>Total Amount</h6><h4 id="total_display">₹0.00</h4></div></div>
    </div>
    <button type="button" class="btn btn-primary mt-3" data-bs-toggle="modal" data-bs-target="#confirmModal" id="previewBtn">Preview & Confirm</button>
</form>

<!-- Confirmation Modal -->
<div class="modal fade" id="confirmModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Confirm Order</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" id="modalBody">
        <!-- Filled by JS -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary" id="confirmSubmit">Confirm Order</button>
      </div>
    </div>
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const totalKg = document.getElementById('total_kg');
    const cleaning = document.getElementById('cleaning');
    const grindingDisplay = document.getElementById('grinding_display');
    const cleaningDisplay = document.getElementById('cleaning_display');
    const totalDisplay = document.getElementById('total_display');
    const previewBtn = document.getElementById('previewBtn');
    const modalBody = document.getElementById('modalBody');
    const confirmSubmit = document.getElementById('confirmSubmit');

    function updateCalculations() {
        const kg = parseFloat(totalKg.value) || 0;
        const clean = cleaning.checked;
        fetch('/portal/{{ tenant.schema_name }}/chakki/calculate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: 'total_kg=' + kg + '&cleaning=' + clean
        })
        .then(res => res.json())
        .then(data => {
            grindingDisplay.textContent = '₹' + data.grinding_charges.toFixed(2);
            cleaningDisplay.textContent = '₹' + data.cleaning_charges.toFixed(2);
            totalDisplay.textContent = '₹' + data.total_amount.toFixed(2);
            // Store for modal
            window.calcData = data;
        });
    }

    totalKg.addEventListener('input', updateCalculations);
    cleaning.addEventListener('change', updateCalculations);
    updateCalculations();

    previewBtn.addEventListener('click', function(e) {
        // Build modal content
        const data = window.calcData || {};
        const kg = parseFloat(totalKg.value) || 0;
        const clean = cleaning.checked;
        modalBody.innerHTML = `
            <p><strong>Customer:</strong> ${document.querySelector('input[name="name"]').value || 'N/A'}</p>
            <p><strong>Total KG:</strong> ${kg}</p>
            <p><strong>Cleaning:</strong> ${clean ? 'Yes' : 'No'}</p>
            <hr>
            <p><strong>Grinding Charges:</strong> ₹${(data.grinding_charges || 0).toFixed(2)}</p>
            <p><strong>Cleaning Charges:</strong> ₹${(data.cleaning_charges || 0).toFixed(2)}</p>
            <h5><strong>Total Amount:</strong> ₹${(data.total_amount || 0).toFixed(2)}</h5>
        `;
    });

    confirmSubmit.addEventListener('click', function() {
        document.getElementById('orderForm').submit();
    });
});
</script>
{% endblock %}
'''
    write_file("templates/desktop/add_order.html", add_order_desktop)

    # Order List (pending/partial/completed)
    order_list_desktop = '''
{% extends "desktop/base.html" %}
{% block content %}
<h2>{{ order_type|title }} Orders</h2>
<form method="get" class="mb-3">
    <div class="input-group">
        <input type="text" name="search" class="form-control" placeholder="Search by customer, phone, order ID" value="{{ request.GET.search }}">
        <button class="btn btn-outline-secondary">Search</button>
    </div>
</form>
<table class="table table-bordered">
    <tr><th>ID</th><th>Customer</th><th>KG</th><th>Total</th><th>Paid</th><th>Remaining</th><th>Status</th><th>Ready</th><th>Action</th></tr>
    {% for o in orders %}
    <tr>
        <td>{{ o.id }}</td><td>{{ o.customer.name }}</td><td>{{ o.total_kg }}</td><td>₹{{ o.total_amount }}</td><td>₹{{ o.amount_paid }}</td><td>₹{{ o.remaining_amount }}</td>
        <td>
            {% if o.status == 'ready' %}<span class="badge bg-warning">Ready</span>
            {% elif o.status == 'completed' %}<span class="badge bg-success">Done</span>
            {% else %}<span class="badge bg-secondary">Pending</span>{% endif %}
            {% if o.payment_status == 'partial' %}<span class="badge bg-info">Partial</span>{% endif %}
        </td>
        <td>{{ o.ready_time|date:"d M H:i" }}</td>
        <td><a href="/portal/{{ tenant.schema_name }}/chakki/order/{{ o.id }}/" class="btn btn-sm btn-primary">View</a></td>
    </tr>
    {% empty %}
    <tr><td colspan="9">No orders found.</td></tr>
    {% endfor %}
</table>
{% endblock %}
'''
    write_file("templates/desktop/order_list.html", order_list_desktop)

    # Order Detail with payment and transcript
    order_detail_desktop = '''
{% extends "desktop/base.html" %}
{% block content %}
<h2>Order #{{ order.id }}</h2>
<div class="row">
    <div class="col-md-6">
        <div class="card p-3">
            <h5>Customer</h5>
            <p><strong>Name:</strong> {{ order.customer.name }}</p>
            <p><strong>Phone:</strong> {{ order.customer.phone }}</p>
            <p><strong>Address:</strong> {{ order.customer.address }}</p>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card p-3">
            <h5>Order Details</h5>
            <p><strong>Total KG:</strong> {{ order.total_kg }}</p>
            <p><strong>Grinding Charges:</strong> ₹{{ order.grinding_charges }}</p>
            <p><strong>Cleaning Charges:</strong> ₹{{ order.cleaning_charges }}</p>
            <p><strong>Total Amount:</strong> ₹{{ order.total_amount }}</p>
            <p><strong>Amount Paid:</strong> ₹{{ order.amount_paid }}</p>
            <p><strong>Remaining:</strong> ₹{{ order.remaining_amount }}</p>
            <p><strong>Status:</strong> {{ order.status }} | Payment: {{ order.payment_status }}</p>
            <p><strong>Ready Time:</strong> {{ order.ready_time|date:"d M Y H:i" }}</p>
        </div>
    </div>
</div>
<div class="mt-3">
    {% if order.status != 'completed' %}
    <form method="post" class="row g-3">
        {% csrf_token %}
        <div class="col-auto">
            <input type="number" name="payment_amount" step="0.01" class="form-control" placeholder="Payment amount" required>
        </div>
        <div class="col-auto">
            <button class="btn btn-success">Add Payment</button>
        </div>
    </form>
    <div class="mt-2">
        {% if order.remaining_amount == 0 %}
            <a href="/portal/{{ tenant.schema_name }}/chakki/complete/{{ order.id }}/" class="btn btn-primary">Complete Order</a>
        {% else %}
            <span class="text-muted">Complete order requires full payment (remaining: ₹{{ order.remaining_amount }})</span>
        {% endif %}
    </div>
    {% endif %}
</div>
<div class="mt-3">
    <a href="/portal/{{ tenant.schema_name }}/chakki/transcript/{{ order.id }}/" target="_blank" class="btn btn-secondary">📄 Transcript</a>
</div>
{% endblock %}
'''
    write_file("templates/desktop/order_detail.html", order_detail_desktop)

    # Transcript (printable)
    transcript_html = '''
<!DOCTYPE html>
<html>
<head><title>Transcript - Order #{{ order.id }}</title>
<style>
    body { font-family: Arial, sans-serif; padding: 40px; }
    .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
    .watermark { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); font-size: 80px; color: rgba(0,0,0,0.1); pointer-events: none; }
    .footer { text-align: center; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px; }
    table { width: 100%; border-collapse: collapse; }
    td, th { padding: 8px; border: 1px solid #ccc; }
    .right { text-align: right; }
</style>
</head>
<body>
<div class="watermark">PAID</div>
<div class="header">
    <h1>{{ tenant.name }}</h1>
    <p>Flour Mill Invoice</p>
</div>
<h3>Order #{{ order.id }}</h3>
<p><strong>Customer:</strong> {{ order.customer.name }}<br>
<strong>Phone:</strong> {{ order.customer.phone }}<br>
<strong>Address:</strong> {{ order.customer.address }}</p>
<table>
    <tr><th>Item</th><th>KG</th><th>Rate</th><th>Amount</th></tr>
    <tr><td>Grinding</td><td>{{ order.total_kg }}</td><td>{{ order.grinding_charges|divide:order.total_kg }}</td><td class="right">₹{{ order.grinding_charges }}</td></tr>
    {% if order.is_cleaning_done %}
    <tr><td>Cleaning</td><td>{{ order.total_kg }}</td><td>{{ order.cleaning_charges|divide:order.total_kg }}</td><td class="right">₹{{ order.cleaning_charges }}</td></tr>
    {% endif %}
    <tr><th colspan="3">Total</th><th class="right">₹{{ order.total_amount }}</th></tr>
    <tr><td colspan="3">Amount Paid</td><td class="right">₹{{ order.amount_paid }}</td></tr>
    <tr><td colspan="3">Remaining</td><td class="right">₹{{ order.remaining_amount }}</td></tr>
</table>
<div class="footer">
    <p>Generated on {% now "d M Y H:i" %} | Thank you!</p>
</div>
</body>
</html>
'''
    write_file("templates/desktop/transcript.html", transcript_html)

    # Mobile templates (simplified – reuse desktop for now, but we'll create basic versions)
    # To save space, we'll just copy desktop templates for mobile (user can customize later)
    # Actually we need base.html for mobile and other templates.
    mobile_base = '''
<!DOCTYPE html>
<html>
<head><title>{% block title %}SaaS{% endblock %}</title>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<style>body{background:#f1f1f1; padding:10px;} .btn-lg{padding:15px; font-size:1.2rem;} .card{margin-bottom:15px;}</style>
</head>
<body>
<div class="container">
    <div class="mb-3 d-flex justify-content-between align-items-center">
        <h4>📱 {{ tenant.name }}</h4>
        <a href="/portal/{{ tenant.schema_name }}/logout/" class="btn btn-sm btn-danger">Logout</a>
    </div>
    {% if messages %}{% for m in messages %}<div class="alert alert-success alert-dismissible">{{ m }}</div>{% endfor %}{% endif %}
    {% block content %}{% endblock %}
    <div class="fixed-bottom bg-white p-2 d-flex justify-content-around border-top">
        <a href="/portal/{{ tenant.schema_name }}/dashboard/" class="btn btn-link">🏠</a>
        <a href="/portal/{{ tenant.schema_name }}/chakki/" class="btn btn-link">🌾</a>
        <a href="/portal/{{ tenant.schema_name }}/expenses/" class="btn btn-link">💰</a>
        <a href="/portal/{{ tenant.schema_name }}/chakki/add/" class="btn btn-primary">+ Order</a>
    </div>
</div>
</body>
</html>
'''
    write_file("templates/mobile/base.html", mobile_base)

    # We'll copy desktop templates to mobile (just for now)
    # But we need to ensure they extend mobile base. We'll create simplified versions.
    # For brevity, we'll just create mobile versions that extend mobile base.
    # We'll create a simple dashboard for mobile.
    chakki_dashboard_mobile = '''
{% extends "mobile/base.html" %}
{% block content %}
<div class="row text-center">
    <div class="col-4"><div class="card"><h5>Pending</h5><h2>{{ pending }}</h2><a href="/portal/{{ tenant.schema_name }}/chakki/orders/pending/" class="btn btn-sm btn-primary">View</a></div></div>
    <div class="col-4"><div class="card bg-warning"><h5>Ready</h5><h2>{{ ready }}</h2><a href="/portal/{{ tenant.schema_name }}/chakki/orders/pending/" class="btn btn-sm btn-dark">View</a></div></div>
    <div class="col-4"><div class="card bg-info"><h5>Partial</h5><h2>{{ partial }}</h2><a href="/portal/{{ tenant.schema_name }}/chakki/orders/partial/" class="btn btn-sm btn-dark">View</a></div></div>
</div>
<div class="row text-center mt-2">
    <div class="col-6"><div class="card"><h6>Income</h6><h4>₹{{ total_income }}</h4></div></div>
    <div class="col-6"><div class="card"><h6>Profit</h6><h4>₹{{ net_profit }}</h4></div></div>
</div>
<a href="/portal/{{ tenant.schema_name }}/chakki/add/" class="btn btn-primary btn-lg w-100 mb-3">➕ New Order</a>
<h6>Recent Orders</h6>
{% for o in recent_orders %}
<div class="card">
    <div class="card-body">
        <b>#{{ o.id }} {{ o.customer.name }}</b> - {{ o.total_kg }}kg | ₹{{ o.total_amount }}<br>
        <small>Ready: {{ o.ready_time|date:"d M H:i" }} | Status: {{ o.status }}</small>
        <a href="/portal/{{ tenant.schema_name }}/chakki/order/{{ o.id }}/" class="btn btn-sm btn-primary float-end">View</a>
    </div>
</div>
{% endfor %}
{% endblock %}
'''
    write_file("templates/mobile/chakki_dashboard.html", chakki_dashboard_mobile)

    # For other mobile templates, we'll create basic ones extending mobile base.
    # We'll just copy the desktop ones but replace extends with mobile/base.
    for template_name in ['add_order.html', 'order_list.html', 'order_detail.html', 'settings.html']:
        src = f"templates/desktop/{template_name}"
        dst = f"templates/mobile/{template_name}"
        if os.path.exists(src):
            with open(src, 'r') as f:
                content = f.read()
            # Replace extends line
            content = content.replace("{% extends \"desktop/base.html\" %}", "{% extends \"mobile/base.html\" %}")
            write_file(dst, content)

    # Also transcript for mobile (same as desktop)
    write_file("templates/mobile/transcript.html", open("templates/desktop/transcript.html").read())

    # -----------------------------
    # 5. Install weasyprint for PDF (optional)
    # -----------------------------
    print("📦 Installing weasyprint for PDF generation...")
    subprocess.run([sys.executable, "-m", "pip", "install", "weasyprint"], check=False)

    # -----------------------------
    # 6. Migrations
    # -----------------------------
    print("🔄 Creating migrations...")
    subprocess.run([sys.executable, "manage.py", "makemigrations", "chakki"], check=True)
    print("🔄 Applying migrations...")
    subprocess.run([sys.executable, "manage.py", "migrate"], check=True)

    print("\n✅ Chakki module rebuild complete!")
    print("👉 Restart server: python manage.py runserver 0.0.0.0:8000")
    print("👉 New features:")
    print("   - Order form with live calculation and custom confirmation modal")
    print("   - Pending/Partial/Completed order lists with search")
    print("   - Order detail with payment entry and completion")
    print("   - Transcript generation (printable HTML)")
    print("   - All mobile-friendly templates")
    print("   - Payments tracking per order")

if __name__ == "__main__":
    main()
