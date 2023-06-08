from django.contrib import admin
from .models import Profile, Favorite, Photo, Wishlist

# Register your models here.
admin.site.register(Profile)
admin.site.register(Favorite)
admin.site.register(Photo)
admin.site.register(Wishlist)