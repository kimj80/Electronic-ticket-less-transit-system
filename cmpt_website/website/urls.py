"""cmpt_website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('aboutus', views.aboutus, name='aboutus'),
    path('contact', views.contact, name='contact'),
    path('product', views.product, name='product'),
    path('safetyrules', views.safetyrules, name='safetyrules'),
    path('my_account', views.myaccount, name='account'),
    path('', views.redirect_view, name='redirect'),
    path('add_balance/<card_id>', views.add_balance, name="add-balance"),
    path('link_card', views.link_card, name="link-card"),
    path('transfer_balance', views.transfer_balance, name="transfer-balance"),
    path('success_page', views.success_page, name="success-page"),
    path('not_enough_cards', views.transfer_balance, name="not-enough-cards"),
    path('transfer_subscription', views.transfer_subscription, name="transfer-subscription"),
    path('not_enough_subscriptions', views.transfer_subscription, name="not_enough_subscriptions"),
    path('message_sent', views.message_sent, name="message_sent"),
    path('add_subscription/<card_id>', views.add_subscription, name="add_subscription"),
    path('deactivate_card/<card_id>', views.deactivate_card, name="deactivate_card")
]
