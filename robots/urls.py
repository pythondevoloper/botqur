from django.urls import path
from django.http import JsonResponse

def test_api(request):
    return JsonResponse({
        "status": "Muvaffaqiyatli",
        "message": "BotQur API include orqali ishlamoqda!"
    })

urlpatterns = [
    path('test/', test_api),  
]