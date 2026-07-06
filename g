#!/usr/bin/env python3
import os
import re
import subprocess

BASE_DIR = os.getcwd()

def write_file(path, content):
    path = os.path.join(BASE_DIR, path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Updated: {path}")

def main():
    print("🔥 Applying final order status fix...")

    # ---------- 1. Update models.py ----------
    models_path = "chakki/models.py"
    with open(models_path, 'r') as f:
        models_content = f.read()

    # Replace the ChakkiOrder.save() method
    old_save = r'def save\(self, \*args, \*\*kwargs\):.*?(?=\n    def __str__|\nclass |\Z)'
    new_save = '''
    def save(self, *args, **kwargs):
        # Recalculate total from items only if this is an existing record
        if self.pk:
            total = sum(item.item_total for item in self.items.all())
            self.total_amount = total
        else:
            # For new orders, total_amount remains as default (0) until items are added
            pass

        # Determine payment status and update order status accordingly
        if self.amount_paid == 0:
            self.payment_status = 'unpaid'
            # Don't change status here; auto-ready will handle it
        elif self.total_amount > 0 and self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
            self.amount_paid = self.total_amount
            self.status = 'completed'
            self.completed_at = timezone.now()
        else:
            self.payment_status = 'partial'
            # If it was ready, move it back to pending (or keep as pending)
            if self.status == 'ready':
                self.status = 'pending'

        super().save(*args, **kwargs)
'''
    models_content = re.sub(old_save, new_save, models_content, flags=re.DOTALL)
    write_file(models_path, models_content)
    print("✅ Updated ChakkiOrder.save() with status logic.")

    # ---------- 2. Update views.py ----------
    views_path = "chakki/views.py"
    with open(views_path, 'r') as f:
        views_content = f.read()

    # Fix order_list filters: exclude partial from pending and ready
    # Replace the block for pending and ready
    views_content = views_content.replace(
        "if order_type == 'pending':\n        orders = orders.filter(status='pending')",
        "if order_type == 'pending':\n        orders = orders.filter(status='pending').exclude(payment_status='partial')"
    )
    views_content = views_content.replace(
        "elif order_type == 'ready':\n        orders = orders.filter(status='ready').exclude(payment_status='partial')",
        "elif order_type == 'ready':\n        orders = orders.filter(status='ready').exclude(payment_status='partial').exclude(payment_status='paid')"
    )

    # Fix dashboard auto-ready: only unpaid orders
    views_content = views_content.replace(
        "pending_orders = ChakkiOrder.objects.filter(status='pending', amount_paid=0)",
        "pending_orders = ChakkiOrder.objects.filter(status='pending', payment_status='unpaid')"
    )

    # Remove duplicate messages.info line (if any)
    views_content = re.sub(r'order\.save\(\)\s+ messages\.info\(request, f"Order #\{order\.id\} for \{order\.customer\.name\} is READY!"\)', 'order.save()', views_content)

    write_file(views_path, views_content)
    print("✅ Updated views: filters and auto-ready fixed.")

    # ---------- 3. Create data migration to fix existing orders ----------
    migration_code = '''
# Generated migration to fix existing orders
from django.db import migrations
from django.utils import timezone

def fix_orders(apps, schema_editor):
    ChakkiOrder = apps.get_model('chakki', 'ChakkiOrder')
    for order in ChakkiOrder.objects.all():
        if order.total_amount == 0:
            # If no items, maybe delete? We'll keep but set amount_paid=0 and status='pending'
            order.amount_paid = 0
            order.payment_status = 'unpaid'
            if order.status != 'completed':
                order.status = 'pending'
        elif order.amount_paid >= order.total_amount:
            order.payment_status = 'paid'
            order.amount_paid = order.total_amount
            order.status = 'completed'
            if not order.completed_at:
                order.completed_at = timezone.now()
        elif order.amount_paid > 0:
            order.payment_status = 'partial'
            if order.status == 'ready':
                order.status = 'pending'
        # If unpaid, keep as is
        order.save()

class Migration(migrations.Migration):
    dependencies = [
        ('chakki', '0003_chakkicategory_remove_chakkiorder_cleaning_charges_and_more'),
    ]
    operations = [
        migrations.RunPython(fix_orders),
    ]
'''
    migration_dir = "chakki/migrations"
    os.makedirs(migration_dir, exist_ok=True)
    # Find next migration number
    existing = [f for f in os.listdir(migration_dir) if f.startswith('000') and f.endswith('.py')]
    nums = [int(f.split('_')[0]) for f in existing if f.split('_')[0].isdigit()]
    next_num = max(nums) + 1 if nums else 4
    migration_file = os.path.join(migration_dir, f'{next_num:04d}_fix_order_status.py')
    with open(migration_file, 'w') as f:
        f.write(migration_code)
    print(f"✅ Created data migration: {migration_file}")

    # ---------- 4. Run migrations ----------
    print("🔄 Running migrations to fix existing orders...")
    subprocess.run([sys.executable, "manage.py", "makemigrations", "chakki"], check=False)
    subprocess.run([sys.executable, "manage.py", "migrate", "chakki"], check=True)

    print("\n✅ All fixes applied successfully!")
    print("👉 Restart server: python manage.py runserver 0.0.0.0:8000")
    print("👉 Changes:")
    print("   - Full paid orders now auto-complete (status='completed').")
    print("   - Partial paid orders are excluded from pending and ready lists.")
    print("   - Data migration fixes existing orders.")

if __name__ == "__main__":
    main()
