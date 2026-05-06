from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from core.utils import hash_national_id
from django.core.validators import RegexValidator
from .models import AccountUser, UserDelegation 
import re

# إذا النظام سعودي فقط
phone_regex = RegexValidator(
    regex=r'^05\d{8}$',
    message="رقم الهاتف يجب أن يبدأ بـ 05 ويكون 10 أرقام"
)

#تحقق من الهويه
national_id_regex = RegexValidator(
    regex=r'^\d{10}$',
    message="رقم الهوية يجب أن يكون 10 أرقام"
)

# ============================================================
# StartRegistrationSerializer
# ============================================================
class StartRegistrationSerializer(serializers.Serializer):
    national_id = serializers.CharField(required=True, write_only=True, max_length=10)

    def validate_national_id(self, value):
        value = (value or "").strip()
        national_id_regex(value)
        return value
    
class CompleteRegistrationSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=True)
    username = serializers.CharField(required=True, max_length=20)
    display_name = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(required=True, write_only=True,min_length=8, max_length=128)
    phone = serializers.CharField(required=True, max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    def validate_username(self, value):
        return value.strip().lower()

    def validate_email(self, value):
        if not value:
            return None
        return value.strip().lower()

    def validate_phone(self, value):
        import re
        value = re.sub(r"\D", "", value or "")
        phone_regex(value)
        return value
    

class RegistrationSessionSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    is_final = serializers.BooleanField(read_only=True)

    class Meta:
        from .models import RegistrationSession
        model = RegistrationSession
        fields = [
            "id", "status", "expires_at", "created_at",
            "is_expired", "is_final",
        ]
        read_only_fields = fields

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get("username").strip().lower()
        password = data.get("password")
        try:
            user = AccountUser.objects.get(username=username)
        except AccountUser.DoesNotExist:
            raise serializers.ValidationError("Invalid username or password.")

        if not user.password_hash:
            raise serializers.ValidationError("Invalid username or password.")

        if not check_password(password, user.password_hash):
            raise serializers.ValidationError("Invalid username or password.")

        data["user"] = user
        return data



# ============================================================
# Account
# ============================================================
class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountUser
        fields = [
            "id", "username", "display_name", "email", "phone",
            "status", "created_at", "updated_at",
        ]
        read_only_fields = fields





# ============================================================
# Delegation
# ============================================================
class DelegationSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(
        source="owner_account.username", read_only=True
    )
    delegated_username = serializers.CharField(
        source="delegated_account.username", read_only=True
    )
    delegated_display_name = serializers.CharField(
        source="delegated_account.display_name", read_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserDelegation
        fields = [
            "id",
            "owner_username",
            "delegated_username",
            "delegated_display_name",
            "delegation_method",
            "status",
            "expires_at",
            "revoked_at",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CreateDelegationSerializer(serializers.Serializer):
   
    delegated_account_id = serializers.UUIDField(required=True)
    delegation_method = serializers.ChoiceField(
        choices=[UserDelegation.METHOD_QR, UserDelegation.METHOD_OTP],
        required=True,
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)