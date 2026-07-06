from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense_dashboard, name='expense_dashboard'),
    path('add/', views.add_expense, name='add_expense'),
    path('repay/<int:expense_id>/', views.repay_loan, name='repay_loan'),
    path('daily/', views.daily_expense_list, name='daily_expense_list'),
    path('loans/<str:loan_type>/', views.loan_list, name='loan_list'),
    path('reminders/', views.reminder_list, name='reminder_list'),
    path('reminders/add/', views.add_reminder, name='add_reminder'),
    path('reminders/complete/<int:reminder_id>/', views.complete_reminder, name='complete_reminder'),
    path('workers/', views.worker_list, name='worker_list'),
    path('workers/add/', views.add_worker, name='add_worker'),
    path('workers/edit/<int:worker_id>/', views.edit_worker, name='edit_worker'),
    path('workers/category/add/', views.add_worker_category, name='add_worker_category'),
]