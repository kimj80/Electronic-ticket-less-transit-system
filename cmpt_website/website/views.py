import email
from random import randint
import time
from django.conf import settings
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from .models import AuthUser, CardAction, CardSubscription, CardAction, TransactionTypes, TravelZone
from .models import Card
from .forms import UpdateCardBalanceForm
from .forms import CreateCardAction
from .forms import ContactForm
from .forms import LinkCardForm
from .forms import TransferFundsForm
from .forms import TransferSubscriptionForm
from .forms import AddSubscription
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField
from django.core.mail import send_mail, BadHeaderError
from datetime import datetime, timedelta
import time
 



# Create your views here.
def index(request):
    return render(request, 'index.html', {})

def product(request):
    return render(request, 'product.html', {})

def contactus(request):
    return render(request, 'contactus.html', {})

def aboutus(request):
    return render(request, 'aboutus.html', {})

def safetyrules(request):
    return render(request, 'safetyrules.html', {})

def success_page(request):
    return render(request, 'success_page.html', {})

def message_sent(request):
    return render(request, 'message_sent.html', {})


@login_required
def myaccount(request):
    users = AuthUser.objects.filter(id = request.user.id)
    cards = Card.objects.filter(user = request.user.id)
    context = {
        'users': users,
        'cards': cards
    }
    return render(request, 'my_account.html', context)

def redirect_view(request):
    response = redirect('my_account')
    return response

