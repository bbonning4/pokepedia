from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/signup/', views.signup, name='signup'),
    path('profile/<int:pk>/update/', views.ProfileUpdate.as_view(), name='update_profile'),
    path('profile/<int:profile_id>/avatar/', views.update_avatar, name='update_avatar'),
    path('profile/<int:profile_id>/default/', views.default, name='default'),
    path('search/', views.search, name='search'),
    path('favorites/', views.favorites_index, name='favorites'),
    path('favorites/add/', views.add_favorite, name='add_favorite'),
    # update to more RESTful favorites/<int:favorite_id>/remove/
    path('favorites/remove/', views.remove_favorite, name='remove_favorite'),
    path('favorites/<int:profile_id>/pokemon/<int:favorite_id>/', views.show_favorite, name='show_favorite'),
    path('favorites/update_shiny/', views.update_shiny, name='update_shiny'),
    path('products/<str:name>/', views.find_products, name='products'),
    path('products/<str:name>/more/', views.find_more_products, name='more_products'),
    path('wishlist/', views.wishlist_index, name='wishlist'),
    path('wishlist/add/', views.add_wishlist_item, name='add_wishlist_item'),
    path('wishlist/<int:wishlist_id>/remove', views.remove_wishlist_item, name='remove_wishlist_item'),
]