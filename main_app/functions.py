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
from bs4 import BeautifulSoup
import random
import requests

def search_function(request):
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
        main_type = types[0]
        image = json["sprites"]["other"]["official-artwork"]["front_default"]
        abilities = []
        for ability_data in json['abilities']:
            ability_name = ability_data['ability']['name']
            abilities.append(ability_name)
        formatted_abilities = [ability_name.title().replace(' ', '_').replace('-', '_') for ability_name in abilities]
        ability_tuples = [(ability, formatted_ability) for ability, formatted_ability in zip(abilities, formatted_abilities)]
    else:
        error_msg = "No Results"

        if request.user.id:
            context = {
                'error': True,
                'error_msg': error_msg,
                'profile': profile,
            }
            return context

        else:
            context = {
                'error': True,
                'error_msg': error_msg,
            }
            return context

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

                if request.user.id:
                    context = {
                        'error': True,
                        'error_msg': error_msg,
                        'profile': profile,
                    }
                    return context

                else:
                    context = {
                        'error': True,
                        'error_msg': error_msg,
                    }
                    return context

    type_url = "https://pokeapi.co/api/v2/type"
    type_response = requests.get(type_url)
    type_data = type_response.json()["results"]

    weaknesses = {}
    weaknesses_to_remove = []
    resistances = {}

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
                for relation in damage_relations["half_damage_from"]:
                    resistance_type = relation["name"]
                    if resistance_type in weaknesses:
                        weaknesses[resistance_type] -= 1
                        if weaknesses[resistance_type] <= 0:
                            weaknesses_to_remove.append(resistance_type)
                    else:
                        if resistance_type in resistances:
                            resistances[resistance_type] += 1
                        else:
                            resistances[resistance_type] = 1
                for relation in damage_relations["no_damage_from"]:
                    immunity_type = relation["name"]
                    if immunity_type in weaknesses:
                        del weaknesses[immunity_type]
                    elif immunity_type in resistances:
                        resistances[immunity_type] = 0
                    else:
                        resistances[immunity_type] = 0


    for weakness in weaknesses_to_remove:
        del weaknesses[weakness]

    weakness_info_list = [(weakness, value*2) for weakness, value in zip(weaknesses.keys(), weaknesses.values())]
    resist_info_list = [(resistance, value*2) for resistance, value in zip(resistances.keys(), resistances.values())]
    name = next((key for key, val in POKEMON.items() if val == name), None)
    if request.user.id:
        context = {
            'error': False,
            'name': name,
            'image': image,
            'dex_num': dex_num,
            'types': types,
            'main_type': main_type,
            'weaknesses': weakness_info_list,
            'resistances': resist_info_list,
            'description': english_description,
            'abilities': ability_tuples,
            'is_favorite': any(name == favorite.name for favorite in favorites),
            'profile': profile,
        }
    else:
        context = {
            'error': False,
            'name': name,
            'image': image,
            'dex_num': dex_num,
            'types': types,
            'main_type': main_type,
            'weaknesses': weakness_info_list,
            'resistances': resist_info_list,
            'description': english_description,
            'abilities': ability_tuples,
        }
    return context

def show_favorite_function(request, profile_id, favorite_id):
    favorite = Favorite.objects.get(id=favorite_id)
    # check if logged in user is the user for the profile_id being accessed
    profile = get_object_or_404(Profile, id=profile_id)
    if profile.user != request.user:
        context = {
            'error': True,
        }
        return context
    
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
        context = {
            'error': True,
        }
        return context

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
                context = {
                    'error': True,
                }
                return context

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
        'error': False,
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
    return context

def get_evolution_chain(pokemon_name):
    # Retrieve Pokemon species data
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}")
    if response.status_code != 200:
        print("Error occurred while retrieving Pokemon species data.")
        return None

    species_data = response.json()

    # Retrieve evolution chain URL
    evolution_chain_url = species_data['evolution_chain']['url']

    # Retrieve evolution chain data
    response = requests.get(evolution_chain_url)
    if response.status_code != 200:
        print("Error occurred while retrieving evolution chain data.")
        return None

    evolution_chain_data = response.json()

    # Parse evolution chain data
    evolution_line = []
    current_evolution = evolution_chain_data['chain']

    while True:
        pokemon_species_name = current_evolution['species']['name']
        evolution_details = current_evolution.get('evolution_details', [])

        evolution_line.append((pokemon_species_name, evolution_details))

        if not current_evolution['evolves_to']:
            break

        current_evolution = current_evolution['evolves_to'][0]

    return evolution_line