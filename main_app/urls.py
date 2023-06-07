from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/signup/', views.signup, name='signup'),
    path('search/', views.search, name='search'),
    path('favorites/', views.favorites_index, name='favorites'),
    path('favorites/add/', views.add_favorite, name='add_favorite'),
    path('favorites/remove/', views.remove_favorite, name='remove_favorite'),
    path('favorites/<int:profile_id>/pokemon/<int:favorite_id>/', views.show_favorite, name='show_favorite'),
    path('favorites/update_shiny', views.update_shiny, name='update_shiny'),
    path('products/', views.find_products, name='products'),
    path('products/more', views.find_more_products, name='more_products'),
]