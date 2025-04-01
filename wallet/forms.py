from django import forms

class TransferForm(forms.Form):
    recipient_id = forms.CharField(max_length=100, required=True)
    amount = forms.DecimalField(max_digits=20, decimal_places=2, required=True)
    currency = forms.ChoiceField(choices=[('QPT', 'QPT')])
