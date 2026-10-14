from django.contrib import admin
from .models import User,Product,Order,OrderItem

admin.site.register([User, Product,Order,OrderItem])
