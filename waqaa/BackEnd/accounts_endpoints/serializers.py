from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password

from .models import WaqaUser, DelegatedAccess
from core.utils import hash_national_id
from django.core.validators import RegexValidator
import re



#------------
# user 
#-----------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WaqaUser
        fields = ['id', 'username', 'display_name', 'email', 'phone', 'status', 'created_at', 'updated_at']


# ------------------------
# Auth
# ------------------------

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

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    display_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=True, allow_blank=False)
    national_id = serializers.CharField(required=True,write_only=True)
    password = serializers.CharField(required=True,write_only=True,min_length=8)

    

    def validate_username(self, value):
        value = value.strip().lower()
        if WaqaUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_email(self, value):
        if value:
            value = value.strip().lower()
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if not re.match(pattern, value):
                raise serializers.ValidationError("Invalid email format.")
            if WaqaUser.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already registered.")
        return value
    

    
    def validate_phone(self, value):
        if value:
            cleaned = re.sub(r'(?!^\+)\D', '', value.strip())
            phone_regex(cleaned)
            
            if WaqaUser.objects.filter(phone=cleaned).exists():
                raise serializers.ValidationError("Phone number already registered.")
            return cleaned
        return value

    def validate_national_id(self, value):
        national_id_regex(value)
        national_id_hmac = hash_national_id(value)

        if WaqaUser.objects.filter(national_id_hmac=national_id_hmac).exists():
            raise serializers.ValidationError("National ID already registered.")

        return national_id_hmac

    def create(self, validated_data):
        password = validated_data.pop("password")
        national_id_hmac  = validated_data.pop("national_id")

        user = WaqaUser.objects.create(
            password_hash=make_password(password),
            national_id_hmac=national_id_hmac,
            **validated_data
        )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        try:
            user = WaqaUser.objects.get(username=username)
        except WaqaUser.DoesNotExist:
            raise serializers.ValidationError("Invalid username or password.")

        if not user.password_hash:
            raise serializers.ValidationError("This account has no password configured.")

        if not check_password(password, user.password_hash):
            raise serializers.ValidationError("Invalid username or password.")

        data["user"] = user
        return data


# ------------------------
# Delegation
# ------------------------

class DelegateSerializer(serializers.ModelSerializer):
    delegate_username = serializers.CharField(source='delegate_user.username', read_only=True)
    delegate_displayname = serializers.CharField(source='delegate_user.display_name', read_only=True)

    class Meta:
        model = DelegatedAccess
        fields = [
            'id',
            'delegate_user',
            'delegate_username',
            'delegate_displayname',
            'added_via',
            'status',
            'created_at',
            'revoked_at',
        ]


class AddDelegateSerializer(serializers.Serializer):
    primary_user_id = serializers.UUIDField()
    delegate_user_id = serializers.UUIDField()
    added_via = serializers.ChoiceField(choices=['qr', 'otp'])

    def validate(self, data):
        primary_user_id = data["primary_user_id"]
        delegate_user_id = data["delegate_user_id"]

        try:
            primary_user = WaqaUser.objects.get(id=primary_user_id)
        except WaqaUser.DoesNotExist:
            raise serializers.ValidationError("Primary user not found.")

        try:
            delegate_user = WaqaUser.objects.get(id=delegate_user_id)
        except WaqaUser.DoesNotExist:
            raise serializers.ValidationError("Delegate user not found.")

        if primary_user.id == delegate_user.id:
            raise serializers.ValidationError("You cannot delegate yourself.")

        exists = DelegatedAccess.objects.filter(
            primary_user=primary_user,
            delegate_user=delegate_user,
            status="active"
        ).exists()

        if exists:
            raise serializers.ValidationError("This user is already delegated.")

        data["primary_user"] = primary_user
        data["delegate_user"] = delegate_user
        return data

    def create(self, validated_data):
        delegation = DelegatedAccess.objects.create(
            primary_user=validated_data["primary_user"],
            delegate_user=validated_data["delegate_user"],
            added_via=validated_data["added_via"],
            status="active"
        )
        return delegation