from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..serializers import RegisterSerializer, UserSerializer, LoginSerializer


@api_view(["GET"])
def health_check(request):
    return Response({"status": "server is running"})


@api_view(["POST"])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()

    return Response(
        {
            "message": "User registered successfully.",
            "user": UserSerializer(user).data
        },
        status=status.HTTP_201_CREATED
    )

@api_view(["POST"])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]

    return Response(
        {
            "message": "Login successful.",
            "user": UserSerializer(user).data
        },
        status=status.HTTP_200_OK
    )