import requests
import json
from django.shortcuts import render,redirect, get_object_or_404
from .models import *
from django.http import HttpResponse
from django.conf import settings
from .forms import *
from django.db.models import Q,Avg,Count
from .models import MoodFoodAssociation
from django.contrib.auth import login,authenticate,logout,update_session_auth_hash, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
import re
# from openrouter import OpenRouter


User = get_user_model()
@login_required
def log_mood(request):
    ensure_mood_categories()
    recommendation = None
    if request.method == "POST":
        form = moodEntryForm(request.POST)
        if form.is_valid():
            mood_entry = form.save(commit=False)
            mood_entry.user = request.user
            mood_entry.save()
            try:
                food_names = list(
                FoodItem.objects.values_list('name', flat=True))

                food_list_text = "\n".join(f"- {name}" for name in food_names)


                prompt = f"""
                User mood category :  {form.cleaned_data['mood_category']}
                Mood intensity : {form.cleaned_data['mood_intensity']}
                Stress level : {form.cleaned_data['stress_level']}
                Energy level : {form.cleaned_data['energy_level']}
                Hunger level : {form.cleaned_data['hunger_level']}
                Craving : {form.cleaned_data['craving']}
                Time of the day : {form.cleaned_data['time_of_day']}
                Weather : {form.cleaned_data['weather']}
                 feelings : {form.cleaned_data['specific_feelings']}
                 MUST choose food items ONLY from the list below.
                 NOT invent new food names.
                 NOT modify names.
                Use the names EXACTLY as written.

                AVAILABLE FOODS:{food_list_text}

                Return response in EXACT format:

                PRIMARY: <food name from list>
                ALTERNATIVES:
                - <food name from list>
                - <food name from list>
                EXPLANATION: <short explanation

                """

                url = "https://openrouter.ai/api/v1/chat/completions"

                data = {
                    "model" : "meta-llama/llama-3.3-70b-instruct:free",
                    "messages" : [{"role":"user","content" : prompt}]
                }

                headers = {"Authorization":f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
                }
                response = requests.post(url,json=data,headers=headers)
            
                if response.status_code == 200:
                    food_suggestions = response.json()['choices'][0]['message']['content']
            
                    lines = food_suggestions.splitlines()
                    primary_food = None
                    alternatives = []
                    explanation = ""
                    for line in lines:
                        if line.startswith("PRIMARY:"):
                            primary_food = line.replace("PRIMARY:", "").strip()

                        elif line.startswith("-"):
                            alternatives.append(line.replace("-", "").strip())

                        elif line.startswith("EXPLANATION:"):
                            explanation = line.replace("EXPLANATION:", "").strip()
                

                    primary_item = FoodItem.objects.filter(name=primary_food).first()
                    alt_items = FoodItem.objects.filter(
                            name__in=alternatives)


                    recommendation = FoodRecommendation.objects.create(
                        mood_entry=mood_entry,
                        primary_recommendation=primary_item,
                        ai_explanation=explanation
                    )

                    recommendation.alternative_recommendations.set(alt_items)
            except (requests.RequestException, KeyError, IndexError, ValueError) as e:
                # Handles network/API errors or bad response parsing
                print("AI API Error:", e)
                food_suggestions = "Sorry, could not fetch suggestions at this time."
                recommendation = None
        
            if recommendation:
                request.session['recommendation_id'] = recommendation.id
                return redirect('food_suggestions')
    else:
        form = moodEntryForm()

    return render(request, 'core/log_mood.html', {'form': form})


@login_required
def food_suggestions(request):
    recommendation = None
    recommendation_id = request.session.get('recommendation_id')
    if recommendation_id:
        try:
            recommendation = FoodRecommendation.objects.select_related(
                'mood_entry',
                'primary_recommendation'
            ).prefetch_related(
                'alternative_recommendations'
            ).get(id=recommendation_id)
        except FoodRecommendation.DoesNotExist:
            recommendation = None

    food_history = FoodRecommendation.objects.filter(
        mood_entry__user=request.user
    ).exclude(id=recommendation_id).order_by('-created_at')[:5]

    return render(request, 'core/food_suggestions.html', {
        'recommendation': recommendation,"food_history":food_history
    })

