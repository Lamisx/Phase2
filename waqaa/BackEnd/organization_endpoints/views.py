from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import LinkUserSerializer
from .permissions import require_scope
from .models import OrganizationUser




@api_view(["POST"])
@require_scope("session:create")
def link_user(request):

    # ✅ Validate request
    serializer = LinkUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    organization = serializer.validated_data['organization']

    # 🔐 RBAC: فقط admin يقدر يربط مستخدم
    is_admin = OrganizationUser.objects.filter(
        user=request.user,
        organization=organization,
        role='admin'
    ).exists()

    if not is_admin:
        return Response(
            {"error": "You are not allowed to link users to this organization"},
            status=status.HTTP_403_FORBIDDEN
        )

    # ✅ إنشاء الربط
    org_user = serializer.save(
        linked_by=request.user
    )

    # ✅ response نظيف
    return Response(
        {
            "message": "User linked to organization successfully.",
            "org_user_id": str(org_user.id),
            "external_user_ref": org_user.external_user_ref,
            "status": org_user.status
        },
        status=status.HTTP_201_CREATED
    )