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
from .utils import POKEMON, POKEMON_TYPES, get_evolution_chain
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

    if request.user.id:
        profile = Profile.objects.get(user_id=request.user.id)
        profile_id = Profile.objects.get(user_id=request.user.id).id
        favorites = Favorite.objects.filter(profile_id=profile_id)
        pokemon_name = request.GET.get('pokemon_name')
        #initialize for when a dex number is used
        dex_num = pokemon_name
        for key in POKEMON:
            if key.lower() == pokemon_name.lower():
                pokemon_name = POKEMON[key]
                url_param = pokemon_name
                break
            else:
                url_param = dex_num

        url = f"https://pokeapi.co/api/v2/pokemon/{url_param}"
        response = requests.get(url)

        if response.status_code == 200:
            json = response.json()
            name = json["forms"][0]["name"]
            dex_num = json["id"]
            types = [type_data["type"]["name"] for type_data in json["types"]]
            image = json["sprites"]["other"]["official-artwork"]["front_default"]
            abilities = []
            for ability_data in json['abilities']:
                ability_name = ability_data['ability']['name']
                abilities.append(ability_name)
        else:
            error_msg = "No Results"

            return render(request, '404.html', {
                "error_msg": error_msg,
                'profile': profile
            })

    species_url = f"https://pokeapi.co/api/v2/pokemon-species/{dex_num}"
    species_response = requests.get(species_url)

    if species_response.status_code == 200:
        species_json = species_response.json()
        flavor_text_entries = species_json["flavor_text_entries"]
        english_description = ""
        if len(flavor_text_entries) > 0:
            for entry in flavor_text_entries:
                if entry["language"]["name"] == "en":
                    english_description = entry["flavor_text"]
                    english_description = english_description.replace('', ' ')
                    break
            else:
                error_msg = "No Results"

                return render(request, '404.html', {
                    "error_msg": error_msg,
                    'profile': profile
                })

        type_colors = []
        for type in types:
            type_color = POKEMON_TYPES[type.lower()]
            type_colors.append(type_color)
        type_tuples = tuple(zip(types, type_colors))

        type_url = "https://pokeapi.co/api/v2/type"
        type_response = requests.get(type_url)
        type_data = type_response.json()["results"]

        weaknesses = {}
        for pokemon_type in types:
            for data in type_data:
                if data["name"] == pokemon_type:
                    type_url = data["url"]
                    type_response = requests.get(type_url)
                    type_data_nested = type_response.json()

                    damage_relations = type_data_nested["damage_relations"]
                    for relation in damage_relations["double_damage_from"]:
                        weakness_type = relation["name"]
                        if weakness_type in weaknesses:
                            weaknesses[weakness_type] += 1
                        else:
                            weaknesses[weakness_type] = 1

        weakness_colors = []
        for weakness, effective in weaknesses.items():
            weakness_color = POKEMON_TYPES[weakness]
            weakness_colors.append(weakness_color)
        weakness_info_list = [(weakness, value * 2, color) for weakness, value, color in zip(weaknesses.keys(), weaknesses.values(), weakness_colors)]
        name = next((key for key, val in POKEMON.items() if val == name), None)
        context = {
            'name': name,
            'image': image,
            'dex_num': dex_num,
            'types': type_tuples,
            'weaknesses': weakness_info_list,
            'description': english_description,
            'abilities': abilities,
            'is_favorite': any(name == favorite.name for favorite in favorites),
            'profile': profile
        }
        return render(request, 'pokemon/detail.html', context)
    else:
        pokemon_name = request.GET.get('pokemon_name')
        #initialize for when a dex number is used
        dex_num = pokemon_name
        for key in POKEMON:
            if key.lower() == pokemon_name.lower():
                pokemon_name = POKEMON[key]
                url_param = pokemon_name
                break
            else:
                url_param = dex_num

        url = f"https://pokeapi.co/api/v2/pokemon/{url_param}"
        response = requests.get(url)

        if response.status_code == 200:
            json = response.json()
            name = json["forms"][0]["name"]
            dex_num = json["id"]
            types = [type_data["type"]["name"] for type_data in json["types"]]
            image = json["sprites"]["other"]["official-artwork"]["front_default"]
        else:
            error_msg = "No Results"

            return render(request, '404.html')

        species_url = f"https://pokeapi.co/api/v2/pokemon-species/{dex_num}"
        species_response = requests.get(species_url)

        if species_response.status_code == 200:
            species_json = species_response.json()
            flavor_text_entries = species_json["flavor_text_entries"]
            english_description = ""
            for entry in flavor_text_entries:
                if entry["language"]["name"] == "en":
                    english_description = entry["flavor_text"]
                    break
            else:
                error_msg = "No Results"

                return render(request, '404.html')
        
        name = next((key for key, val in POKEMON.items() if val == name), None)
        context = {
            'name': name,
            'image': image,
            'dex_num': dex_num,
            'types': types,
            'description': english_description,
        }
        return render(request, 'pokemon/detail.html', context)


