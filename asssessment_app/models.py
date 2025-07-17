from django.db import models

# Create your models here.
class BankTransactions(models.Model):
    date= models.DateTimeField()
    description= models.CharField(max_length=100)
    amount= models.DecimalField(max_digits=50, decimal_places=2)
    reference_number= models.IntegerField(default=0)
    status= models.BooleanField(default=False)
    class Meta:
        db_table= "bank_transactions"


class Customer(models.Model):
    name= models.CharField(max_length=100)
    email= models.CharField(max_length=100)
    class Meta:
        db_table="customer"






class Invoice(models.Model):
    customer= models.CharField(max_length=100)
    amount_due= models.DecimalField(max_digits=50, decimal_places=2)
    status= models.BooleanField(default= False)
    class Meta:
        db_table= "invoice"





class ReconciliationLog(models.Model):
    bank_transaction= models.ForeignKey(BankTransactions, on_delete=models.CASCADE)
    invoice= models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    MATCHED_BY_CHOICES = [
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
    ]
    matched_by = models.CharField(max_length=10, choices=MATCHED_BY_CHOICES, default='auto', null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table= "reconciliation_log"