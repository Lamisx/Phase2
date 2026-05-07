from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import UserDelegation, RegistrationSession, AccountUser
from .serializers import StartRegistrationSerializer, AccountSerializer, LoginSerializer, CreateDelegationSerializer, DelegationSerializer
from core.utils import hash_national_id


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
    national_id_hmac=hash_national_id(national_id)
)

    return Response({
        "session_id": str(session.id)
    })

@api_view(["POST"])
def complete_registration(request):
    session = RegistrationSession.objects.get(id=request.data.get("session_id"))

    user = AccountUser.objects.create_user(
        national_id_hmac=session.national_id_hmac,
        username=session.username,
        display_name=session.display_name,
        password=session.password_hash,
        phone=session.phone,
        email=session.email,
    )

    session.status = RegistrationSession.STATUS_COMPLETED
    session.save()

    return Response({
        "message": "User created",
        "user_id": str(user.id)
    })
# register endpoint
@api_view(["POST"])
def register(request):
    serializer = StartRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()

    return Response(
        {
            "message": "User registered successfully.",
            "user": AccountSerializer(user).data
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
            "user": AccountSerializer(user).data
        },
        status=status.HTTP_200_OK
    ) 

@api_view(["POST"])
def create_delegate(request):
    serializer = CreateDelegationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    delegation = serializer.save()

    return Response(
        {
            "message": "Delegate added successfully",
            "delegate": DelegationSerializer(delegation).data
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

    delegations = UserDelegation.objects.filter(
        owner_account_id=primary_user_id

    ).order_by("-created_at")

    serializer = DelegationSerializer(delegations, many=True)
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
        delegation = UserDelegation.objects.get(id=delegate_id)
    except UserDelegation.DoesNotExist:
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