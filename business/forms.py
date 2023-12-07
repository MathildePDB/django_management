from django import forms
from .models import Customer, Order, Product, OrderDetail
from django.core.exceptions import ValidationError

# customer form
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer

        fields = [
            "first_name", 
            "last_name", 
            "address", 
            "zipcode", 
            "city", 
            "email", 
            "phone_number",
        ]

        labels = {
            "first_name": "Prénom",
            "last_name": "Nom de famille",
            "address": "Adresse",
            "zipcode": "Code postal",
            "city": "Ville",
            "email": "Adresse e-mail",
            "phone_number": "Téléphone",
        }

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        
        # Ajouter des classes CSS aux champs du formulaire
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['address'].widget.attrs.update({'class': 'form-control'})
        self.fields['zipcode'].widget.attrs.update({'class': 'form-control'})
        self.fields['city'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})    

# order form
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order

        fields = [
            "code",
            "customer",
            "payment_method",
        ]

        labels = {
            "code": "Numéro de commande",
            "customer" : "Client",
            "payment_method": "Moyen de paiement", 
        }

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)

        self.fields['code'].widget.attrs.update({'class': 'form-control'})
        self.fields['payment_method'].widget.attrs.update({'class': 'form-select'})

        customers = Customer.objects.all()
        choices = [(customer.id, f"{customer.first_name} {customer.last_name}") for customer in customers]
        self.fields['customer'].widget = forms.Select(choices=choices, attrs={'class': 'form-select'})
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# order_detail form
class OrderDetailForm(forms.ModelForm):
    class Meta:
        model = OrderDetail

        fields = [
            "product",
            "quantity",
        ]

        labels = {
            "product": "Produit",
            "quantity": "Quantité",
        }

    def __init__(self, *args, **kwargs):
        super(OrderDetailForm, self).__init__(*args, **kwargs)
 
        self.fields['quantity'].initial = 1
        self.fields['quantity'].widget.attrs.update({'class': 'form-control'})
        
        products = Product.objects.all()
        choices = [(product.id, str(product)) for product in products]
        self.fields['product'].widget = forms.Select(choices=choices, attrs={'class': 'form-select'})
   
# product form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product

        fields = [
           "name", 
           "description", 
           "price", 
           "stock", 
           "taxe", 
        ]

        labels = {
            "name": "Nom",
            "description" : "description",
            "price": "Prix", 
            "stock": "Stock",
            "taxe": "Taxe",
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['price'].widget.attrs.update({'class': 'form-control'})
        self.fields['stock'].widget.attrs.update({'class': 'form-control'})
        self.fields['taxe'].widget.attrs.update({'class': 'form-select'})

    def clean_price(self):
        price = self.cleaned_data['price']
        if not (0 <= price <= 99999.99):  # adjust the range based on your requirements
            raise ValidationError("Price must be between 0 and 99999.99")
        return int(price * 100)

    def __str__(self):
        return self.name
