from rest_framework import serializers
from .models import MenuItem,Category,Cart,OrderItem,Order
from django.contrib.auth.models import User
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=['id','slug','title']
class MenuSerializer(serializers.ModelSerializer):
    category=CategorySerializer()
    class Meta:
        model=MenuItem
        fields =['id','title','price','featured','category']

class MenuCreateSerializer(serializers.ModelSerializer):
    # category=CategorySerializer()
    class Meta:
        model=MenuItem
        fields =['id','title','price','featured','category']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']  # Include any other fields you need

class UserCartSerializer(serializers.ModelSerializer):
    menuitem=MenuCreateSerializer()
    user=UserSerializer()
    class Meta:
        model=Cart
        fields=['id','menuitem','quantity','user','unit_price','price']

class CreateCartSerializer(serializers.ModelSerializer):
    class Meta:
        model=Cart
        fields=['id','menuitem','quantity','user','unit_price','price']

class Deliverycrew(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','username']

class OrderSerializer(serializers.ModelSerializer):
    user=UserSerializer()
    delivery_crew=Deliverycrew()
    class Meta:
        model=Order
        fields=['id','user','delivery_crew','status','total','date']
class OrderItemSerialzer(serializers.ModelSerializer):
    order=OrderSerializer()
    menuitem=MenuCreateSerializer()
    class Meta:
        model=OrderItem
        fields=['id','order','menuitem','quantity','unit_price','price']

class CreateOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrderItem
        fields=['id','order','menuitem','quantity','unit_price','price']
