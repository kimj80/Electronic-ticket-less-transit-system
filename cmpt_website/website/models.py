from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import datetime
from django.http import HttpResponseRedirect
import time
import math

# Create your models here.
def bits2a(b):
    return ''.join(chr(int(''.join(x), 2)) for x in zip(*[iter(b)]*8))

class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'

    def __str__(self):
        return self.username

class Card(models.Model):
    card_id = models.CharField(db_column='card_ID', primary_key=True, max_length=256)  # Field name made lowercase.
    manufacturer_id = models.CharField(max_length=50)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column='user', blank=True, null=True)
    status = models.IntegerField()
    balance = models.DecimalField(max_digits = 200, decimal_places = 2)
    expiry = models.DateTimeField()
    
    class Meta:
        managed = False
        db_table = 'card'

    def __str__(self):
        return str("ID: "+str(self.card_id) + " -- BALANCE: "+ "${:,.2f}".format(self.balance/100))
    def __getstatus__(self):
        return str(self.status)
    def is_active(self):
        if self.status == 1:
            print("CARD STATUS", self.status)
            return True
        else:
            return False
    def make_inactive(self):
        self.status = 0
        self.save(update_fields=['status'])
        
    def make_active(self):
        self.status = 1
        self.save(update_fields=['status'])

    def expiry_status(self):
        now = datetime.now()
        unixtime_1 = time.mktime(now.timetuple())
        unixtime_2 = time.mktime(self.expiry.timetuple())
       
        if unixtime_1 > unixtime_2:
            return("-- EXPIRED")
            
        else:
            return("")

    def sub_time_remaining(self):
        results = CardSubscription.objects.all().filter(card = self.card_id)
        results_list = list(results)
        if len(results_list) == 0:
            return "Not Applicable"
        else:
            subscription_time = results_list[0].expiry
            now = datetime.now()
            unixtime_1 = time.mktime(now.timetuple())
            unixtime_2 = time.mktime(subscription_time.timetuple())
            if unixtime_2 < unixtime_1:
                return "Expired"
            else:
                difference = unixtime_2 - unixtime_1
                days_difference = difference / (60 * 24 * 60)
                return str(math.floor(days_difference)) + " day(s)"

    def get_subscription_expiry(self):
        results = CardSubscription.objects.all().filter(card = self.card_id)
        results_list = list(results)
        print(results_list)
        if len(results_list) == 0:
            return "NO RESULT"
        else:
            subscription_time = results_list[0].expiry
            return subscription_time

    def has_subscription(self):
        subscription = CardSubscription.objects.all().filter(card  = self.card_id)
      
        sub_list = list(subscription)
    
        if len(sub_list) > 0:
            print("TRUE")
            return True
        else:
            return False

    def MakeDollar(self):
        if self.balance == 0:
            return "$0.00"
        else:
            dollar_balance = self.balance/100
            return "${:,.2f}".format(dollar_balance)
    
    def deactivateCard(self):
        if self.is_active():
            self.make_inactive()
        else:
            self.make_active()
        
        return None



        


class CardSubscription(models.Model):
    card = models.OneToOneField(Card, models.DO_NOTHING, db_column='card', primary_key=True)
    sub = models.ForeignKey('Subscription', models.DO_NOTHING, db_column='sub')
    expiry = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'card_subscription'
        unique_together = (('card', 'sub'),)



class Subscription(models.Model):
    sub_id = models.IntegerField(db_column='sub_ID', primary_key=True)  # Field name made lowercase.
    title = models.CharField(max_length=100)
    type = models.TextField()  # This field type is a guess.
    rate = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'subscription'



class CardAction(models.Model):
    transaction_id = models.CharField(db_column='transaction_ID', primary_key=True, max_length=256)  # Field name made lowercase.
    card = models.ForeignKey(Card, models.DO_NOTHING)
    zone = models.ForeignKey('TravelZone', models.DO_NOTHING, db_column='zone', blank=True, null=True)
    new_amount = models.IntegerField()
    charge = models.IntegerField()
    type = models.ForeignKey('TransactionTypes', models.DO_NOTHING, db_column='type')
    time = models.DateTimeField()
    bus_number = models.IntegerField(blank=True, null=True)
    verification = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'card_action'


class TransactionTypes(models.Model):
    type_id = models.IntegerField(db_column='type_ID', primary_key=True)  # Field name made lowercase.
    description = models.CharField(max_length=256)
    location = models.CharField(max_length=256)

    class Meta:
        managed = False
        db_table = 'transaction_types'


class TravelZone(models.Model):
    zone_id = models.IntegerField(db_column='zone_ID', primary_key=True)  # Field name made lowercase.
    zone_name = models.CharField(max_length=256)
    ride_charge = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'travel_zone'
