from .models import *
from django.forms import ModelForm
from django import forms

class profileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name','last_name','gender','profile_picture']

        widgets = {
            'first_name' : forms.TextInput(attrs={'class' : 'form-control w-100', 'placeholder' : 'Enter your first name'}),
            'last_name' : forms.TextInput(attrs={'class':'form-control w-100', 'placeholder' : 'Enter your last name'}),
            'gender' : forms.Select(attrs={'class':'form-control w-100', 'placeholder' : 'Enter your email'}),
            'profile_picture' : forms.ClearableFileInput(attrs={'class':'form-control w-100'}),
        }

class moodEntryForm(ModelForm):
    class Meta:
        model = MoodEntry
        fields = [
            'mood_category',
            'mood_intensity',
            'stress_level',
            'energy_level',
            'hunger_level',
            'craving',
            'time_of_day',
            'weather',
            'specific_feelings',
        ]
        widgets = {
            'mood_category' : forms.Select(attrs={'class':'form-select'}),
            'mood_intensity' : forms.NumberInput(attrs={'type':'range','min':1,'max':10,'class':'form-range'}),
            'stress_level' : forms.NumberInput(attrs={'type':'range','min':1,'max':10,'class':'form-range'}),
            'energy_level' : forms.NumberInput(attrs={'type':'range','min':1,'max':10,'class':'form-range'}),
            'hunger_level' : forms.NumberInput(attrs={'type':'range','min':1,'max':10,'class':'form-range'}),
            'craving' : forms.TextInput(attrs={'class':'form-control','placeholder':'Optional: Chocolate, Pizza...'}),
            'time_of_day': forms.Select(attrs={'class':'form-select'}),
            'weather': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional: Sunny, Rainy…'}),
            'specific_feelings': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your mood…'}),
        }

class foodCategory(ModelForm):
    class Meta:
        model = FoodCategory
        fields = ['name','description',]
        widgets = {
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'description':forms.TextInput(attrs={'class':'form-control'}),
        }

class foodItemForm(ModelForm):
    class Meta:
        model = FoodItem
        fields = [
            'name',
            'description',
            'category',
            'calories',
            'prep_time',
            'difficulty',
            'recipe_link',
            'image_url',
        ]
        widgets = {
            'name':forms.TextInput(attrs={'class':'form-control','placeholder':'Food name (e.g. Pasta)'}),
            'description' : forms.Textarea(attrs={'class':'form-control','placeholder':'Short description','rows':2}),
            'category' : forms.Select(attrs={'class':'form-select'}),
            'calories' : forms.NumberInput(attrs = {'class':'form-control','placeholder':'calories'}),
            'prep_time':forms.NumberInput(attrs={'class':'form-control','placeholder':'preparation time (minutes)'}),
            'difficulty' : forms.Select(attrs={'class':'form-select'}),
            'recipe_link' : forms.URLInput(attrs={'class':'form-control','placeholder' :'recipe URL'}),
            'image_url' : forms.URLInput(attrs={'class':'form-control','placeholder':'image URL'}),
        }