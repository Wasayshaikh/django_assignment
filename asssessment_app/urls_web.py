from django.urls import path
from .views import index, bank_transaction_view, invoice_view, reconciliation_log_view,match_log_view,unmatched_log_view,manual_match_transaction

urlpatterns = [
    path('', index, name='home'),
    path('upload-transaction', bank_transaction_view, name='home'),
    path('upload-invoice', invoice_view, name='upload_invoice'),
    path('reconciliation-log', reconciliation_log_view, name='logs'),
    path('matched-log', match_log_view, name='match_logs'),
    path('unmatched-log', unmatched_log_view, name='unmatched_logs'),
    path('manual-match', manual_match_transaction, name='manual_match'),
    
]