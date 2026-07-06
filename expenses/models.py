from django.db import models
from django.utils import timezone

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('medicine', 'Medicine'),
        ('food', 'Food'),
        ('utility', 'Utility'),
        ('given_loan', 'Given Loan (Udhaar)'),
        ('taken_loan', 'Taken Loan'),
        ('other', 'Other'),
    ]
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    description = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)          # creation timestamp
    expense_date = models.DateField(default=timezone.now)   # date the expense occurred
    is_credit = models.BooleanField(default=False, help_text="Money given to someone (receivable)")
    person_name = models.CharField(max_length=100, blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_repaid = models.BooleanField(default=False, help_text="Mark if loan is repaid")
    phone = models.CharField(max_length=20, blank=True, help_text="Contact number")
    address = models.TextField(blank=True, help_text="Address of person")
    notes = models.TextField(blank=True, help_text="Additional notes")
    reason = models.CharField(max_length=200, blank=True, help_text="Reason for transaction")

    def __str__(self):
        return f"{self.title} - {self.amount}"
