from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def health_check(request):
    return Response({"status": "server is running"})
#تجريبي فقط للتأكد من ان السيرفر شغال