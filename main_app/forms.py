from django.forms import ModelForm
from .models import Profile

class PokemonForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['favorite_pokemon']
