
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
