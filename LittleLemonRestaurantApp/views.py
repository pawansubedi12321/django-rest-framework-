from django.shortcuts import render
from rest_framework import status # type: ignore
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from .models import MenuItem,Category,Cart,OrderItem,Order,Category
from .serializers import MenuSerializer,UserSerializer,MenuCreateSerializer,UserCartSerializer,CreateCartSerializer,CategorySerializer,CreateOrderItemSerializer,OrderItemSerialzer
from django.contrib.auth.models import User, Group
from datetime import date
from django.core.paginator import Paginator,EmptyPage
from rest_framework import generics,permissions
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
import logging
logger = logging.getLogger(__name__)
from django.views.decorators.csrf import csrf_exempt
# from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
class CategoryListCreateView(generics.ListCreateAPIView):
    # print("hello world")
    queryset =Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    # Define custom permission class
class IsManagerPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            return  request.user.groups.filter(name='Manager').exists()

class IsDeliveryCrewPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            return  request.user.groups.filter(name='Delivery crew').exists()
            
class MenuListAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'  # Specify the lookup field here

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH','DELETE']:
            self.permission_classes = [IsAdminUser | (IsAuthenticated & IsManagerPermission)]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000

class GetMenuListAPIView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [AllowAny]
    pagination_class = LargeResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['price']


