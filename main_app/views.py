import os # used to access .env variables
import uuid # helpful for generating random strings
import boto3 # AWS SDK python library
from typing import Any, Dict
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile, Favorite, Photo, Wishlist
from .utils import POKEMON, POKEMON_TYPES
from .functions import search_function, show_favorite_function, get_evolution_chain
from bs4 import BeautifulSoup
import random
import requests

# Create your views here.
def home(request):
    if request.user.id:
        profile = Profile.objects.get(user_id=request.user.id)
        return render(request, 'home.html', {
            'profile': profile
        })
    else:
        return render(request, 'home.html')

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
            print(profile.favorite_pokemon)
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
    context = search_function(request)
    if context["error"]:
        return render(request, '404.html', context)
    else:    
        return render(request, 'pokemon/detail.html', context)
    

@login_required
def favorites_index(request):
    profile_id = Profile.objects.get(user_id=request.user.id).id
    profile = Profile.objects.get(user_id=request.user.id)
    favorites = Favorite.objects.filter(profile_id=profile_id)
    favorites = sorted(favorites, key=lambda favorite: favorite.name)
    context = {
        'favorites': favorites, 
        'profile_id': profile_id,
        'profile': profile,
    }
    return render(request, 'pokemon/favorites.html', context)

@login_required
def add_favorite(request):
    profile = Profile.objects.get(user_id=request.user.id)
    Favorite.objects.create(name=request.POST.get('name'), image=request.POST.get('image'), profile=profile)
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
    context = show_favorite_function(request, profile_id, favorite_id)
    if context["error"]:
        return render(request, '404.html', context)
    else:
        return render(request, 'pokemon/show.html', context)


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
    profile_id = Profile.objects.get(user_id=request.user.id).id
    wishlist_items = Wishlist.objects.filter(profile_id=profile_id)
    images = []
    urls = []
    is_wishlist_items = []
    products = []

    url = f"https://www.google.com/search?q={name}+pokemon+toy&tbm=shop"
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
                    is_wishlist_item = item.id
                    is_wishlist_items.append(is_wishlist_item)
            if not is_wishlist_item:
                    is_wishlist_item = False
                    is_wishlist_items.append(is_wishlist_item)
            product = {
                'image': image,
                'url': url,
                'is_wishlist_item': is_wishlist_item,
            }
            products.append(product)

    filtered_list = products[1::3]
    if len(filtered_list) < 24:
        filtered_list_20 = filtered_list[:len(filtered_list) - 6]
    else:    
        filtered_list_20 = filtered_list[:20]

    main_type = request.GET.get('main_type')
    print(main_type)
    if request.user.id:
        profile = Profile.objects.get(user_id=request.user.id)
        context = {
            'name': name,
            'main_type': main_type,
            'profile': profile,
            'items': filtered_list_20,
        }
    else:
        context = {
            'name': name,
            'main_type': main_type,
            'items': filtered_list_20,
        }
    return render(request, 'pokemon/products.html', context)



def find_more_products(request, name):
    profile = Profile.objects.get(user_id=request.user.id)
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
                    is_wishlist_item = item.id
                    is_wishlist_items.append(is_wishlist_item)
            if not is_wishlist_item:
                    is_wishlist_item = False
                    is_wishlist_items.append(is_wishlist_item)
            product = {
                'image': image,
                'url': url,
                'is_wishlist_item': is_wishlist_item,
            }
            products.append(product)

    filtered_list = products[1::3]
    if len(filtered_list) < 24:
        filtered_list_20 = filtered_list[:len(filtered_list) - 6]
    else:    
        filtered_list_20 = filtered_list[:20]
    
    main_type = request.GET.get('main_type')
    if request.user.id:
        profile = Profile.objects.get(user_id=request.user.id)
        context = {
            'name': name,
            'main_type': main_type,
            'profile': profile,
            'items': filtered_list_20,
        }
    else:
        context = {
            'name': name,
            'main_type': main_type,
            'items': filtered_list_20,
        }
    return render(request, 'pokemon/products.html', context)



@login_required
def wishlist_index(request):
    profile = Profile.objects.get(user_id=request.user.id)
    profile_id = Profile.objects.get(user_id=request.user.id).id
    wishlist_items = Wishlist.objects.filter(profile_id=profile_id)
    context = {
        'wishlist_items': wishlist_items,
        'profile': profile
    }
    return render(request, 'pokemon/wishlist.html', context)

@login_required
def add_wishlist_item(request):
    profile = Profile.objects.get(user_id=request.user.id)
    wishlist_item = Wishlist.objects.create(image=request.POST.get('image'), url=request.POST.get('url'), profile=profile)
    return redirect(request.META['HTTP_REFERER'])

@login_required
def remove_wishlist_item(request, wishlist_id):
    profile_id = Profile.objects.get(user_id=request.user.id).id
    profile = get_object_or_404(Profile, id=profile_id)
    if profile.user != request.user:
        return redirect('/')
    Wishlist.objects.get(id=wishlist_id).delete()

    return redirect(request.META['HTTP_REFERER'])


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ['display_name', 'favorite_pokemon']

    # Sets default display name to users username
    def get_initial(self):
        initial = super().get_initial()
        initial['display_name'] = self.object.display_name
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
            photo = Photo.objects.create(url=url, profile_id=profile_id)
            profile = Profile.objects.get(user_id=request.user.id)
            profile.avatar = photo.url
            profile.save()
        except Exception as e:
            print('An error occured uploading file to S3')
            print(e)
    return redirect('update_profile', pk=profile_id)

@login_required
def default(request, profile_id):
    if request.method == 'POST':
        id = request.POST.get('id')
        profile = Profile.objects.get(id=profile_id)
        profile.avatar = id
        profile.save()
    return JsonResponse({'success': True})
    # return redirect('update_profile', profile_id=profile_id)

def custom_404_page(request, exception):
    profile = Profile.objects.get(user_id=request.user.id)
    return render(request, '404.html', {'profile': profile}, status=404)