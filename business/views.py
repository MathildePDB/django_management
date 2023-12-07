from .models import Customer, Order, OrderDetail, Product
from .forms import CustomerForm, OrderForm, ProductForm, OrderDetailForm
from io import BytesIO
from django.views import View
from django.db import transaction
from django.db.models import Count, Case, When, FloatField, Sum
from django.db.models.functions import TruncMonth
from django.contrib import messages
from django.core.serializers import serialize
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.platypus import Table
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import requests
import json
import pytz

# dashbord
def dashbord(request):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        # Récupérez les données agrégées par mois directement dans une liste de dictionnaires
        orders_data = (
            Order.objects.all()
            .annotate(month=TruncMonth('created_at', tzinfo=pytz.UTC))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        # Créez un dictionnaire pour stocker les données de chaque mois
        data_dict = {order['month']: order['count'] for order in orders_data}

        # Récupérez tous les mois de l'année
        all_months = [
            datetime(year=2023, month=month, day=1, tzinfo=pytz.UTC)
            for month in range(1, 13)
        ]

        # Préparez les données pour le rendu dans le template
        data_labels = [month.strftime('%B') for month in all_months]
        data_values = [data_dict.get(month, 0) for month in all_months]

        # Récupérez les commandes pour chaque client
        orders_by_customer = (
            Order.objects.all()
            .values('customer__id', 'customer__first_name', 'customer__last_name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Préparez les données pour le graphique des commandes par client
        customers_data = [
            {
                'id': order['customer__id'], 
                'count': order['count'],
                'first_name': order['customer__first_name'],
                'last_name': order['customer__last_name'],
            } for order in orders_by_customer
        ]

        # Convertissez la liste en chaîne JSON
        customers_data_json = json.dumps(customers_data)

        # Récupérez les quantité de produits vendus dans toutes les commandes
        products_sold = (
            OrderDetail.objects.all()
            .values('product__name', 'quantity')
            .annotate(count=Count('product_id'))
            .order_by('-count')
        )

        # Préparez les données pour le graphique des produits vendus
        products_data = [
            {
                'name': product['product__name'],
                'count': product['count'],
                'quantity': product['quantity'],
            } for product in products_sold
        ]

        # convertissez la liste en chaîne JSON
        products_data_json = json.dumps(products_data)

        # Récupérez la ville des clients
        customers_for_map = Customer.objects.all()

        # Créer une liste pour stocker les données des clients avec les informations nécessaires pour la carte
        customer_list_for_map = []

        for customer in customers_for_map:
            # Appeler la fonction pour obtenir les coordonnées à partir du nom de la ville
            coordinates = get_coordinates(customer.city)

            # Ajouter les données du client à la liste
            customer_list_for_map.append({
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'city': customer.city,
                'coordinates': coordinates,
            })

        # convertissez la liste en chaîne JSON
        customers_map_json = json.dumps(customer_list_for_map)

        # Récupérer les informations sur chaque commande pour chaque client
        orders_data = Order.objects.values('id', 'customer__first_name', 'customer__last_name', 'is_valid')

        # Calculer le nombre total de commandes, de commandes valides et de commandes non valides pour chaque client
        customer_data_list = Customer.objects.annotate(
            total_orders=Count('order'),
            valid_orders=Count(Case(When(order__is_valid=True, then=1), default=None, output_field=FloatField())),
            invalid_orders=Count(Case(When(order__is_valid=False, then=1), default=None, output_field=FloatField())),
        ).values('id', 'first_name', 'last_name', 'total_orders', 'valid_orders', 'invalid_orders')

        # Convertir les données pour qu'elles soient lisibles
        customer_data_list = list(customer_data_list)
        customer_data_list_json = json.dumps(customer_data_list)
        
        # Calculer la somme de toutes les commandes
        total_sum = Order.objects.aggregate(total_sum=Sum('id'))['total_sum']

        # Calculer la somme de toutes les commandes pour lesquelles is_valid=true
        valid_sum = Order.objects.filter(is_valid=True).aggregate(valid_sum=Sum('id'))['valid_sum']

        # Calculer la somme de toutes les commandes pour lesquelles is_valid=false
        invalid_sum = Order.objects.filter(is_valid=False).aggregate(invalid_sum=Sum('id'))['invalid_sum']

        # Convertir Decimal en float
        total_sum = float(total_sum) if total_sum is not None else None
        valid_sum = float(valid_sum) if valid_sum is not None else None
        invalid_sum = float(invalid_sum) if invalid_sum is not None else None

        # Ajouter les valeurs à la liste
        order_data_all_list = [total_sum, valid_sum, invalid_sum]

        # Convertir la liste en JSON
        order_data_all_json = json.dumps(order_data_all_list)

        # contexte à retourner
        context = {
            'orders': orders_data,
            'data_labels': json.dumps(data_labels),
            'data_values': json.dumps(data_values),
            'customers_data_json': customers_data_json,
            'products_data_json': products_data_json,
            'customers_map_json': customers_map_json,
            'customer_data_list_json': customer_data_list_json,
            'order_data_all_json': order_data_all_json,
        }

        return render(request, "business/home/index.html", context)
    else:
        return redirect("index")

# Fonction pour obtenir les coordonnées à partir du nom de la ville
def get_coordinates(city_name):
    # Construire l'URL du service de géocodage
    geocoding_url = f'https://nominatim.openstreetmap.org/search?format=json&q={city_name}'

    # Effectuer une requête HTTP pour obtenir les coordonnées
    response = requests.get(geocoding_url)
    data = response.json()

    # Vérifier si des résultats ont été obtenus
    if data and data[0].get('lat') and data[0].get('lon'):
        # Récupérer les coordonnées du premier résultat
        latitude = float(data[0]['lat'])
        longitude = float(data[0]['lon'])
        return {'latitude': latitude, 'longitude': longitude}
    else:
        return None

# list of customers
def listCustomer(request):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        # Récupérer les données pour un utilisateur admin
        is_business_admin = request.user.groups.filter(name="Business_admin").exists()

        # Filtrer les données suivant le groupe de l'utilisateur
        if request.user.groups.filter(name="Business_user").exists():
            customers = Customer.objects.filter(user=request.user)
        elif request.user.groups.filter(name="Business_admin").exists():
            customers = Customer.objects.all()
        else:
            customers = []
        
        # Pagination
        paginator = Paginator(customers, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return render(
            request, 
            'business/customer/customer_list.html', 
            {
                'is_business_admin': is_business_admin,
                'page_obj': page_obj,
            }
        )
    else:
        return redirect("index")

# add customer
def addCustomer(request):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        # Vérirfications pour l'ajout d'un client
        if request.method == "POST":
            form = CustomerForm(request.POST)

            if form.is_valid():
                form.instance.user = request.user
                form.save()
                messages.success(request, f"Client supprimé avec succès.")
                return redirect("customers")
        else:
            form = CustomerForm()

        return render(request, "business/customer/customer_form.html", {"form": form})
    else:
        return redirect("index")

# detail customer
def detailCustomer(request, customer_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        # Récupération des données de commandes nécessaires
        customer = get_object_or_404(Customer, id=customer_id)
        is_business_admin = request.user.groups.filter(name="Business_admin").exists()
        orders = Order.objects.filter(customer=customer)
        estimates = orders.filter(is_valid=False)
        bills = orders.filter(is_valid=True)

        # Sécurisation de l'accès aux données pour l'admin
        if is_business_admin or (request.user == customer.user):
            return render(
                request, 
                "business/customer/customer_detail.html", 
                {
                    "customer": customer, 
                    "is_business_admin": is_business_admin, 
                    "estimates": estimates, 
                    "bills": bills,
                }
            )
        else:
            # message d'eereur : accès refusé
            return render(request, "business/home/index.html")
    else:
        return redirect("index")

# update customer
def updateCustomer(request, customer_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        # Récupération des données client
        customer = get_object_or_404(Customer, id=customer_id)

        # Sécurisation de l'accès aux données
        if not request.user == customer.user:
            if request.user.groups.filter(name="Business_user").exists():
                # add a message : un problème est survenu
                return redirect("business_dashbord")
        
        # Filtres de validaion du formulaire
        if request.method == "POST":
            form = CustomerForm(request.POST, instance=customer)
            if form.is_valid():
                form.save()
                messages.success(request, f"Client modifié avec succès")
                return redirect("detail_customer", customer_id)
        else:
            form = CustomerForm(instance=customer)

        return render(request, "business/customer/customer_form.html", {"form": form})
    else:
        return redirect("index")

# delete customer 
def deleteCustomer(request, customer_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        # Récupération des données du client
        customer = get_object_or_404(Customer, id=customer_id)

        # Filtres de sécurité pour l'accès aux données
        if not request.user == customer.user:
            if request.user.groups.filter(name="Business_user").exists():
                return redirect("business_dashbord")
        
        if request.method == "POST":
            customer.delete()
            messages.success(request, f"Client supprimé avec succès.")
            return redirect("customers")
    else:
        return redirect("index")

# list of orders estimate
def listEstimate(request):
    # Filtres d'accès aux données en fonction du rôle
    if request.user.groups.filter(name="Business_admin").exists():
        estimates = Order.objects.filter(is_valid=False)
    elif request.user.groups.filter(name="Business_user").exists():
        estimates = Order.objects.filter(is_valid=False, user=request.user)
    else:
        estimates = []

    paginator = Paginator(estimates, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'business/order/order_list.html', {'page_obj': page_obj})

# list of orders validate
def listBill(request):
    # Filtres d'accès aux données en fonction du rôle
    if request.user.groups.filter(name="Business_admin").exists():
        bills = Order.objects.filter(is_valid=True)
    elif request.user.groups.filter(name="Business_user").exists():
        bills = Order.objects.filter(is_valid=True, user=request.user)
    else:
        bills = []

    paginator = Paginator(bills, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'business/order/order_list.html', {'page_obj': page_obj})

# add order
def addOrder(request):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        if request.method == "POST":
            form = OrderForm(request.POST)

            if form.is_valid():
                form.instance.user = request.user
                order = form.save()
                messages.success(request, f"Devis créé avec succès.")
                return redirect("update_product_order", order_id=order.id)
        else:
            form = OrderForm()

        return render(request, "business/order/order_form.html", {"form": form})
    else:
        return redirect("index")

# detail order
def detailOrder(request, order_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        order = get_object_or_404(Order, id=order_id)
        orderDetails = OrderDetail.objects.filter(order=order)
        form = OrderDetailForm()

        total = Decimal('0')
        total_taxe = Decimal('0')

        for orderDetail in orderDetails:
            subtotal = orderDetail.subtotal_ht()
            total += subtotal
            total_taxe += subtotal + (subtotal * Decimal(str(orderDetail.product.taxe)))

        if request.method == "POST":
            form = OrderDetailForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    product = form.cleaned_data['product']
                    quantity = form.cleaned_data['quantity']

                    existing_order_detail = OrderDetail.objects.filter(order=order, product=product).first()

                    if existing_order_detail:
                        existing_order_detail.quantity += quantity
                        existing_order_detail.save()
                    else:
                        order_detail = OrderDetail(product=product, quantity=quantity, order=order)
                        order_detail.save()

                return redirect("detail_order", order_id=order.id)

        else:
            form = OrderDetailForm()

        return render(
            request, 
            "business/order/order_detail.html", 
            {
                "order": order,
                "order_detail": orderDetails,
                "total": total,
                "total_taxe": total_taxe,
                "form": form,
            }
        )
    else:
        return redirect("index")

# update products in order
def updateProductOrder(request, order_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        order = get_object_or_404(Order, id=order_id)
        orderDetails = OrderDetail.objects.filter(order=order)
        form = OrderDetailForm()
        products = Product.objects.all()

        total = Decimal('0')
        total_taxe = Decimal('0')

        for orderDetail in orderDetails:
            subtotal = orderDetail.subtotal_ht()
            total += subtotal
            total_taxe += subtotal + (subtotal * Decimal(str(orderDetail.product.taxe)))

        products_json = serialize('json', products)

        if request.method == "POST":
            form = OrderDetailForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    product = form.cleaned_data['product']
                    quantity = form.cleaned_data['quantity']

                    existing_order_detail = OrderDetail.objects.filter(order=order, product=product).first()

                    if existing_order_detail:
                        existing_order_detail.quantity += quantity
                        existing_order_detail.save()
                    else:
                        order_detail = OrderDetail(product=product, quantity=quantity, order=order)
                        order_detail.save()
                    
                    messages.success(request, f"Article ajouté avec succès.")

                return redirect("update_product_order", order_id=order.id)

        else:
            form = OrderDetailForm()

        return render(
            request, 
            "business/order/order_detail_products.html", 
            {
                "order": order,
                "order_detail": orderDetails,
                "total": total,
                "total_taxe": total_taxe,
                "form": form,
                "products_json": products_json,
            }
        )
    else:
        return redirect("index")

# update quantity of a product in order
def update_quantity(request, order_id,order_detail_id, quantity):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        order_detail = get_object_or_404(OrderDetail, id=order_detail_id)

        # Vérifier si l'utilisateur a le droit de modifier la commande
        if not request.user == order_detail.order.user:
            if request.user.groups.filter(name="Business_user").exists():
                return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
            
        # Vérifiez si la nouvelle quantité est valide
        try:
            new_quantity = int(quantity)
            if new_quantity <= 0:
                return messages.alert(request, f"La quantité doit être supérieure à zéro.")
        except ValueError:
            return messages.alert(request, f"La quantité est invalide.")
        
        # Mettez à jour la quantité
        order_detail.quantity = new_quantity
        order_detail.save()

        # Affichage des totaux
        total_ht = calculate_total(order_id)
        total_ttc = calculate_total_taxe(order_id)

        return JsonResponse({
            "success": True, 
            "message": "Quantité mise à jour avec succès",
            "total" : total_ht,
            "total_taxe": total_ttc,
            "subtotal": order_detail.subtotal_with_tax(),
        })
    else:
        return redirect("index")  

# Pour afficher le total HT d'une commande
def calculate_total(order_id):
    order_details = OrderDetail.objects.filter(order_id=order_id)
    total_ht = sum(detail.subtotal_ht() for detail in order_details)
    return total_ht

# Pour afficher le total TTC d'une commande
def calculate_total_taxe(order_id):
    order_details = OrderDetail.objects.filter(order_id=order_id)
    total_ttc = sum(detail.subtotal_with_tax() for detail in order_details)
    return total_ttc

# delete a product in order
def deleteProductOrder(request, orderDetail_id, order_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        order = get_object_or_404(Order, id=order_id)
        orderDetail = get_object_or_404(OrderDetail, id=orderDetail_id)

        # un utilisateur qui n'est pas admin de la commande ne peut pas modifier les articles de la commande
        if not request.user == orderDetail.order.user:
            if request.user.groups.filter(name="Business_user").exists():
                return redirect("business_dashbord")

        if request.method == "POST":
            try:
                orderDetail.delete()
                messages.success(request, f"L'article {orderDetail.product.name} a été supprimé avec succès.")
            except Exception as e:
                messages.error(request, f"Error deleting product: {e}")

            # Redirect to the update_product_order view after deletion
            return redirect("update_product_order", order_id=order_id)
        else:
            # Handle non-POST requests as needed
            return HttpResponse("Method not allowed", status=405)
    
# update order
def updateOrder(request, order_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        order = get_object_or_404(Order, id=order_id)

        if not request.user == order.user:
            if request.user.groups.filter(name="Business_user").exists():
                # add a message : un problème est survenu
                return redirect("business_dashbord")
        
        if request.method == "POST":
            form = OrderForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
                messages.success(request, f"Commande modifiée aec succès.")
                return redirect("detail_order", order_id)
        else:
            form = OrderForm(instance=order)

        return render(request, "business/order/order_form.html", {"form": form})
    else:
        return redirect("index")

# delete order
def deleteOrder(request, order_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        order = get_object_or_404(Order, id=order_id)

        if not request.user == order.user:
            if request.user.groups.filter(name="Business_user").exists():
                return redirect("business_dashbord")
        
        if request.method == "POST":
            order.delete()
            messages.success(request, f"Commande supprimée avec succès")
            return redirect("business_dashbord")
        else:
            return redirect("business_dashbord")
    else:
        return redirect("index")

# remove product from order 
def removeOrderProduct(request, order_id, product_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        if request.method == 'POST':
            # Supprimez l'OrderDetail associé au produit dans la commande
            order = get_object_or_404(Order, id=order_id)
            OrderDetail.objects.filter(product_id=product_id, order=order).delete()
            return messages.success(request, f"Article supprimé avec succès")

        return JsonResponse({'success': False})
    else:
        return redirect("index")

# validate order
def validateOrder(request, order_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        order = get_object_or_404(Order, id=order_id)
        orderDetails = OrderDetail.objects.filter(order=order)

        if request.method == "POST":
            if 'validate_button' in request.POST:
                order.is_valid = True
                order.save()

                for order_detail in orderDetails:
                    product = order_detail.product
                    product.stock -= order_detail.quantity
                    product.save()

                # message : Devis validé ; vous pouvez maintenant le retrouver dans la liste des factures
        
        return render(request, 'business/order/order_detail.html', {"order" : order, "order_detail": orderDetails})
    else:
        return redirect("index")

# list of products
def listProduct(request):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        business_admin = request.user.groups.filter(name="Business_admin").exists()
        business_user = request.user.groups.filter(name="Business_user").exists()

        if business_admin or business_user:
            products = Product.objects.all().order_by('-id')
        else:
            products = []

        paginator = Paginator(products, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return render(request, 'business/product/product_list.html', {"page_obj": page_obj})
    else:
        return redirect("index")

# add product
def addProduct(request):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists():
        if request.method == "POST":
            form = ProductForm(request.POST)

            if form.is_valid():
                form.save()
                messages.success(request, f"Produit ajouté avec succès.")
                return redirect("products")
        else:
            form = ProductForm()

        return render(request, "business/product/product_form.html", {"form": form})
    else:
        return redirect("index")

# update product
def updateProduct(request, product_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists() or request.user.groups.filter(name="Business_user").exists():
        product = get_object_or_404(Product, id=product_id)

        if not request.user.groups.filter(name="Business_admin").exists():
            return redirect("business_dashbord")
        
        if request.method == "POST":
            form = ProductForm(request.POST, instance=product)
            if form.is_valid():
                form.save()
                messages.success(request, f"Produit modifié avec succès.")
                return redirect("products")
        else:
            form = ProductForm(instance=product)

        return render(request, "business/product/product_form.html", {"form": form})
    else:
        return redirect("index")

# delete product
def deleteProduct(request, product_id):
    # Sécurisation de l'accès aux données
    if request.user.groups.filter(name="Business_admin").exists():
        product = get_object_or_404(Product, id=product_id)
        
        if request.method == "POST":
            product.delete()
            messages.success(request, f"Produit supprimé avec succès.")
            return redirect("products")
        else:
            messages.error(request, f"Un problème est survenu.")
            return redirect("products")
    return redirect("index")

# convert order to pdf
class GeneratePDF(View):
    def get(self, request, *args, **kwargs):
        # Récupérer les données nécessaires pour le PDF (par exemple, order)
        order = Order.objects.get(id=kwargs['order_id'])

        # Créer un objet HttpResponse avec le type de contenu PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename="order_{}.pdf"'.format(order.code)

        # Créer un objet PDF en utilisant le module canvas de ReportLab
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        # Ajouter les informations du client et de la commande dans la partie supérieure
        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(colors.HexColor('#3498db'))  # Bleu clair
        p.drawString(100, 750, 'Informations du client')
        p.setFillColor(colors.black)

        p.setFont("Helvetica", 12)
        y_position = 730
        p.drawString(100, y_position, 'Client : {} {}'.format(order.customer.first_name, order.customer.last_name))
        y_position -= 20
        p.drawString(100, y_position, 'Adresse : {} {} {}'.format(order.customer.address, order.customer.zipcode, order.customer.city))
        y_position -= 20
        p.drawString(100, y_position, 'Email : {}'.format(order.customer.email))
        y_position -= 20
        p.drawString(100, y_position, 'Téléphone : {}'.format(order.customer.phone_number))

        y_position -= 40

        p.setFillColor(colors.HexColor('#2ecc71'))  # Vert clair
        p.drawString(100, y_position, 'Informations de la commande')
        p.setFillColor(colors.black)

        y_position -= 20
        p.drawString(100, y_position, 'Commande : {}'.format(order.code))
        y_position -= 20
        if order.is_valid == False:
            p.drawString(100, y_position, 'En cours de validation')
        else:
            p.drawString(100, y_position, 'Commande payée')

        # Ajouter le tableau récapitulatif dans la partie inférieure
        table_data = [
            ['Produit', 'Quantité', 'Prix unitaire', 'TVA', 'Total HT'],
        ]

        for detail in order.orderdetail_set.all():
            table_data.append([
                detail.product.name,
                str(detail.quantity),
                '{}€'.format(detail.product.price),
                '{}%'.format(detail.product.taxe),
                '{}€'.format(detail.subtotal_ht()),
            ])

        # Calculer les totaux
        total_ht = sum(detail.subtotal_ht() for detail in order.orderdetail_set.all())
        total_ttc = sum(detail.subtotal_with_tax() for detail in order.orderdetail_set.all())

        y_position -= 40

        p.setFillColor(colors.HexColor('#e74c3c'))  # Rouge clair
        p.drawString(100, y_position, 'Récapitulatif de la commande')
        p.setFillColor(colors.black)

        # Ajouter le tableau à la page
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),  # Gris clair
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]

        table = Table(table_data, style=table_style, colWidths=[200, 50, 80, 50, 80])
        table.wrapOn(p, 400, 600)
        table.drawOn(p, 100, y_position - 80)

        # Ajouter les totaux sous le tableau
        y_position -= 140
        p.setFillColor(colors.HexColor('#34495e'))  # Gris foncé
        p.drawString(100, y_position, 'Total de la commande HT : {}€'.format(total_ht))
        y_position -= 20
        p.drawString(100, y_position, 'Total de la commande TTC : {}€'.format(total_ttc))

        # Fermer le PDF
        p.showPage()
        p.save()

        # Mettez à jour le HttpResponse avec le contenu du buffer
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)

        return response
