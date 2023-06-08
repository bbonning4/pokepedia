from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from .utils import POKEMON_TUPLES

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.CharField(max_length=250, default='https://w0.peakpx.com/wallpaper/416/975/HD-wallpaper-slowpoke-pokemon-face-eyes.jpg')
    display_name = models.CharField(max_length=100, default='', blank=True)
    favorite_pokemon = models.CharField(
        max_length=100,
        choices=POKEMON_TUPLES,
        default=POKEMON_TUPLES[802][1] # 'Slowpoke'
    )

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.user.username
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('update_profile', kwargs={'pk': self.id})
    
    def __str__(self):
        return self.user.username

class Favorite(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    image = models.CharField(max_length=250)
    is_shiny = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} favorited by {self.profile.user.username}'
    
class Photo(models.Model):
    url = models.CharField(max_length=250)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f"Photo for {self.profile.user.username}'s Profile @{self.url}"