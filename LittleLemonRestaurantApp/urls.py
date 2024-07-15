from django.urls import path
# from . import views
from .views import CategoryListCreateView, MenuListAPIView,GetMenuListAPIView,ManagerListAPIView,UserCartListAPIView,OrderProductsListAPIView
from .serializers import CategorySerializer
from .models import Category

urlpatterns = [

    # http://127.0.0.1:8000/api/users/ for registration
    # http://127.0.0.1:8000/api/token/login for login


    # path('category',views.category,name='category'),
    # path('category', ListCreateAPIView.as_view(queryset=Category.objects.all(), serializer_class=CategorySerializer), name='user-list'),
    path('category',CategoryListCreateView.as_view(), name='category-list'),
    path('menu-items',GetMenuListAPIView.as_view(), name='menu-items'),  # List all menu items
    path('menu-items/<int:id>', MenuListAPIView.as_view(), name='menu-item-detail'),  # Detail view for specific menu item
    path('groups/manager/users',ManagerListAPIView.as_view(),name='manger-list'),
    path('groups/manager/users/<int:id>',ManagerListAPIView.as_view(),name='manger-list'),
    # path('groups/delivery-crew/users',views.Deliverycrew,name='Deliverycrew'),

    # # cart Management endpoints
    path('cart/menu-items',UserCartListAPIView.as_view(),name='usercart'),


    # # Order management endpoints
    path('orders',OrderProductsListAPIView.as_view(),name='userorder'),
    path('orders/<int:pk>',OrderProductsListAPIView.as_view(),name='singleorder'),
    # path('orders/<int:pk>',views.OrderProducts,name="showsingleorder")
]