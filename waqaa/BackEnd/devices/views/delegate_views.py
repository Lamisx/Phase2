from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import DelegatedAccess
from ..serializers import AddDelegateSerializer, DelegateSerializer


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