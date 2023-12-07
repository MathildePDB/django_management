from django.contrib import admin
from .models import Customer, Product, Image, Order, OrderDetail

admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Image)
admin.site.register(Order)
admin.site.register(OrderDetail)
