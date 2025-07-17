from django import forms

class upLoadTransactions(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV File",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',   
            'accept': '.csv, .xlsx'
        })
    )


class uploadInvoice(forms.Form):
    invoice_csv = forms.FileField(
        label="Upload CSV File",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',   
            'accept': '.csv, .xlsx',
            
        })
    )