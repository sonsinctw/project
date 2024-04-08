# models.py
from django.db import models
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File

class Product(models.Model):
    product_code = models.CharField(max_length = 10, unique=True)
    name = models.CharField(max_length=50)
    SHELF_CHOICES = [
        ('A01', 'A01'),
        ('A02', 'A02'),
        ('A03', 'A03'),
        ('B01', 'B01'),
        ('B02', 'B02'),
        ('B03', 'B03'),
    ]
    shelf = models.CharField(max_length=3, choices=SHELF_CHOICES, unique=True)
    description = models.CharField(max_length=100)
    status = models.BooleanField(default=False)
    barcode = models.ImageField(upload_to='images/', blank=True)
    nodeMCU_ip = models.CharField(max_length=15) 

    def __str__(self):
        return self.name

    def generate_barcode(self):
        barcode_value = self.product_code
        code128 = barcode.Code128(barcode_value, writer=ImageWriter())
        buffer = BytesIO()
        code128.write(buffer)
        filename = f'barcode_{barcode_value}.png'
        self.barcode.save(filename, File(buffer), save=False)
        buffer.close()

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.generate_barcode()
        super().save(*args, **kwargs)
        
        
from django.utils import timezone

class HistoryEntry(models.Model):
    ACTION_CHOICES = [
        ('add', 'Add'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('put_away', 'Put Away'),
        ('picking', 'Picking'),
        ('move', 'Move'),
        ('status_update', 'Status Update'), 
        ('shelf_update', 'Shelf Update'),   
    ]
    
    date = models.DateTimeField(default=timezone.now)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    product_code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.date} - {self.action} - {self.product_code}"
