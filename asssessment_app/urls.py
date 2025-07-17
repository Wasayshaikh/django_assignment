from django.urls import path
from .views import api_home,upload_transaction,upload_invoice

urlpatterns = [
    path('home', api_home),
    path('bank/upload', upload_transaction),
    path('bank/upload-invoices', upload_invoice),
]