@login_required
def favorites_index(request):
    profile_id = Profile.objects.get(user_id=request.user.id).id
    profile = Profile.objects.get(user_id=request.user.id)
    favorites = Favorite.objects.filter(profile_id=profile_id)
    favorites = sorted(favorites, key=lambda favorite: favorite.name)
    return render(request, 'pokemon/favorites.html', {
        'favorites': favorites, 
        'profile_id': profile_id,
        'profile': profile
    })

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
    # user_profile = Profile.objects.get(user_id=request.user.id)
    favorite = Favorite.objects.get(id=favorite_id)
    # check if logged in user is the user for the profile_id being accessed
    profile = get_object_or_404(Profile, id=profile_id)
    if profile.user != request.user:
        return redirect('/')
    
    image = favorite.image
    pokemon_name = favorite.name
    is_shiny = favorite.is_shiny

    profile = Profile.objects.get(user_id=request.user.id)
    
    for key in POKEMON:
        if key.lower() == pokemon_name.lower():
            name = POKEMON[key]
            url_param = name
            break

    url = f"https://pokeapi.co/api/v2/pokemon/{url_param}"
    response = requests.get(url)

    if response.status_code == 200:
        json = response.json()
        name = json["forms"][0]["name"]
        dex_num = json["id"]
        types = [type_data["type"]["name"] for type_data in json["types"]]
        abilities = []
        for ability_data in json['abilities']:
            ability_name = ability_data['ability']['name']
            abilities.append(ability_name)
    else:
        error_msg = "No Results"

        return render(request, '404.html', {
            "error_msg": error_msg,
            'profile': profile
        })

    species_url = f"https://pokeapi.co/api/v2/pokemon-species/{dex_num}"
    species_response = requests.get(species_url)

    if species_response.status_code == 200:
        species_json = species_response.json()
        flavor_text_entries = species_json["flavor_text_entries"]
        english_description = ""
        if len(flavor_text_entries) > 0:
            for entry in flavor_text_entries:
                if entry["language"]["name"] == "en":
                    english_description = entry["flavor_text"]
                    english_description = english_description.replace('', ' ')
                    break
            else:
                error_msg = "No Results"

                return render(request, '404.html', {
                    "error_msg": error_msg,
                    'profile': profile
                })

    type_colors = []
    for type in types:
        type_color = POKEMON_TYPES[type.lower()]
        type_colors.append(type_color)
    type_tuples = tuple(zip(types, type_colors))

    type_url = "https://pokeapi.co/api/v2/type"
    type_response = requests.get(type_url)
    type_data = type_response.json()["results"]

    weaknesses = {}
    for pokemon_type in types:
        for data in type_data:
            if data["name"] == pokemon_type:
                type_url = data["url"]
                type_response = requests.get(type_url)
                type_data_nested = type_response.json()

                damage_relations = type_data_nested["damage_relations"]
                for relation in damage_relations["double_damage_from"]:
                    weakness_type = relation["name"]
                    if weakness_type in weaknesses:
                        weaknesses[weakness_type] += 1
                    else:
                        weaknesses[weakness_type] = 1

    weakness_colors = []
    for weakness, effective in weaknesses.items():
        weakness_color = POKEMON_TYPES[weakness]
        weakness_colors.append(weakness_color)
    weakness_info_list = [(weakness, value * 2, color) for weakness, value, color in zip(weaknesses.keys(), weaknesses.values(), weakness_colors)]
    name = next((key for key, val in POKEMON.items() if val == name), None)
    context = {
        'name': name,
        'image': image,
        'dex_num': dex_num,
        'types': type_tuples,
        'weaknesses': weakness_info_list,
        'description': english_description,
        'abilities': abilities,
        'is_shiny': is_shiny,
        'profile': profile,
    }
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
    if request.user.id:
        profile = Profile.objects.get(user_id=request.user.id)
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

        context = {
            'name': name,
            'profile': profile,
            'items': filtered_list_20,
        }
        return render(request, 'pokemon/products.html', context)
    else:
        images = []
        urls = []
        is_wishlist_items = []
        products = []

        url = f"https://www.google.com/search?q={name}+pokemon+toy&tbm=shop"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        divs = soup.find_all('div')

        for div in divs:
            a_element = div.find('a')
            img_element = div.find('img')
            if a_element and img_element:
                image = img_element.get('src')
                url_param = a_element.get('href')
                images.append(image)
                urls.append(f"https://www.google.com{url_param}")
                product = {
                    'image': image,
                    'url': url,
                }
                products.append(product)

        filtered_list = products[1::3]
        if len(filtered_list) < 24:
            filtered_list_20 = filtered_list[:len(filtered_list) - 6]
        else:    
            filtered_list_20 = filtered_list[:20]

        context = {
            'name': name,
            'items': filtered_list_20,
        }
        return render(request, 'pokemon/products.html', context)



def find_more_products(request, name):
    if request.user.id:
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

        context = {
            'name': name,
            'profile': profile,
            'items': filtered_list_20,
        }
        return render(request, 'pokemon/products.html', context)
    else:
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
                product = {
                    'image': image,
                    'url': url,
                }
                products.append(product)

        filtered_list = products[1::3]
        if len(filtered_list) < 24:
            filtered_list_20 = filtered_list[:len(filtered_list) - 6]
        else:    
            filtered_list_20 = filtered_list[:20]

        context = {
            'name': name,
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