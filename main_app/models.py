from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.CharField(default='https://w0.peakpx.com/wallpaper/416/975/HD-wallpaper-slowpoke-pokemon-face-eyes.jpg')

    def __str__(self):
        return self.user.username

class Favorite(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    name = models.CharField()
    image = models.CharField()
    is_shiny = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} favorited by {self.profile.user.username}'