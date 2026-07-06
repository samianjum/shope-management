from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Expense, Reminder, Worker, WorkerCategory
from django.db.models import Q

@login_required
def expense_dashboard(request, **kwargs):
    """Expense dashboard with cards and summary."""
    # Summary
    expenses = Expense.objects.all().order_by('-date')
    total_expenses = sum(e.amount for e in expenses)
    total_given = sum(e.amount for e in expenses if e.is_credit and not e.is_repaid)
    total_taken = sum(e.amount for e in expenses if e.category == 'taken_loan' and not e.is_repaid)
    net_balance = total_given - total_taken

    # Counts for cards
    daily_expenses = expenses.filter(category__in=['general','food','medicine','utility','other']).count()
    loans_given = expenses.filter(category='given_loan').count()
    loans_taken = expenses.filter(category='taken_loan').count()
    reminders = Reminder.objects.filter(is_completed=False).count()
    workers = Worker.objects.filter(is_active=True).count()

    context = {
        'total_expenses': total_expenses,
        'total_given': total_given,
        'total_taken': total_taken,
        'net_balance': net_balance,
        'daily_expenses_count': daily_expenses,
        'loans_given_count': loans_given,
        'loans_taken_count': loans_taken,
        'reminders_count': reminders,
        'workers_count': workers,
        'tenant': request.tenant,
    }
    template = 'mobile/expenses.html' if request.mobile else 'desktop/expenses.html'
    return render(request, template, context)

@login_required
def daily_expense_list(request, **kwargs):
    """List daily expenses (non-loan categories)."""
    expenses = Expense.objects.filter(category__in=['general','food','medicine','utility','other']).order_by('-date')
    context = {'expenses': expenses, 'title': 'Daily Expenses', 'tenant': request.tenant}
    template = 'mobile/expense_list.html' if request.mobile else 'desktop/expense_list.html'
    return render(request, template, context)

@login_required
def loan_list(request, loan_type, **kwargs):
    """List loans (given or taken)."""
    if loan_type == 'given':
        expenses = Expense.objects.filter(category='given_loan').order_by('-date')
        title = 'Loans Given'
    else:
        expenses = Expense.objects.filter(category='taken_loan').order_by('-date')
        title = 'Loans Taken'
    context = {'expenses': expenses, 'title': title, 'loan_type': loan_type, 'tenant': request.tenant}
    template = 'mobile/expense_list.html' if request.mobile else 'desktop/expense_list.html'
    return render(request, template, context)

# ---- Reminder Views ----
@login_required
def reminder_list(request, **kwargs):
    reminders = Reminder.objects.all().order_by('remind_date')
    context = {'reminders': reminders, 'tenant': request.tenant}
    template = 'mobile/reminder_list.html' if request.mobile else 'desktop/reminder_list.html'
    return render(request, template, context)

@login_required
def add_reminder(request, **kwargs):
    if request.method == 'POST':
        title = request.POST.get('title')
        notes = request.POST.get('notes', '')
        remind_date = request.POST.get('remind_date')
        if title and remind_date:
            Reminder.objects.create(
                title=title,
                notes=notes,
                remind_date=remind_date,
            )
            messages.success(request, "Reminder added!")
            return redirect('reminder_list', schema_name=request.tenant.schema_name)
    template = 'mobile/add_reminder.html' if request.mobile else 'desktop/add_reminder.html'
    return render(request, template)

@login_required
def complete_reminder(request, reminder_id, **kwargs):
    reminder = get_object_or_404(Reminder, id=reminder_id)
    reminder.is_completed = True
    reminder.save()
    messages.success(request, "Reminder marked as done.")
    return redirect('reminder_list', schema_name=request.tenant.schema_name)

# ---- Worker Views ----
@login_required
def worker_list(request, **kwargs):
    workers = Worker.objects.all().order_by('-created_at')
    categories = WorkerCategory.objects.all()
    context = {'workers': workers, 'categories': categories, 'tenant': request.tenant}
    template = 'mobile/worker_list.html' if request.mobile else 'desktop/worker_list.html'
    return render(request, template, context)

