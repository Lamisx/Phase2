from django.utils import timezone
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import DelegatedAccess , RegistrationSession , WaqaUser
from django.contrib.auth.hashers import make_password

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    LoginSerializer,
    AddDelegateSerializer,
    DelegateSerializer,
)
@api_view(["GET"])
def health_check(request):
    return Response({"status": "server is running"})

#تحقق من الهوية في عملية انشاء حساب

@api_view(["POST"])
def start_registration(request):
    national_id = request.data.get("national_id")

    # ✅ validation
    if not national_id:
        return Response(
            {"error": "national_id is required"},
            status=400
        )

    session = RegistrationSession.objects.create(
        national_id=national_id
    )

    return Response({
        "session_id": str(session.id)
    })

@api_view(["POST"])
def mock_nafath(request):
    session_id = request.data.get("session_id")
    national_id = request.data.get("national_id")

    if not session_id:
        return Response({"error": "session_id required"}, status=400)

    session = RegistrationSession.objects.get(id=session_id)

    time.sleep(3)

    if national_id.startswith("1"):
        session.is_verified = True
        session.status = "nafath_verified"
        session.save()

        return Response({
            "verified": True,
            "message": "Nafath verification successful"
        })
    else:
        return Response({
            "verified": False,
            "message": "Nafath verification failed"
        }, status=400)
    
@api_view(["POST"])
def set_credentials(request):
    session = RegistrationSession.objects.get(id=request.data.get("session_id"))

    if not session.is_verified:
        return Response({"error": "Not verified"}, status=400)

    session.username = request.data.get("username")
    session.password = make_password(request.data.get("password"))  
    session.save()

    return Response({"message": "Saved"})

@api_view(["POST"])
def set_contact(request):
    session = RegistrationSession.objects.get(id=request.data.get("session_id"))

    session.phone = request.data.get("phone")
    session.email = request.data.get("email")
    session.save()

    return Response({"message": "Saved"})

@api_view(["POST"])
def complete_registration(request):
    session = RegistrationSession.objects.get(id=request.data.get("session_id"))

    user = WaqaUser.objects.create(
        national_id=session.national_id,
        username=session.username,
        password=session.password,
        phone=session.phone,
        email=session.email,
    )

    session.status = "completed"
    session.save()

    return Response({
        "message": "User created",
        "user_id": str(user.id)
    })
# register endpoint
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
# log in endpoint
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

@api_view(["POST"])
def create_delegate(request):
    serializer = AddDelegateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    delegation = serializer.save()

    return Response(
        {
            "message": "Delegate added successfully",
            "delegate": DelegateSerializer(delegation).data
        },
        status=status.HTTP_201_CREATED
    )#

@api_view(["GET"])
def list_delegates(request):
    primary_user_id = request.query_params.get("primary_user_id")

    if not primary_user_id:
        return Response(
            {"error": "primary_user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    delegations = DelegatedAccess.objects.filter(
        primary_user_id=primary_user_id
    ).order_by("-created_at")

    serializer = DelegateSerializer(delegations, many=True)
    return Response(
        {
            "count": len(serializer.data),
            "delegates": serializer.data
        },
        status=status.HTTP_200_OK
    )

@api_view(["DELETE"])
def delete_delegate(request, delegate_id):
    try:
        delegation = DelegatedAccess.objects.get(id=delegate_id)
    except DelegatedAccess.DoesNotExist:
        return Response(
            {"error": "Delegation not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    delegation.status = "revoked"
    delegation.revoked_at = timezone.now()
    delegation.save()

    return Response(
        {"message": "Delegation revoked successfully"},
        status=status.HTTP_200_OK
    )