@staff_member_required
def base(request):
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    # 🔹 KPI CARDS
    total_users = UserProfile.objects.count()
    total_entries = MoodEntry.objects.count()

    avg_mood = MoodEntry.objects.aggregate(
        avg=Avg('mood_intensity')
    )['avg'] or 0


    # 🔹 Mood trend (last 30 days)
    mood_trend = (
        MoodEntry.objects
        .filter(created_at__date__gte=last_30_days)
        .values('created_at__date')
        .annotate(avg_mood=Avg('mood_intensity'))
        .order_by('created_at__date')
    )

    trend_labels = [str(item['created_at__date']) for item in mood_trend]
    trend_data = [round(item['avg_mood'], 2) for item in mood_trend]

    # 🔹 Mood category distribution
    mood_distribution = (
        MoodEntry.objects
        .values('mood_category__name', 'mood_category__emoji')
        .annotate(count=Count('id'))
    )

    category_labels = [
        f"{item['mood_category__emoji']} {item['mood_category__name']}"
        for item in mood_distribution
    ]
    category_data = [item['count'] for item in mood_distribution]

    # 🔹 Mood by time of day
    mood_by_time = (
        MoodEntry.objects
        .values('time_of_day')
        .annotate(avg_mood=Avg('mood_intensity'))
    )

    time_labels = [item['time_of_day'] for item in mood_by_time]
    time_data = [round(item['avg_mood'], 2) for item in mood_by_time]

    # 🔹 Low mood alert
    low_mood_count = MoodEntry.objects.filter(mood_intensity__lte=3).count()
    low_mood_percentage = (
        (low_mood_count / total_entries) * 100 if total_entries else 0
    )

    recent_moods = (
    MoodEntry.objects
    .select_related('user', 'mood_category')
    .order_by('-created_at')[:10]
)


    context = {
        "total_users": total_users,
        "total_entries": total_entries,
        "total_predictions" :FoodRecommendation.objects.count(),
        "avg_mood": round(avg_mood, 2),

        "trend_labels": trend_labels,
        "trend_data": trend_data,

        "category_labels": category_labels,
        "category_data": category_data,

        "time_labels": time_labels,
        "time_data": time_data,

        "low_mood_percentage": round(low_mood_percentage, 1),
        "recent_moods" : recent_moods
    }

    return render(request, "core/base.html", context)



@login_required
def index(request):
    if request.user.is_staff:
        return redirect('base')
    return render(request,'core/index.html')

@staff_member_required
def profile(request):
    user = request.user
    form  = profileForm(instance=user)
    if request.method == "POST":
        form = profileForm(request.POST,request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    return render(request,'core/profile.html',{'form':form})

@login_required
def user_profile(request):
    user = request.user
    form  = profileForm(instance=user)
    if request.method == "POST":
        formtype = request.POST.get('form_type')

        if formtype == 'profile':
            form = profileForm(request.POST,request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                redirect('user_profile') 

        elif formtype == 'password':
            old = request.POST.get('old_password')
            new1 = request.POST.get('new_password')
            new2 = request.POST.get('confirm_password')

            if not user.check_password(old):
                messages.error(request, "Old password is incorrect")
            elif new1 != new2:
                messages.error(request, "New passwords do not match")
            else:
                user.set_password(new1)
                user.save()
                update_session_auth_hash(request, user)  # keeps user logged in
                messages.success(request, "Password changed successfully")
                return redirect('user_profile')

    return render(request,'core/user_profile.html',{'form':form})


def sign_in(request):
    if request.method == "POST":
        data = request.POST
        email = data.get('email')
        password = data.get('password')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            user_obj = None
        if user_obj and not user_obj.is_active:
            messages.error(request, "Your account has been deactivated. Please contact admin.")
            return redirect('sign-in')

        user = authenticate(request,username=email,password=password)
        
        if user is not None:
            login(request,user)

            if user.is_staff:
                return redirect('base')
            else:
                return redirect('index')
        else:
            messages.error(request,"Invalid email or password")
            return redirect('sign-in')
    return render(request,'core/sign-in.html')

def sign_up(request):
    if request.method == "POST":
        data = request.POST
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        password2 = data.get('password2')

        if(password!=password2):
            messages.error(request,"Password do not match!")
            return redirect('sign-up')
        
        if UserProfile.objects.filter(username=username).exists():
            messages.error(request,'Username exists!')
            return redirect('sign-up')
        
        user = UserProfile.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        login(request,user)
        return redirect('sign-in')
    return render(request,'core/sign-up.html')


def ensure_mood_categories():
    moods = [
        ("Happy", "😊", "Feeling cheerful and positive"),
        ("Sad", "😔", "Feeling down or upset"),
        ("Stressed", "😫", "Feeling tense or anxious"),
        ("Tired", "😴", "Feeling exhausted or sleepy"),
        ("Relaxed", "😌", "Feeling calm and at ease"),
        ("Excited", "😃", "Feeling thrilled or energetic"),
        ("Bored", "😐", "Feeling uninterested or dull"),
    ]

    for name, emoji, desc in moods:
        MoodCategory.objects.get_or_create(
            name=name,
            defaults={"emoji": emoji, "description": desc}
        )

@staff_member_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request,'core/user_list.html',{'users':users})

@staff_member_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, "You cannot deactivate yourself.")
        return redirect('admin_user_list')

    user.is_active = not user.is_active
    user.save()

    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} {status} successfully.")

    return redirect('user_list')



