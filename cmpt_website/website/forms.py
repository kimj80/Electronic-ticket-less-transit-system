from pyexpat import model
from django import forms
from django.forms import ModelForm
from .models import Card, CardAction
from .models import AuthUser
from django.core.exceptions import ValidationError

def validate_unique(value):

    ID = value
    result = Card.objects.filter(card_id = ID)
    if len(result) == 0:
         raise forms.ValidationError(
            (' No Card Found with ID Number %(value)s. Please Try Again.'),
            params={'value': value},
        )
    else: 
        this_card = Card.objects.get(card_id = ID)
        user_id = getattr(this_card, 'user')

        if user_id != None:
            raise forms.ValidationError(
            ('The Card With ID Number %(value)s Is In Use. Please Try Again.'),
            params={'value': value},
        )
    return result


def validate_transfer(value):
    balance = value
    if (balance <= 0):
        raise forms.ValidationError(
            ('Insufficient balance for card %(value)s'),
            params={'balance': balance},
        )

 # Create a card form
class UpdateCardBalanceForm(ModelForm):
    class Meta:
        model = Card
        # model = [Card, CardAction]
        fields = ('balance',)
        labels={'balance': 'Enter Amount',}

class CreateCardAction(ModelForm):
    class Meta:
        model = CardAction
        fields = ('transaction_id', 'card', 'zone', 'new_amount', 'charge', 'type', 'time', 'bus_number', 'verification', )

# Link card to user account
class LinkCardForm(forms.Form):
    card_id = forms.IntegerField(label='Enter Card ID', validators=[validate_unique])


# transfer funds from one linked card to another
class TransferFundsForm(forms.Form):

    dropdown_1 = forms.ModelChoiceField(label='From Card ', queryset=Card.objects.all())
    dropdown_2 = forms.ModelChoiceField(label='To Card ', queryset=Card.objects.all())

    def __init__(self, cards1=None, *args, **kwargs):
         super(TransferFundsForm, self).__init__(*args, **kwargs)
         if cards1:
            self.fields['dropdown_1'].queryset = cards1
            self.fields['dropdown_2'].queryset = cards1

    def clean(self):
        if self.cleaned_data['dropdown_1'].card_id == self.cleaned_data['dropdown_2'].card_id:
            raise ValidationError("Cannot Transfer Funds To The Same Card")
        elif self.cleaned_data['dropdown_1'].balance <= 0:
            raise ValidationError("Cannot Transfer From a Negative Balance")
        return self.cleaned_data

# transfers subscriptions from one linked card to another
class TransferSubscriptionForm(forms.Form):

    dropdown_1 = forms.ModelChoiceField(label='From Card ', queryset = Card.objects.all())
    dropdown_2 = forms.ModelChoiceField(label='To Card ', queryset = Card.objects.all())


    def __init__(self, cards1=None, cards2=None, *args, **kwargs):
         super(TransferSubscriptionForm, self).__init__(*args, **kwargs)
         if cards1:
            self.fields['dropdown_1'].queryset = cards1
            self.fields['dropdown_2'].queryset = cards2

    def clean(self):
        if self.cleaned_data['dropdown_1'].card_id == self.cleaned_data['dropdown_2'].card_id:
            raise ValidationError("Cannot Transfer  To The Same Card")
        return self.cleaned_data


# form to use for the contact us page
class ContactForm(forms.Form):
	first_name = forms.CharField(max_length = 50)
	last_name = forms.CharField(max_length = 50)
	email_address = forms.EmailField(max_length = 150)
	message = forms.CharField(widget = forms.Textarea, max_length = 2000)

# adds subscription
SUBSCRIPTION_CHOICES= [
    ('week', 'One Week'),
    ('month', 'One Month'),
    ('two_months', 'Two Months'),
    ('four_months', 'Four Months'),
    ('yearly', 'One Year')
    ]

class AddSubscriptionForm(ModelForm):
    class Meta:
        model = Card
        fields = ('expiry',)
        labels={'expiry': 'Enter Length of Time ',}

class AddSubscription(forms.Form):
     subscription = forms.CharField(label='Choose a Subscription', widget=forms.Select(choices=SUBSCRIPTION_CHOICES))