@login_required
def add_balance(request, card_id):
    this_card = Card.objects.get(pk=card_id)
    current_balance = getattr(this_card, 'balance')
    form = UpdateCardBalanceForm(request.POST or None)

    if form.is_valid():
        amount_adds = form.cleaned_data['balance']
        amount_add = amount_adds * 100
        new_amount = int(current_balance) + amount_add
        this_card.balance = new_amount
        this_card.save(update_fields=['balance'])

        action = CardAction.objects.create(\
            transaction_id = str(card_id) + str( time.time_ns()//1000000 ),\
            card = this_card,\
            zone = TravelZone.objects.get(pk=0),\
            new_amount = new_amount,\
            charge = amount_add,\
            type = TransactionTypes.objects.get(pk="5"),\
            time = datetime.fromtimestamp((time.time_ns()//1000000) / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f"),\
            bus_number = '0',\
            verification = randint(1, 65535),\
        )

        return HttpResponseRedirect('../success_page')

    return render(request, 'add_card_balance.html', {'card': this_card, 'form': form})


@login_required
def link_card(request):
    form_1 = LinkCardForm(request.POST or None)
    if request.method == "POST":
        if form_1.is_valid():
            ID = form_1.cleaned_data['card_id']
            this_card = Card.objects.get(card_id = ID)
            correct_user = AuthUser.objects.get(pk=getattr(request.user,"id"))
            this_card.user = correct_user
            this_card.save(update_fields=['user'])
            return HttpResponseRedirect('../success_page')


    return render(request, 'link_card.html', {'user': request.user, 'form_1': form_1})

@login_required
def transfer_balance(request):

    Cards_1 = Card.objects.all().filter(user= getattr(request.user, 'id'))

    list_cards = list(Cards_1)
    if len(list_cards) <= 1:
        return render(request,'not_enough_cards.html', {})

    if request.method == "POST":
        form_2 = TransferFundsForm(Cards_1, request.POST or None)
        if form_2.is_valid():
            card_1 = form_2.cleaned_data['dropdown_1']
            card_2 = form_2.cleaned_data['dropdown_2']

            action_1 = CardAction.objects.create(\
                transaction_id = str(card_1.card_id) + str( time.time_ns()//1000000 ),\
                card = card_1,\
                zone = TravelZone.objects.get(pk=0),\
                new_amount = 0,\
                charge = -(getattr(card_1, 'balance')),\
                type = TransactionTypes.objects.get(pk="8"),\
                time = datetime.fromtimestamp((time.time_ns()//1000000) / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f"),\
                bus_number = '0',\
                verification = randint(1, 65535),\
            )
            action_2 = CardAction.objects.create(\
                transaction_id = str(card_2.card_id) + str( time.time_ns()//1000000 ),\
                card = card_2,\
                zone = TravelZone.objects.get(pk=0),\
                new_amount = getattr(card_2, 'balance') + getattr(card_1, 'balance'),\
                charge = getattr(card_1, 'balance'),\
                type = TransactionTypes.objects.get(pk="8"),\
                time = datetime.fromtimestamp((time.time_ns()//1000000) / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f"),\
                bus_number = '0',\
                verification = randint(1, 65535),\
            ) 

            card_2.balance = card_1.balance + card_2.balance
            card_1.balance = 0

            card_1.save(update_fields=['balance'])
            card_2.save(update_fields=['balance'])


            return render(request,'success_page.html', {})


    else:
        form_2 = TransferFundsForm(Cards_1, request.POST or None)


    return render(request,'transfer_balance.html', {'form_2': form_2})


@login_required
def transfer_subscription(request):

    Cards_1 = Card.objects.all().filter(user= getattr(request.user, 'id'))
    Cards_2 = Card.objects.all().filter(user= getattr(request.user, 'id'))
    list_cards = list(Cards_1)
    if len(list_cards) <= 1:
        return render(request,'not_enough_cards.html', {})


    for card in list_cards:
         print(card)
         if card.has_subscription():
            print("TRUE")
            Cards_2 = Cards_2.exclude(card_id = card.card_id)
            print(list(Cards_2))
         else:
            Cards_1 = Cards_1.exclude(card_id = card.card_id)
            print("Nope")

    # No cards linked to account with subscription
    if len(Cards_1) < 1:
        return render(request,'not_enough_subscriptions.html', {})

    if request.method == "POST":
        form_3 = TransferSubscriptionForm(Cards_1, Cards_2, request.POST or None)
        if form_3.is_valid():
            card_1 = form_3.cleaned_data['dropdown_1']
            card_2 = form_3.cleaned_data['dropdown_2']

            sub_1 = CardSubscription.objects.filter(card = card_1.card_id)
            sub_list = list(sub_1)
            card_sub = sub_list[0]

            new_sub = CardSubscription.objects.create(card=card_2, sub=card_sub.sub, expiry=card_sub.expiry)
            new_sub.save()
            record = CardSubscription.objects.get(card = card_1.card_id)
            record.delete()

            action_1 = CardAction.objects.create(\
                transaction_id = str(card_1.card_id) + str( time.time_ns()//1000000 ),\
                card = card_1,\
                zone = TravelZone.objects.get(pk=0),\
                new_amount = getattr(card_1, 'balance'),\
                charge = 0,\
                type = TransactionTypes.objects.get(pk="9"),\
                time = datetime.fromtimestamp((time.time_ns()//1000000) / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f"),\
                bus_number = '0',\
                verification = randint(1, 65535),\
            )
            action_2 = CardAction.objects.create(\
                transaction_id = str(card_2.card_id) + str( time.time_ns()//1000000 ),\
                card = card_2,\
                zone = TravelZone.objects.get(pk=0),\
                new_amount = getattr(card_2, 'balance'),\
                charge = 0,\
                type = TransactionTypes.objects.get(pk="9"),\
                time = datetime.fromtimestamp((time.time_ns()//1000000) / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f"),\
                bus_number = '0',\
                verification = randint(1, 65535),\
            )


            return render(request,'success_page.html', {})


    else:
        form_3 = TransferSubscriptionForm(Cards_1, Cards_2, request.POST or None)


    return render(request,'transfer_subscription.html', {'form_3': form_3})



def contact(request):
	if request.method == 'POST':
		form = ContactForm(request.POST)
		if form.is_valid():
			subject = "Website Inquiry" 
			body = {
			'first_name': form.cleaned_data['first_name'], 
			'last_name': form.cleaned_data['last_name'], 
			'email': form.cleaned_data['email_address'], 
			'message':form.cleaned_data['message'], 
			}
			message = "\n".join(body.values())

			try:
				send_mail(subject, message, settings.EMAIL_HOST_USER, [settings.RECIPIENT_ADDRESS]) 
			except BadHeaderError:
				return HttpResponse('Invalid header found.')
			return redirect ("message_sent")

	form = ContactForm()
	return render(request, "contact.html", {'form':form})


@login_required
def add_subscription(request, card_id):
    this_card = Card.objects.get(pk=card_id)
    form_4 = AddSubscription(request.POST or None)
    if form_4.is_valid():
        sub_choice = form_4.cleaned_data['subscription']
        now_time = datetime.now()

        if sub_choice == "week":
            now_time = now_time + timedelta(days=8)
            td = timedelta(weeks=1)
        elif sub_choice == "month":
            now_time = now_time + timedelta(days=31)
            td = timedelta(days=31)
        elif sub_choice == "two_months":
            now_time = now_time + timedelta(days=62)
            td = timedelta(days=62)
        elif sub_choice == "four_months":
            now_time = now_time + timedelta(days=124)
            td = timedelta(days=124)
        elif sub_choice == "yearly":
            now_time = now_time + timedelta(days=366)
            td = timedelta(days=365)

        get_sub = CardSubscription.objects.filter(card=this_card.card_id)
        get_sub_list = list(get_sub)

        action = CardAction.objects.create(\
            transaction_id = str(card_id) + str( time.time_ns()//1000000 ),\
            card = this_card,\
            zone = TravelZone.objects.get(pk=0),\
            new_amount = getattr(this_card, 'balance'),\
            charge = 0,\
            type = TransactionTypes.objects.get(pk="9"),\
            time = datetime.fromtimestamp((time.time_ns()//1000000) / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f"),\
            bus_number = '0',\
            verification = randint(1, 65535),\
        )

        if len(get_sub_list) == 0:
            subscript = CardSubscription(card=this_card, sub_id=1, expiry = now_time)
            subscript.save()
            return render(request,'success_page.html', {})
        else:
            card_sub_expiry = this_card.get_subscription_expiry()
            new_expiry = card_sub_expiry + td
            card_sub = CardSubscription.objects.get(pk=this_card.card_id)
            card_sub.expiry = new_expiry
            card_sub.save()
            return render(request,'success_page.html', {})


    else:
        form_4 = AddSubscription(request.POST or None)

    return render(request, 'add_subscription.html', {'card': this_card, 'form_4': form_4})

def deactivate_card(request, card_id):
    card = Card.objects.get(pk=card_id)

    users = AuthUser.objects.filter(id = request.user.id)
    card.deactivateCard()
    cards = Card.objects.filter(user = request.user.id)
 
    context = {
        'users': users,
        'cards': cards
    }

    action = CardAction.objects.create(\
            transaction_id = str(card_id) + str( time.time_ns()//1000000 ),\
            card = card,\
            zone = TravelZone.objects.get(pk=0),\
            new_amount = getattr(card, 'balance'),\
            charge = 0,\
            type = TransactionTypes.objects.get(pk="6"),\
            time = datetime.fromtimestamp((time.time_ns()//1000000) / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f"),\
            bus_number = '0',\
            verification = randint(1, 65535),\
        )

    return render(request, 'my_account.html', context)