@staff_member_required
def mood_history(request):
    user = request.user
    selected_user = request.GET.get('user')
    if user.is_staff:
        mood_entries = MoodEntry.objects.all().order_by('-created_at')
        if selected_user:
            mood_entries = mood_entries.filter(user__id=selected_user)

            search = request.GET.get('search')
            if search:
                mood_entries = mood_entries.filter(
                Q(user__username__icontains=search)
            )
    else:
        mood_entries = MoodEntry.objects.filter(user=user).order_by('-created_at')

    mood_entries = mood_entries.order_by('-created_at')
    users = User.objects.all() if user.is_staff else None
    return render(request, 'core/mood_history.html', {
        'mood_entries': mood_entries,'users':users,'selected_user':selected_user
    })

@staff_member_required
def mood_update(request,id):
    mood = MoodEntry.objects.get(id=id)
    form = moodEntryForm(instance=mood)
    if request.method == "POST":
        form = moodEntryForm(request.POST,instance=mood)
        if form.is_valid():
            form.save()
            return redirect('base')
    return render(request,'core/mood_update.html',{'form':form})

@staff_member_required
def mood_delete(request,id):
    mood = MoodEntry.objects.get(id=id)
    if request:
        mood.delete()
        return redirect('mood_history')
    return redirect('mood_history')

@staff_member_required
def food_category(request):
    form = foodCategory()
    categories = FoodCategory.objects.all()
    if request.method == "POST":
        form = foodCategory(request.POST)
        if form.is_valid():
            form.save()
            return redirect('food_category')
    return render(request,'core/food_category.html',{'form':form,'food_categories':categories})

@staff_member_required
def food_update(request,id):
    category = FoodCategory.objects.get(id=id)
    form = foodCategory(instance=category)
    if request.method == "POST":
        form = foodCategory(request.POST,instance=category)
        if form.is_valid():
            form.save()
            return redirect('food_category')
    return render(request,'core/food_cat_update.html',{'form':form})

@staff_member_required
def food_delete(request,id):
    category = FoodCategory.objects.get(id=id)
    if request:
        category.delete()
        return redirect('food_category')
    return redirect('food_category')

@staff_member_required
def food_item(request):
    form = foodItemForm()
    items = FoodItem.objects.all()
    if request.method == "POST":
        form = foodItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('food_item')
    return render(request,'core/food_item.html',{'form':form,'food_items':items})

@staff_member_required
def food_item_update(request,id):
    item = FoodItem.objects.get(id=id)
    form = foodItemForm(instance=item)
    if request.method=="POST":
        form = foodItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('food_item')
    return render(request,'core/food_item_update.html',{'form':form})

@staff_member_required
def food_item_delete(request,id):
    item = FoodItem.objects.get(id=id)
    if request:
        item.delete()
        return redirect('food_item')
    return redirect('food_item')

@staff_member_required
def food_explorer(request):
    items = FoodItem.objects.all()
    if request.method == "POST":
        return redirect('food_explorer')
    return render(request,'core/food_explorer.html',{'items':items})

def log_out(request):
    logout(request)
    return render(request,'core/sign-out.html')


