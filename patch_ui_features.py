#!/usr/bin/env python3
import os
import re
import shutil

BASE_DIR = os.getcwd()

def write_file(path, content):
    path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Updated: {path}")

def main():
    print("🚀 Applying UI/UX improvements...")

    # ---------- 1. Update Desktop Base Template ----------
    desktop_base = '''
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}SaaS System{% endblock %}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #f8f9fa; }
        .sidebar { 
            background: #2c3e50; 
            min-height: 100vh; 
            transition: all 0.3s;
            padding-top: 20px;
        }
        .sidebar .nav-link {
            color: #ecf0f1;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 2px 10px;
            display: flex;
            align-items: center;
        }
        .sidebar .nav-link:hover {
            background: #34495e;
        }
        .sidebar .nav-link i {
            width: 25px;
            font-size: 1.1rem;
        }
        .sidebar .nav-link .badge {
            margin-left: auto;
            background: #e74c3c;
        }
        .sidebar .nav-item .dropdown-menu {
            background: #34495e;
            border: none;
        }
        .sidebar .nav-item .dropdown-menu a {
            color: #ecf0f1;
            padding: 8px 20px;
        }
        .sidebar .nav-item .dropdown-menu a:hover {
            background: #2c3e50;
        }
        .sidebar .nav-item .dropdown-menu .badge {
            background: #f39c12;
            float: right;
        }
        .sidebar .collapse-toggle {
            cursor: pointer;
        }
        .header {
            background: white;
            border-bottom: 1px solid #dee2e6;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header .search-box {
            width: 300px;
        }
        .header .notifications {
            position: relative;
            cursor: pointer;
        }
        .header .notifications .badge {
            position: absolute;
            top: -5px;
            right: -10px;
            background: #e74c3c;
            border-radius: 50%;
            font-size: 0.7rem;
            padding: 3px 6px;
        }
        .header .notifications .dropdown-menu {
            min-width: 300px;
            max-height: 400px;
            overflow-y: auto;
        }
        .main-content {
            padding: 20px;
        }
        .sidebar-toggle {
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            margin-left: 10px;
        }
        @media (max-width: 768px) {
            .sidebar {
                min-height: auto;
                width: 100%;
            }
            .header .search-box {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <nav class="col-md-2 d-md-block sidebar">
                <div class="d-flex justify-content-between align-items-center">
                    <h4 class="text-white ms-3">{{ tenant.name|default:"SaaS" }}</h4>
                    <button class="sidebar-toggle d-md-none" type="button" data-bs-toggle="collapse" data-bs-target="#sidebarCollapse">
                        <i class="fas fa-bars"></i>
                    </button>
                </div>
                <div class="collapse d-md-block" id="sidebarCollapse">
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link" href="/portal/{{ tenant.schema_name }}/dashboard/">
                                <i class="fas fa-tachometer-alt"></i> Dashboard
                            </a>
                        </li>
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="chakkiDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="fas fa-wheat-awn"></i> Chakki
                            </a>
                            <ul class="dropdown-menu" aria-labelledby="chakkiDropdown">
                                <li><a class="dropdown-item" href="/portal/{{ tenant.schema_name }}/chakki/orders/pending/">
                                    Pending <span class="badge bg-danger rounded-pill">{{ pending_count }}</span>
                                </a></li>
                                <li><a class="dropdown-item" href="/portal/{{ tenant.schema_name }}/chakki/orders/ready/">
                                    Ready <span class="badge bg-warning rounded-pill">{{ ready_count }}</span>
                                </a></li>
                                <li><a class="dropdown-item" href="/portal/{{ tenant.schema_name }}/chakki/orders/partial/">
                                    Partial Paid <span class="badge bg-info rounded-pill">{{ partial_count }}</span>
                                </a></li>
                                <li><a class="dropdown-item" href="/portal/{{ tenant.schema_name }}/chakki/orders/completed/">
                                    Completed <span class="badge bg-success rounded-pill">{{ completed_count }}</span>
                                </a></li>
                            </ul>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/portal/{{ tenant.schema_name }}/expenses/">
                                <i class="fas fa-money-bill-wave"></i> Expenses
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/portal/{{ tenant.schema_name }}/chakki/settings/">
                                <i class="fas fa-cog"></i> Settings
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/portal/{{ tenant.schema_name }}/logout/">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a>
                        </li>
                    </ul>
                </div>
            </nav>

            <!-- Main Content -->
            <main class="col-md-10 ms-sm-auto px-md-4">
                <!-- Header -->
                <div class="header">
                    <div>
                        <button class="btn btn-outline-secondary d-md-none" type="button" data-bs-toggle="collapse" data-bs-target="#sidebarCollapse">
                            <i class="fas fa-bars"></i>
                        </button>
                    </div>
                    <div class="search-box">
                        <form action="/portal/{{ tenant.schema_name }}/search/" method="get" class="d-flex">
                            <input class="form-control me-2" type="search" name="q" placeholder="Search orders, customers..." aria-label="Search">
                            <button class="btn btn-outline-secondary" type="submit"><i class="fas fa-search"></i></button>
                        </form>
                    </div>
                    <div class="notifications dropdown">
                        <i class="fas fa-bell fa-lg" data-bs-toggle="dropdown" aria-expanded="false"></i>
                        <span class="badge bg-danger" id="notif-count">{{ ready_count }}</span>
                        <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="notificationDropdown">
                            <li><h6 class="dropdown-header">Ready Orders</h6></li>
                            {% if ready_orders %}
                                {% for order in ready_orders %}
                                    <li><a class="dropdown-item" href="/portal/{{ tenant.schema_name }}/chakki/order/{{ order.id }}/">
                                        Order #{{ order.id }} - {{ order.customer.name }}
                                    </a></li>
                                {% endfor %}
                            {% else %}
                                <li><span class="dropdown-item text-muted">No ready orders</span></li>
                            {% endif %}
                        </ul>
                    </div>
                </div>

                <!-- Page Content -->
                <div class="main-content">
                    {% if messages %}
                        {% for m in messages %}
                            <div class="alert alert-info alert-dismissible fade show">{{ m }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>
                        {% endfor %}
                    {% endif %}
                    {% block content %}{% endblock %}
                </div>
            </main>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Auto-update notification count from server (optional, we can just rely on page load)
        // For real-time, we could use polling but we'll keep it simple.
    </script>
</body>
</html>
'''
    write_file("templates/desktop/base.html", desktop_base)

    # ---------- 2. Update Chakki Dashboard (remove KPI cards) ----------
    chakki_dashboard_desktop = '''
{% extends "desktop/base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h2>🌾 Chakki Dashboard</h2>
    <a href="/portal/{{ tenant.schema_name }}/chakki/add/" class="btn btn-primary">+ New Order</a>
</div>
<div class="row">
    <div class="col-md-12">
        <a href="/portal/{{ tenant.schema_name }}/chakki/orders/pending/" class="btn btn-outline-primary me-2">Pending <span class="badge bg-primary">{{ pending }}</span></a>
        <a href="/portal/{{ tenant.schema_name }}/chakki/orders/ready/" class="btn btn-outline-warning me-2">Ready <span class="badge bg-warning">{{ ready }}</span></a>
        <a href="/portal/{{ tenant.schema_name }}/chakki/orders/partial/" class="btn btn-outline-info me-2">Partial <span class="badge bg-info">{{ partial }}</span></a>
        <a href="/portal/{{ tenant.schema_name }}/chakki/orders/completed/" class="btn btn-outline-success">Completed <span class="badge bg-success">{{ completed }}</span></a>
    </div>
</div>
<h4 class="mt-4">Recent Orders</h4>
<table class="table table-bordered table-hover">
    <thead>
        <tr><th>ID</th><th>Customer</th><th>KG</th><th>Total</th><th>Paid</th><th>Status</th><th>Ready</th><th>Action</th></tr>
    </thead>
    <tbody>
    {% for o in recent_orders %}
    <tr>
        <td>{{ o.id }}</td>
        <td>{{ o.customer.name }}</td>
        <td>{{ o.total_kg }}</td>
        <td>₹{{ o.total_amount }}</td>
        <td>₹{{ o.amount_paid }}</td>
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
    <tr><td colspan="8" class="text-center">No orders yet.</td></tr>
    {% endfor %}
    </tbody>
</table>
{% endblock %}
'''
    write_file("templates/desktop/chakki_dashboard.html", chakki_dashboard_desktop)

    # ---------- 3. Update Order List View to support 'ready' type ----------
    # We'll modify chakki/views.py: add 'ready' to order_list logic.
    views_path = "chakki/views.py"
    with open(views_path, 'r') as f:
        views_content = f.read()
    # Replace the order_list function to include 'ready' filter.
    # Find the block that handles order_type and add 'ready'.
    # We'll use regex to replace the function.
    import re
    pattern = r"def order_list\(request, order_type, \*\*kwargs\):.*?(?=\n@login_required|\n\Z)"
    replacement = '''
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
'''
    # Use DOTALL to match across lines
    views_content = re.sub(pattern, replacement, views_content, flags=re.DOTALL)
    write_file(views_path, views_content)
    print("✅ Updated chakki/views.py to support 'ready' order_type.")

    # ---------- 4. Update Dashboard view to pass counts and ready orders to context ----------
    # We need to add 'pending_count', 'ready_count', etc. to the context for base template.
    # In dashboard, we already have pending, ready, completed, partial. We'll add those to context.
    # But base template expects variables like pending_count, ready_count, partial_count, completed_count, ready_orders.
    # We'll modify the dashboard view in chakki/views.py to include these in context.
    # We'll also add ready_orders list.
    # Let's patch the dashboard function.
    pattern_dash = r"def dashboard\(request, \*\*kwargs\):.*?(?=\n@login_required|\n\Z)"
    replacement_dash = '''
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
'''
    views_content = re.sub(pattern_dash, replacement_dash, views_content, flags=re.DOTALL)
    write_file(views_path, views_content)
    print("✅ Updated dashboard view with counts and ready orders.")

    # ---------- 5. Update order_list template to show status filter tabs ----------
    # Not required, but we can add quick links in the order_list template.
    # We'll keep it simple for now.

    # ---------- 6. Update mobile base template similarly (optional, but we'll copy desktop base for mobile) ----------
    # We'll copy the new desktop base to mobile base with minor adjustments.
    mobile_base = desktop_base.replace('SaaS System', 'SaaS')
    mobile_base = mobile_base.replace('col-md-2', 'col-12')
    mobile_base = mobile_base.replace('d-md-block', 'd-block')
    mobile_base = mobile_base.replace('col-md-10', 'col-12')
    # Remove the header search and notification for mobile? We'll keep them but adjust.
    write_file("templates/mobile/base.html", mobile_base)
    print("✅ Updated mobile base template.")

    # ---------- 7. Update mobile dashboard (remove KPI) ----------
    chakki_dashboard_mobile = '''
{% extends "mobile/base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h3>🌾 Chakki</h3>
    <a href="/portal/{{ tenant.schema_name }}/chakki/add/" class="btn btn-primary btn-sm">+ Order</a>
</div>
<div class="row text-center">
    <div class="col-3"><a href="/portal/{{ tenant.schema_name }}/chakki/orders/pending/" class="btn btn-outline-primary btn-sm w-100">Pending<br><span class="badge bg-primary">{{ pending }}</span></a></div>
    <div class="col-3"><a href="/portal/{{ tenant.schema_name }}/chakki/orders/ready/" class="btn btn-outline-warning btn-sm w-100">Ready<br><span class="badge bg-warning">{{ ready }}</span></a></div>
    <div class="col-3"><a href="/portal/{{ tenant.schema_name }}/chakki/orders/partial/" class="btn btn-outline-info btn-sm w-100">Partial<br><span class="badge bg-info">{{ partial }}</span></a></div>
    <div class="col-3"><a href="/portal/{{ tenant.schema_name }}/chakki/orders/completed/" class="btn btn-outline-success btn-sm w-100">Done<br><span class="badge bg-success">{{ completed }}</span></a></div>
</div>
<h5 class="mt-3">Recent Orders</h5>
{% for o in recent_orders %}
<div class="card mb-2">
    <div class="card-body p-2">
        <b>#{{ o.id }} {{ o.customer.name }}</b> - {{ o.total_kg }}kg | ₹{{ o.total_amount }}<br>
        <small>Ready: {{ o.ready_time|date:"d M H:i" }} | Status: {{ o.status }}</small>
        <a href="/portal/{{ tenant.schema_name }}/chakki/order/{{ o.id }}/" class="btn btn-sm btn-primary float-end">View</a>
    </div>
</div>
{% empty %}
<p class="text-muted">No recent orders</p>
{% endfor %}
{% endblock %}
'''
    write_file("templates/mobile/chakki_dashboard.html", chakki_dashboard_mobile)

    # ---------- 8. Add a search view (optional) – we'll add a placeholder view that redirects to order_list with search ----------
    # We'll add a search URL in chakki/urls.py that redirects to order_list with search param.
    # Actually we already have search in order_list via GET parameter, so the form action in header can point to that.
    # So no extra view needed.

    print("\n✅ UI improvements applied successfully!")
    print("👉 Restart server: python manage.py runserver 0.0.0.0:8000")
    print("👉 Changes:")
    print("   - Sidebar now collapsible, with dropdown for Chakki showing counts")
    print("   - Header has search bar and notification bell (shows ready orders count)")
    print("   - Dashboard KPI cards removed; only order summary and recent orders")
    print("   - Ready orders now have their own page (/chakki/orders/ready/)")
    print("   - Notification dropdown shows ready orders")

if __name__ == "__main__":
    main()
