from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET', 'POST'])
def test_api(request):
    if request.method == 'POST':
        data = request.data
        return Response({"status": "Muvaffaqiyatli!", "qabul_qilindi": data})
    return Response({"message": "Django API ishlamoqda!"})