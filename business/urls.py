from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # homepages
    path('dashbord/', views.dashbord, name="business_dashbord"),
    # customer pages
    path('customer/', views.listCustomer, name="customers"),
    path('customer/add/', views.addCustomer, name="add_customer"),
    path('customer/<int:customer_id>/', views.detailCustomer, name="detail_customer"),
    path('customer/<int:customer_id>/update/', views.updateCustomer, name="update_customer"),
    path('customer/<int:customer_id>/delete/', views.deleteCustomer, name="delete_customer"),
    # order pages
    path('order/estimate/', views.listEstimate, name="estimates"),
    path('order/bill/', views.listBill, name="bills"),
    path('order/add/', views.addOrder, name="add_order"),
    path('order/<int:order_id>/', views.detailOrder, name="detail_order"),
    path('order/<int:order_id>/update_product/', views.updateProductOrder, name="update_product_order"),
    path('order/<int:order_id>/delete_product/<int:orderDetail_id>/', views.deleteProductOrder, name='delete_product_order'),
    path('order/<int:order_id>/update_quantity/<int:order_detail_id>/<int:quantity>/', views.update_quantity, name='update_quantity'),
    path('order/<int:order_id>/update/', views.updateOrder, name="update_order"),
    path('order/<int:order_id>/delete/', views.deleteOrder, name="delete_order"),
    path('order/<int:order_id>/validate/', views.validateOrder, name="validate_order"),
    path('order/<int:order_id>/delete/<int:product_id>/', views.removeOrderProduct, name="remove_order_product"),
    # product pages
    path('product/', views.listProduct, name="products"),
    path('product/add/', views.addProduct, name="add_product"),
    path('product/<int:product_id>/update/', views.updateProduct, name="update_product"),
    path('product/<int:product_id>/delete/', views.deleteProduct, name="delete_product"),
    # pdf files
    path('generate_pdf/<int:order_id>/', views.GeneratePDF.as_view(), name='generate_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
