import random
from django.test import TestCase
from .models import Product

class ProductModelUnitTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            product_code=random.randint(111111,000000),
            name='Rice',
            shelf='A01',
            description='Riceberry',
            status=' Fasle',
        )

    def test_product_model(self):
        data = self.product
        self.assertIsInstance(data, Product)