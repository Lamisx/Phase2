# from django.shortcuts import render
# from rest_framework.response import Response
# from rest_framework.decorators import api_view

# @api_view(['GET'])
# def health_check(request):
#     return Response({"status": "server is running"})
# #تجريبي فقط للتأكد من ان السيرفر شغال

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Device

@api_view(["POST"])
def access_decision(request):

    device_id = request.data.get("device_id")

    try:
        device = Device.objects.get(device_id=device_id)

        if device.status == "TRUSTED":
            return Response({"access": "granted"})
        else:
            return Response({"access": "denied"})

    except Device.DoesNotExist:
        return Response({"access": "unknown_device"}, status=404)