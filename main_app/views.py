from typing import Any, Dict
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile, Favorite
from .utils import POKEMON
from bs4 import BeautifulSoup
import random
import requests

# Create your views here.
def home(request):
    error_msg = ""
    return render(request, 'home.html', {'error_msg': error_msg})

def signup(request):
    error_message = ''
    if request.method == 'POST':
        # This is how to create a 'user' form object
        # that includes the data from the browser
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # This will add the user to the database
            user = form.save()
            profile = Profile(user=user)
            profile.save()
            # This is how we log a user in via code
            login(request, user)
            return redirect('/')
        else:
            error_message = 'Invalid sign up - try again'
    # A bad POST or a GET request, so render signup.html with an empty form
    form = UserCreationForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)  

def search(request):
    profile_id = Profile.objects.get(user_id=request.user.id).id
    favorites = Favorite.objects.filter(profile_id=profile_id)
    pokemon_search = request.GET.get('pokemon_name')
    for key in POKEMON:
        if key.lower() == pokemon_search.lower():
            pokemon_name = POKEMON[key]
            name = key

    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
    response = requests.get(url)
    if response.status_code == 200:
        json = response.json()
        # name = json["name"].capitalize()
        image = json["sprites"]["other"]["official-artwork"]["front_default"]
    else:
        error_msg = "No Results"
        return render(request, 'home.html', {"error_msg": error_msg})
    context = {
        'name': name,
        'is_favorite': any(name == favorite.name for favorite in favorites)
    }
    return render(request, 'pokemon/detail.html', {'name': name, 'image': image, 'context': context})    

@login_required
def favorites_index(request):
    profile_id = Profile.objects.get(user_id=request.user.id).id
    favorites = Favorite.objects.filter(profile_id=profile_id)
    favorites = sorted(favorites, key=lambda favorite: favorite.name)
    return render(request, 'pokemon/favorites.html', {'favorites': favorites, 'profile_id': profile_id})

@login_required
def add_favorite(request):
    profile = Profile.objects.get(user_id=request.user.id)
    favorite = Favorite.objects.create(name=request.POST.get('name'), image=request.POST.get('image'), profile=profile)
    # Redirects to current page
    return redirect(request.META['HTTP_REFERER'])

@login_required
def remove_favorite(request):
    profile = Profile.objects.get(user_id=request.user.id)
    favorite = Favorite.objects.get(name=request.POST.get('name'), profile=profile)
    favorite.delete()
    if request.POST.get('show_page') == "true":
        return redirect('favorites')
    # Redirects to current page
    return redirect(request.META['HTTP_REFERER'])

@login_required
def show_favorite(request, profile_id, favorite_id):
    favorite = Favorite.objects.get(id=favorite_id)
    # check if logged in user is the user for the profile_id being accessed
    profile = get_object_or_404(Profile, id=profile_id)
    if profile.user != request.user:
        return redirect('/')
    # is_logged_in = user.is_active and user.is_authenticated
    return render(request, 'pokemon/show.html', {'favorite': favorite})

@login_required
def update_shiny(request):
    profile = Profile.objects.get(user_id=request.user.id)
    favorite = Favorite.objects.get(name=request.POST.get('name'), profile=profile)
    favorite.is_shiny = not favorite.is_shiny
    
    pokemon_name = POKEMON[request.POST.get('name')]
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
    response = requests.get(url)
    if favorite.is_shiny == True:
        json = response.json()
        shiny_image = json["sprites"]["other"]["official-artwork"]["front_shiny"]
        favorite.image = shiny_image
    else:
        json = response.json()
        not_shiny_image = json["sprites"]["other"]["official-artwork"]["front_default"]
        favorite.image = not_shiny_image     
    favorite.save()
    return redirect(request.META['HTTP_REFERER'])

def find_products(request, name):
    url = f"https://www.google.com/search?q={name}+pokemon+toy&tbm=shop"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    image_tags = soup.find_all('img')
    image_urls = [img['src'] for img in image_tags[1:]]
    return render(request, 'pokemon/products.html', {'image_urls': image_urls, 'name': name})

def find_more_products(request, name):
    image_urls = []
    while len(image_urls) < 20:
        random_page = random.randint(0, 500)
        url = f"https://www.google.com/search?q={name}+pokemon+toy&tbm=shop&start={random_page}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        image_tags = soup.find_all('img')
        image_urls = [img['src'] for img in image_tags[1:]]
    return render(request, 'pokemon/products.html', {'image_urls': image_urls, 'name': name})

class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ['avatar', 'display_name', 'favorite_pokemon']

    def get_initial(self):
        initial = super().get_initial()
        initial['display_name'] = self.request.user.username
        return initial  