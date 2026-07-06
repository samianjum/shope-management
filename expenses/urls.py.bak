
from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense_list, name='expense_list'),
    path('add/', views.add_expense, name='add_expense'),
    path('repay/<int:expense_id>/', views.repay_loan, name='repay_loan'),
]
