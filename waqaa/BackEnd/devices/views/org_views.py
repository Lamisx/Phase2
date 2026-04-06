from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..serializers import LinkUserSerializer

@api_view(["POST"])
def link_user(request):
    serializer = LinkUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    org_user = serializer.save()

    return Response(
        {
            "message": "User linked to organization successfully.",
            "org_user_id": str(org_user.id),
            "external_user_ref": org_user.external_user_ref,
            "status": org_user.status
        },
        status=status.HTTP_201_CREATED
    )