from django.contrib import admin
from .models import Card
from .models import AuthUser


# Register your models here.


admin.site.register(Card)
admin.site.register(AuthUser)


