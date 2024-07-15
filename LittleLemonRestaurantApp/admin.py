from django.contrib import admin
from .models import Category,MenuItem,Cart,Order,OrderItem
# Register your models here.
data=[Category,MenuItem,Cart,Order,OrderItem]
for x in data:
    admin.site.register(x)