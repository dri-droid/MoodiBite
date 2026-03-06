# import requests
# import json
# from django.conf import settings

# url = 'https://openrouter.ai/api/v1/chat/completions'

# def OpenRouter(model='openai/gpt-oss-120b:free'):
#     prompt = f"""
#     User mood category : Happy
#     Mood intensity : 7
#     Stress level : 6
#     Energy level : 3
#     Hunger level : 5
#     Craving : Comfort food
#     Time of the day : Afternoon
#     Weather : Cold

#     Suggest 3 quick and easy food options.
#     """
#     data={
#         "model" : model,
#          "messages" : [{"role":"user","content" : prompt}]
#         }
    
#     headers = {"Authorization":f"Bearer {settings.OPENROUTER_API_KEY}",
#             "Content-Type": "application/json",
#             "HTTP-Referer": "http://localhost:8000",
#             "X-Title": "MoodiBite"
#             }
#     response = requests.post(url,json=data,headers=headers)
#     return response.json()["choices"][0]["message"]["content"]