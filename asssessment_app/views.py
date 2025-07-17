from django.shortcuts import render,redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .forms import upLoadTransactions,uploadInvoice
import csv
import io
from .models import BankTransactions, Invoice, ReconciliationLog
from datetime import datetime
import re
from django.utils import timezone
from django.http import HttpResponse, HttpResponseNotAllowed
from django.utils.timezone import now


@api_view(['GET'])
def api_home(request):
    return Response({"message": "Hello from DRF!"})

@api_view(['POST'])
def upload_transaction(request):
    form = upLoadTransactions(request.POST, request.FILES)
    if form.is_valid():
        file = form.cleaned_data['csv_file']
        valid_extensions = ['.csv']
        if not any([file.name.endswith(ext) for ext in valid_extensions]):
            return Response({"message": "Invalid file type. Only .csv and allowed"}, status=400)
        file = form.cleaned_data['csv_file']
        data = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(data))
        count = 0
        for row in csv_reader:
            raw_date = row.get('date', '')
            try:
           
                parsed_date = datetime.strptime(raw_date, "%Y/%m/%d")
                aware_dt = timezone.make_aware(parsed_date)
            except ValueError:
       
                parsed_date = None 
            BankTransactions.objects.update_or_create(
                reference_number=row.get('reference_number', ''),
                defaults={
                    "date":aware_dt,
                    "description":row.get('description', ''),
                    "amount":row.get('amount', ''),
                    "status":row.get('status', ''),
                }
            )
            count += 1
        reconciliation_transaction()
        transactions = BankTransactions.objects.all().values('date','description', 'amount','reference_number','status')
        return Response({
            "message": f"{count} transaction(s) saved to database.",
            "transactions": list(transactions)
        })
    return Response({"message": "Form is not valid"}, status=400)


@api_view(['POST'])
def upload_invoice(request):
    form = uploadInvoice(request.POST, request.FILES)
    if form.is_valid():
        file = form.cleaned_data['invoice_csv']
        valid_extensions = ['.csv']
        if not any([file.name.endswith(ext) for ext in valid_extensions]):
            return Response({"message": "Invalid file type. Only .csv allowed"}, status=400)
        file = form.cleaned_data['invoice_csv']
        data = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(data))
        count = 0
        for row in csv_reader:
            raw_date = row.get('date', '')
            try:
                parsed_date = datetime.strptime(raw_date, "%Y/%m/%d")
            except ValueError:
       
                parsed_date = None 
            customer_id = row.get('customer_id', 0)
            Invoice.objects.update_or_create(
                id=customer_id,
                defaults={
                    "amount_due":row.get('amount_due', ''),
                    "customer":row.get('customer', ''),
                    "status":row.get('status', ''),
                }
            )
            count += 1
        transactions = Invoice.objects.all().values(
            'id', 'amount_due', 'customer', 'status'
        )
        
        return Response({
            "message": f"{count} transaction(s) saved to database.",
            "transactions": list(transactions)
        })
    return Response({"message": "Form is not valid"}, status=400)


def reconciliation_transaction():
    transactions = BankTransactions.objects.all()

    for transaction in transactions:
        existing_log = ReconciliationLog.objects.filter(bank_transaction=transaction).first()


        if existing_log and existing_log.invoice is not None:
            continue

        customer_name = get_name_from_description(transaction.description)

        if not customer_name:
           
            if not existing_log:
                ReconciliationLog.objects.create(
                    bank_transaction=transaction,
                    invoice=None,
                    matched_by=None
                )
            continue

        invoice = Invoice.objects.filter(
            customer__iexact=customer_name,
            amount_due=transaction.amount,
            status=False
        ).first()

        if invoice:
            invoice.status = True
            invoice.save()

            if existing_log:
                
                existing_log.invoice = invoice
                existing_log.matched_by = "Automatic"
                existing_log.save()
            else:
                ReconciliationLog.objects.create(
                    bank_transaction=transaction,
                    invoice=invoice,
                    matched_by="Automatic"
                )
        else:
           
            if not existing_log:
                ReconciliationLog.objects.create(
                    bank_transaction=transaction,
                    invoice=None,
                    matched_by=None
                )


def get_name_from_description(description):
    match = re.search(r'name=([\w\s]+)', description, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

# all the web view functions


def index(request):
    return render(request, 'index.html') 

def bank_transaction_view(request):
    form = upLoadTransactions()
    invoices= uploadInvoice()
    bankTransactions = BankTransactions.objects.all()
    
    return render(request, 'bank_transaction.html', {'form': form,'invoices':invoices, "logs":bankTransactions}) 

def invoice_view(request):
    form = upLoadTransactions()
    invoices= uploadInvoice()
    invoices_log = Invoice.objects.all()
    return render(request, 'invoices.html', {'form': form,'invoices':invoices, 'logs':invoices_log}) 


def reconciliation_log_view(request):
    logs = ReconciliationLog.objects.select_related('bank_transaction', 'invoice').all()
    unpaid_invoices = Invoice.objects.filter(status=False)
    return render(request, 'reconciliation.html', {
        'logs': logs,'unpaid_invoices':unpaid_invoices
    })

def match_log_view(request):
    matched_logs = ReconciliationLog.objects.select_related('bank_transaction', 'invoice').filter(invoice__isnull=False)

    return render(request, 'reconciliation.html', {
       
        'logs': matched_logs,
    })


def unmatched_log_view(request):
    unmatched_logs = ReconciliationLog.objects.select_related('bank_transaction').filter(invoice__isnull=True)
    unpaid_invoices = Invoice.objects.filter(status=False)
    return render(request, 'reconciliation.html', {
        
        'logs': unmatched_logs,'unpaid_invoices':unpaid_invoices
    })

def manual_match_transaction(request):
    if request.method == "POST":
        transaction_id = request.POST.get("transactions_id")
        invoice_id = request.POST.get("invoice_id")
        log_id = request.POST.get("log_id")
        try:
            transaction = BankTransactions.objects.filter(id=transaction_id).first()
            invoice = Invoice.objects.filter(id=invoice_id).first()
            
            invoice.status = True
            invoice.save()

            reconciliationLog = ReconciliationLog.objects.select_related('bank_transaction', 'invoice').filter(bank_transaction=transaction).first()

            if reconciliationLog:
                reconciliationLog.matched_by = "manual"
                reconciliationLog.timestamp = now()
                reconciliationLog.invoice = invoice
                reconciliationLog.save()
            else:
                ReconciliationLog.objects.create(
                    bank_transaction=transaction,
                    invoice=invoice,
                    matched_by="manual"
                )
            return redirect('logs')
        except Exception as e:
            return HttpResponse(f"Error: {e}", status=400)
    else:
        return HttpResponseNotAllowed(["GET"], "Method Not Allowed")