import os # used to access .env variables
import uuid # helpful for generating random strings
import boto3 # AWS SDK python library
from typing import Any, Dict
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile, Favorite, Photo, Wishlist
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

    divs = soup.find_all('div')
    images = []
    urls = []  
    for div in divs:
        a_element = div.find('a')
        img_element = div.find('img')
        if a_element and img_element:
            image = img_element.get('src')
            url_param = a_element.get('href')
            images.append(image)
            urls.append(f"https://www.google.com{url_param}")

    images_and_urls = list(zip(images, urls))
    filtered_list = images_and_urls[1::3]
    filtered_list_20 = filtered_list[:20]

    context = {
        'name': name,
        'images_and_urls': filtered_list_20,
    }
    return render(request, 'pokemon/products.html', context)

def find_more_products(request, name):
    profile_id = Profile.objects.get(user_id=request.user.id).id
    wishlist_items = Wishlist.objects.filter(profile_id=profile_id)
    images = []
    urls = []
    is_wishlist_items = []
    products = []
    random_page = random.randint(0, 500)
    url = f"https://www.google.com/search?q={name}+pokemon+toy&tbm=shop&start={random_page}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    divs = soup.find_all('div')

    for div in divs:
        is_wishlist_item = False
        a_element = div.find('a')
        img_element = div.find('img')
        if a_element and img_element:
            image = img_element.get('src')
            url_param = a_element.get('href')
            images.append(image)
            urls.append(f"https://www.google.com{url_param}")
            for item in wishlist_items:
                if image == item.image:
                    is_wishlist_item = True
                    is_wishlist_items.append(is_wishlist_item)
            if not is_wishlist_item:
                    is_wishlist_item = False
                    is_wishlist_items.append(is_wishlist_item)
            product = {
                'image': image,
                'url': url,
                'is_wishlist_item': True,
            }
            products.append(product)

    filtered_list = products[1::3]
    if len(filtered_list) < 24:
        filtered_list_20 = filtered_list[:len(filtered_list) - 6]
    else:    
        filtered_list_20 = filtered_list[:20]

    context = {
        'name': name,
        'images_and_urls': filtered_list_20,
    }
    return render(request, 'pokemon/products.html', context)

def wishlist_index(request):
    profile_id = Profile.objects.get(user_id=request.user.id).id
    wishlist_items = Wishlist.objects.filter(profile_id=profile_id)
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'pokemon/wishlist.html', context)

def add_wishlist_item(request):
    profile = Profile.objects.get(user_id=request.user.id)
    wishlist_item = Wishlist.objects.create(image=request.POST.get('image'), url=request.POST.get('url'), profile=profile)
    return redirect(request.META['HTTP_REFERER'])

def remove_wishlist_item(request, wishlist_id):
    profile_id = Profile.objects.get(user_id=request.user.id).id
    profile = get_object_or_404(Profile, id=profile_id)
    if profile.user != request.user:
        return redirect('/')
    return redirect(request.META['HTTP_REFERER'])


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ['display_name', 'favorite_pokemon']

    # Sets default display name to users username
    def get_initial(self):
        initial = super().get_initial()
        initial['display_name'] = self.request.user.username
        return initial  
    

@login_required
def update_avatar(request, profile_id):
    # photo_file will be set to the name attribute on the input type="file"
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        # creates unique filename with 6 characters & keeps file extension
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        try:
            bucket = os.environ['S3_BUCKET']
            s3.upload_fileobj(photo_file, bucket, key)
            # builds url string
            url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
            Photo.objects.create(url=url, profile_id=profile_id)
        except Exception as e:
            print('An error occured uploading file to S3')
            print(e)
    return redirect('update_profile', profile_id=profile_id)
