#!/usr/bin/env python3
import os
import re

BASE_DIR = os.getcwd()

def write_file(path, content):
    path = os.path.join(BASE_DIR, path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Updated: {path}")

def main():
    print("🔧 Fixing ChakkiOrder.save() method...")

    models_path = "chakki/models.py"
    with open(models_path, 'r') as f:
        content = f.read()

    # Find the ChakkiOrder.save method and replace it
    old_save = r'def save\(self, \*args, \*\*kwargs\):.*?(?=\n    def __str__|\nclass |\Z)'
    new_save = '''
    def save(self, *args, **kwargs):
        # Recalculate total from items only if this is an existing record
        if self.pk:
            total = sum(item.item_total for item in self.items.all())
            self.total_amount = total
        # For new orders, total_amount remains as default (0) until items are added
        # Determine payment status
        if self.amount_paid == 0:
            self.payment_status = 'unpaid'
        elif self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
            self.amount_paid = self.total_amount
        else:
            self.payment_status = 'partial'
        super().save(*args, **kwargs)
'''
    content = re.sub(old_save, new_save, content, flags=re.DOTALL)
    write_file(models_path, content)
    print("✅ ChakkiOrder.save() updated.")

    print("\n✅ Fix applied. Restart server: python manage.py runserver 0.0.0.0:8000")

if __name__ == "__main__":
    main()