class ManagerListAPIView(generics.ListCreateAPIView,generics.RetrieveUpdateDestroyAPIView):
    serializer_class=UserSerializer
    lookup_field = 'id'  # Specify the lookup field here

    def get_queryset(self):
        return User.objects.filter(groups__name='Manager')

    def get_permissions(self):
        if self.request.method in ['GET']:
            self.permission_classes = [IsAdminUser | (IsAuthenticated & IsManagerPermission)]
        elif self.request.method in ['POST']:
            self.permission_classes=[IsAdminUser | (IsAuthenticated & IsManagerPermission)]
        elif self.request.method in ['DELETE']:
            self.permission_classes=[IsAdminUser | (IsAuthenticated & IsManagerPermission)]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        try:
            user = User.objects.get(username=username)
            group = Group.objects.get(name='Manager')
            group.user_set.add(user)
            user.save()
            return Response({"message": f"User '{username}' added to the 'Manager' group successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": f"User '{username}' does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            group = Group.objects.get(name='Manager')
            if group.user_set.filter(id=instance.id).exists():
                group.user_set.remove(instance)
                # instance.delete()
                return Response({"message": f"User '{instance.username}' removed from the 'Manager' group and deleted successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": f"User '{instance.username}' is not in the 'Manager' group."}, status=status.HTTP_400_BAD_REQUEST)
        except Group.DoesNotExist:
            logger.warning(f"Group 'Manager' does not exist. User {instance.username} is not removed from the group.")
            # instance.delete()
        except Exception as e:
            logger.error(f"An error occurred while trying to remove user {instance.username} from the 'Manager' group: {e}")
            raise
# # cart Management endpoints
class IsUser(permissions.BasePermission):
        def has_permission(self, request, view):
            return  (not request.user.groups.filter(name='Manager').exists() and
                     not request.user.groups.filter(name='Delivery crew').exists() and 
                     not request.user.is_superuser
            )
class UserCartListAPIView(generics.ListCreateAPIView,generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserCartSerializer
    def get_permissions(self):
        if self.request.method in ['GET']:
            self.permission_classes = [IsAuthenticated & IsUser]
        elif self.request.method in ['POST']:
            self.permission_classes=[IsAuthenticated & IsUser]
        elif self.request.method in ['DELETE']:
            self.permission_classes=[IsAuthenticated & IsUser]
        return super().get_permissions()
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        menuitem_id = request.data.get("menuitem")
        try:
            menuitem = MenuItem.objects.get(id=menuitem_id)
        except MenuItem.DoesNotExist:
            return Response({"message": "Please select the correct menu item."}, status=status.HTTP_400_BAD_REQUEST)

        if Cart.objects.filter(user=request.user, menuitem=menuitem_id).exists():
            return Response({"message": "This menu item is already in your cart. Please select another item."}, status=status.HTTP_400_BAD_REQUEST)

        if OrderItem.objects.filter(order__user=request.user, menuitem=menuitem_id).exists():
            return Response({"message": "This item is already being ordered. Please select another item."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CreateCartSerializer(data={
            'menuitem': menuitem.id,
            'quantity': request.data.get("quantity"),
            'unit_price': request.data.get("unit_price"),
            'price': request.data.get("price"),
            'user': request.user.id
        })

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Cart added successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def destroy(request, *args, **kwargs):
        queryset=Cart.objects.all()
        queryset.delete()
        return Response({"message":"Cart deleted successfully"},status=status.HTTP_200_OK)

class OrderProductsListAPIView(generics.ListCreateAPIView,generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderItemSerialzer
    queryset = OrderItem.objects.all()
    lookup_field = 'pk'  # Specify the lookup field here

    def get_permissions(self):
        if self.request.method=='GET':
            if IsUser().has_permission(self.request,self):
                self.permission_classes = [IsAuthenticated & IsUser]
            elif IsManagerPermission().has_permission(self.request,self):
                self.permission_classes=[IsAuthenticated & IsManagerPermission]
            elif IsDeliveryCrewPermission().has_permission(self.request,self):
                self.permission_classes=[IsAuthenticated & IsDeliveryCrewPermission]

        elif self.request.method in ['POST']:
            self.permission_classes=[IsAuthenticated & IsUser]
        elif self.request.method=='PATCH':
             if IsUser().has_permission(self.request,self):
                 self.permission_classes=[IsAuthenticated & IsUser]
             elif IsManagerPermission().has_permission(self.request,self): 
                 self.permission_classes=[IsAuthenticated & IsManagerPermission]
                   
        elif self.request.method in ['DELETE']:
            if IsUser().has_permission(self.request,self) and IsManagerPermission().has_permission(self.request, self):
                self.permission_classes = [IsAuthenticated, IsUser, IsManagerPermission]
        return super().get_permissions()
    
    def get_queryset(self):
        if IsUser().has_permission(self.request, self):
            return self.get_queryset_for_user()
        elif IsManagerPermission().has_permission(self.request,self):
            return self.get_queryset_for_manager()
        elif IsDeliveryCrewPermission().has_permission(self.request,self):
            allorder=OrderItem.objects.filter(order__delivery_crew=self.request.user)
            return allorder   
    
    def get_queryset_for_user(self):
        print("Hello i am not manager")
        if 'id' in self.kwargs:
            return OrderItem.objects.filter(order__user=self.request.user, id=self.kwargs['id'])
        return OrderItem.objects.filter(order__user=self.request.user)
    
    def get_queryset_for_manager(self):
        if self.request.user.groups.filter(name='Manager').exists():
            queryset=OrderItem.objects.all()
            return queryset
           

    
    def create(self, request, *args, **kwargs):
        getcart=Cart.objects.filter(user=request.user.id)
        current_date = date.today()
        for cart in getcart:
            new_order = Order.objects.create(
                            user=request.user,
                            delivery_crew=None,  
                            status=False,  
                            total=cart.price,  
                            date=current_date)
            OrderItem.objects.create(
                            order=new_order,
                            menuitem=cart.menuitem,
                            quantity=cart.quantity,
                            unit_price=cart.unit_price,
                            price=cart.price) 
        if not getcart.exists():
            return Response({"message":"cart does not exists. please do add the item in cart"})
        else:
            getcart.delete()
            return Response({"message":"succcessfully placed order"},status=status.HTTP_200_OK)
    
    def partial_update(self,request, *args, **kwargs):
        if IsUser().has_permission(self.request,self):
            pk = kwargs.get('pk')  # Fetch 'id' parameter from kwargs
            if pk is None:
                return Response({"message": "ID parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
            singleorder = OrderItem.objects.filter(id=pk).first()
            if not singleorder:
                    return Response({"message": "Order item not found."}, status=status.HTTP_404_NOT_FOUND)
            # singleorder = self.get_object()  # Retrieve the OrderItem instanc
                        
            menuitem_id = request.data.get('menuitem')
            if not menuitem_id:
                return Response({"message": "Menu item is required."}, status=status.HTTP_400_BAD_REQUEST)
                        
            menuexists = OrderItem.objects.filter(order=singleorder.order, menuitem=menuitem_id).exists()
            if menuexists:
                return Response({"message": "Menu exists in your order. Please select another menu item."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                    menuitem = MenuItem.objects.get(id=menuitem_id)
            except MenuItem.DoesNotExist:
                    return Response({"message": "Menu item not found."}, status=status.HTTP_404_NOT_FOUND)
            quantity = request.data.get('quantity')
            unit_price = request.data.get('unit_price')
            price = request.data.get('price')
            if quantity is None or unit_price is None or price is None:
                    return Response({"message": "Quantity, unit price, and price are required."}, status=status.HTTP_400_BAD_REQUEST)
            singleorder.quantity = quantity
            singleorder.unit_price = unit_price
            singleorder.price = price
            singleorder.menuitem = menuitem
            singleorder.order = singleorder.order  # keep the original order
            singleorder.save()
            serializer = CreateOrderItemSerializer(singleorder)
            responsedata = {
                            "message": "Successfully edited",
                            "data": serializer.data
                        }
            return Response(responsedata, status=status.HTTP_200_OK)
        
        if IsManagerPermission().has_permission(self.request,self):
            delivery_crew = request.data.get('delivery_crew')
            pk = kwargs.get('pk')  # Fetch 'id' parameter from kwargs
            if pk is None:
                return Response({"message": "ID parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
            if pk:
                orderitem=OrderItem.objects.get(id=pk)
                delivery_crew = User.objects.get(username=delivery_crew)
                order=orderitem.order
                order.delivery_crew=delivery_crew
                order.save()
                orderitem.save()
                serializer=OrderItemSerialzer(orderitem)
                response_data={
                    "message":"successfully edited",
                    "data":serializer.data
                }
                return Response(response_data,status=status.HTTP_200_OK) 
        elif IsDeliveryCrewPermission().has_permission(self.request,self):
            pk = kwargs.get('pk')  # Fetch 'id' parameter from kwargs
            if pk is None:
                return Response({"message": "ID parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            new_status = request.data.get('status')
            if new_status is None:
                return Response({"message": "Please fill the status"}, status=status.HTTP_404_NOT_FOUND)
            try:
                orderitem = OrderItem.objects.get(id=pk)
            except OrderItem.DoesNotExist:
                return Response({"message": "OrderItem not found"}, status=status.HTTP_404_NOT_FOUND)
            order=orderitem.order
            order.status = new_status
            order.delivery_crew = request.user
            order.save()
            orderitem.save()
            orderserializer =OrderItemSerialzer(orderitem)
            response = {
                    "message": "Successfully edited",
                    "data": orderserializer.data
                }
            return Response(response, status=status.HTTP_200_OK)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "congrats,Successfully deleted"}, status=status.HTTP_200_OK)
