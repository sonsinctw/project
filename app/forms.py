#forms.py
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        shelf_choices = kwargs.pop('shelf_choices', None)
        super().__init__(*args, **kwargs)
        if shelf_choices:
            self.fields['shelf'].choices = [(choice, choice) for choice in shelf_choices]

    class Meta:
        model = Product
        fields = ['product_code', 'name', 'shelf', 'description', 'status']
        labels = {
            'product_code': 'Product Code',
            'name': 'Name',
            'shelf': 'Shelf',
            'description': 'Description',
            'status': 'Status',
        }
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'shelf': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }
