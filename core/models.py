# models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(AbstractUser):
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=10, choices=[
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ], blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email


class MoodCategory(models.Model):
    """Pre-defined mood categories"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    emoji = models.CharField(max_length=5, blank=True, null=True)  # For UI representation
    
    class Meta:
        verbose_name_plural = "Mood Categories"
    
    def __str__(self):
        return self.name


class MoodEntry(models.Model):
    """User's mood entry"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    mood_category = models.ForeignKey(MoodCategory, on_delete=models.SET_NULL, null=True)
    
    # Mood intensity
    mood_intensity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="1=Very Low, 10=Very High"
    )
    
    # Additional context
    stress_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="1=Very Relaxed, 10=Very Stressed"
    )
    
    energy_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="1=Very Tired, 10=Very Energetic"
    )
    
    # User's specific feelings/notes
    specific_feelings = models.TextField(
        blank=True, 
        null=True,
        help_text="Describe what you're feeling in detail"
    )
    
    # Physical conditions
    hunger_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="1=Not hungry, 10=Very hungry"
    )
    
    craving = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Specific food craving (if any)"
    )
    
    # Time/context
    time_of_day = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning (6AM-12PM)'),
            ('afternoon', 'Afternoon (12PM-5PM)'),
            ('evening', 'Evening (5PM-9PM)'),
            ('night', 'Night (9PM-6AM)')
        ]
    )
    
    weather = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Current weather condition"
    )
    
    # Entry metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Mood Entries"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.mood_category} - {self.created_at.date()}"


class FoodCategory(models.Model):
    """Food categories"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Food Categories"
    
    def __str__(self):
        return self.name


class FoodItem(models.Model):
    """Food items database"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(FoodCategory, on_delete=models.SET_NULL, null=True)
    
    # Nutritional info (optional, can be added later)
    calories = models.IntegerField(blank=True, null=True)
    prep_time = models.IntegerField(help_text="Preparation time in minutes", blank=True, null=True)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard')
        ],
        blank=True,
        null=True
    )
    
    # Mood associations (for AI training/initial data)
    associated_moods = models.ManyToManyField(
        MoodCategory, 
        through='MoodFoodAssociation',
        blank=True
    )
    
    recipe_link = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.name


class MoodFoodAssociation(models.Model):
    """Association between moods and foods"""
    mood_category = models.ForeignKey(MoodCategory, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    strength = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="How strongly this food is associated with the mood"
    )
    reason = models.TextField(help_text="Why this food is recommended for this mood")
    
    class Meta:
        unique_together = ['mood_category', 'food_item']
    
    def __str__(self):
        return f"{self.mood_category} → {self.food_item}"


class FoodRecommendation(models.Model):
        """AI-generated food recommendations for mood entries"""
        mood_entry = models.OneToOneField(MoodEntry, on_delete=models.CASCADE, related_name='recommendation')
        
        # Recommended foods
        primary_recommendation = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True, 
                                                related_name='primary_recommendations')
        alternative_recommendations = models.ManyToManyField(FoodItem, blank=True)
        
        # AI response
        ai_explanation = models.TextField(help_text="AI's explanation for the recommendation")
        
        # User feedback
        user_feedback = models.CharField(
            max_length=20,
            choices=[
                ('liked', 'Liked'),
                ('neutral', 'Neutral'),
                ('disliked', 'Disliked'),
                ('tried', 'Tried'),
                ('not_tried', 'Not Tried')
            ],
            default='not_tried'
        )
        
        user_rating = models.IntegerField(
            validators=[MinValueValidator(1), MaxValueValidator(5)],
            null=True,
            blank=True
        )
        
        user_comments = models.TextField(blank=True, null=True)
        
        # Metadata
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        class Meta:
            ordering = ['-created_at']
        
        def __str__(self):
            return f"Recommendation for {self.mood_entry.user.username} on {self.created_at.date()}"
