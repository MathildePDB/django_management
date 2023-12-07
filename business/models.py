from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Customer(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    address = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=6)
    city = models.CharField(max_length=30)
    email = models.EmailField()
    phone_number = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)

class Product(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    TAXE_CHOICES = (
        (0.055, "5.5%"),
        (0.1, "10%"),
        (0.2, "20%"),
    )
    taxe = models.FloatField(choices=TAXE_CHOICES, default=0.2)

    def formatted_price(self):
        return f'{self.price / 100:.2f}€'
    
    def get_taxe_display(self):
        return dict(self.TAXE_CHOICES)[self.taxe]
    
    def unit_price_with_tax(self):
        return f'{(self.price) * (self.taxe * self.price) / 100:.2f}'
    
    def __str__(self):
        return f"{self.name} - {self.formatted_price}"
    
    @property
    def formatted_price(self):
        return f"{self.price / 100:.2f}€"

class Image(models.Model):
    name = models.CharField(max_length=30)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

class Order(models.Model):
    code = models.CharField(max_length=20)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    payment_method = models.JSONField(
        default=list,
        choices=[
            ("card", "Carte bancaire"), 
            ("transfer", "Virement bancaire"), 
            ("other", "Autre")
        ]
    )
    is_valid = models.BooleanField(default=False)

class OrderDetail(models.Model):
    product =  models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def subtotal_with_tax(self):
        price = Decimal(str(self.product.price))
        tax_rate = Decimal(str(self.product.taxe))
        subtotal = ((price / 100) + (tax_rate * (price / 100))) * self.quantity
        return Decimal(subtotal)
    
    def subtotal_ht(self):
        return Decimal(str(self.product.price / 100)) * self.quantity
