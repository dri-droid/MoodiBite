from django.urls import path
from core.views import *

urlpatterns = [
    path('',index,name='index'),
    path('base/',base,name='base'),
    path('sign-in/',sign_in,name='sign-in'),
    path('sign-up/',sign_up,name='sign-up'),
    path('sign-out/',log_out, name='sign-out'),
    path('profile/',profile,name='profile'),
    path('user_profile/',user_profile,name='user_profile'),
    path('user_list/',user_list,name='user_list'),
    path('toggle_user_status/<int:user_id>/', toggle_user_status, name='toggle_user_status'),
    path('log_mood/',log_mood,name='log_mood'),
    path('mood_history/',mood_history,name='mood_history'),
    path('mood_update/<int:id>',mood_update,name='mood_update'),
    path('mood_delete/<int:id>',mood_delete,name='mood_delete'),
    path('food_category',food_category,name='food_category'),
    path('food_cat_update/<int:id>',food_update,name='food_cat_update'),
    path('food_cat_del/<int:id>',food_delete,name='food_cat_delete'),
    path('food_item/',food_item,name='food_item'),
    path('food_item_update/<int:id>',food_item_update,name='food_item_update'),
    path('food_item_delete/<int:id>',food_item_delete,name='food_item_delete'),
    path('food_explorer/',food_explorer,name='food_explorer'),
    path('food_suggestions/',food_suggestions,name="food_suggestions"),
]