@login_required
def add_worker(request, **kwargs):
    categories = WorkerCategory.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        if not name:
            messages.error(request, "Name is required.")
            return redirect('add_worker', schema_name=request.tenant.schema_name)
        Worker.objects.create(
            name=name,
            father_name=request.POST.get('father_name', ''),
            cnic=request.POST.get('cnic', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            joining_date=request.POST.get('joining_date'),
            resignation_date=request.POST.get('resignation_date') or None,
            status=request.POST.get('status', 'active'),
            salary_type=request.POST.get('salary_type', 'monthly'),
            salary_amount=request.POST.get('salary_amount', 0),
            category_id=request.POST.get('category') or None,
        )
        messages.success(request, f"Worker {name} added!")
        return redirect('worker_list', schema_name=request.tenant.schema_name)
    context = {'categories': categories, 'tenant': request.tenant}
    template = 'mobile/add_worker.html' if request.mobile else 'desktop/add_worker.html'
    return render(request, template)

@login_required
def add_worker_category(request, **kwargs):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            WorkerCategory.objects.create(name=name, description=request.POST.get('description', ''))
            messages.success(request, f"Category '{name}' added.")
        else:
            messages.error(request, "Category name required.")
        return redirect('worker_list', schema_name=request.tenant.schema_name)
    template = 'mobile/add_worker_category.html' if request.mobile else 'desktop/add_worker_category.html'
    return render(request, template)

@login_required
def edit_worker(request, worker_id, **kwargs):
    worker = get_object_or_404(Worker, id=worker_id)
    categories = WorkerCategory.objects.all()
    if request.method == 'POST':
        worker.name = request.POST.get('name', worker.name)
        worker.father_name = request.POST.get('father_name', worker.father_name)
        worker.cnic = request.POST.get('cnic', worker.cnic)
        worker.phone = request.POST.get('phone', worker.phone)
        worker.address = request.POST.get('address', worker.address)
        worker.joining_date = request.POST.get('joining_date', worker.joining_date)
        worker.resignation_date = request.POST.get('resignation_date') or None
        worker.status = request.POST.get('status', worker.status)
        worker.salary_type = request.POST.get('salary_type', worker.salary_type)
        worker.salary_amount = request.POST.get('salary_amount', worker.salary_amount)
        worker.category_id = request.POST.get('category') or None
        worker.save()
        messages.success(request, "Worker updated!")
        return redirect('worker_list', schema_name=request.tenant.schema_name)
    context = {'worker': worker, 'categories': categories, 'tenant': request.tenant}
    template = 'mobile/edit_worker.html' if request.mobile else 'desktop/edit_worker.html'
    return render(request, template)

# Keep the old add_expense and repay_loan for now, but we can redirect them.
@login_required
def add_expense(request, **kwargs):
    # Redirect to a unified add page or keep as is.
    # For simplicity, we'll keep the old add expense.
    if request.method == 'POST':
        expense = Expense(
            title=request.POST.get('title'),
            amount=request.POST.get('amount'),
            category=request.POST.get('category'),
            description=request.POST.get('description', ''),
            is_credit=request.POST.get('is_credit') == 'on',
            person_name=request.POST.get('person_name', ''),
            due_date=request.POST.get('due_date') or None,
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            notes=request.POST.get('notes', ''),
            reason=request.POST.get('reason', ''),
        )
        expense.save()
        messages.success(request, "Expense added!")
        return redirect('expense_dashboard', schema_name=request.tenant.schema_name)
    template = 'mobile/add_expense.html' if request.mobile else 'desktop/add_expense.html'
    return render(request, template)

@login_required
def repay_loan(request, expense_id, **kwargs):
    expense = get_object_or_404(Expense, id=expense_id)
    if expense.is_credit or expense.category == 'taken_loan':
        expense.is_repaid = True
        expense.save()
        messages.success(request, f"Loan {expense.title} marked as repaid.")
    else:
        messages.error(request, "This is not a loan entry.")
    return redirect('expense_dashboard', schema_name=request.tenant.schema_name)
