from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile
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
    pokemon_name = request.GET.get('pokemon_name')
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        json = response.json()
        name = json["name"].capitalize()
        image = json["sprites"]["other"]["official-artwork"]["front_default"]
    else:
        error_msg = "No Results"
        return render(request, 'home.html', {"error_msg": error_msg})
    return render(request, 'pokemon/detail.html', {'name': name, 'image': image})    
