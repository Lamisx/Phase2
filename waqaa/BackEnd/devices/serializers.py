from rest_framework import serializers
from .models import WaqaUser, Device,DelegatedAccess,VerificationSession,DeviceKey
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from .utils import hash_national_id
from rest_framework import serializers



   #------------
    # auth
    #-----------
class RegisterSerializer(serializers.Serializer):

    username     = serializers.CharField(required=True)
    display_name = serializers.CharField(required=False, allow_blank=True)
    email        = serializers.EmailField(required=False, allow_blank=True)
    phone        = serializers.CharField(required=False, allow_blank=True)
    national_id  = serializers.CharField(required=True)


    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8
    )
    #Vald..

    def validate_username(self, value):

        if WaqaUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")

        return value


    def validate_email(self, value):

        if value and WaqaUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")

        return value
    
    def validate_phone(self, value):

        if value and WaqaUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already registered.")

        return value
    def validate_national_id(self, value):
        national_id_hmac = hash_national_id(value)

        if WaqaUser.objects.filter(national_id_hmac=national_id_hmac).exists():
            raise serializers.ValidationError("National ID already registered.")

        return value


    def create(self, validated_data):

        password = validated_data.pop("password")
        national_id = validated_data.pop("national_id")
         # تحويل national_id إلى HMAC
        national_id_hmac = hash_national_id(national_id)

        user = WaqaUser.objects.create(
            password_hash = make_password(password),
             # تحويل national_id إلى HMAC
            national_id_hmac = hash_national_id(national_id),
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
    
    #------------
    # Device
    #-----------
class DeviceCreateSerializer(serializers.Serializer):

    user_id = serializers.UUIDField(required=True)
    label = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=True)
    app_instance_id = serializers.CharField(required=False, allow_blank=True)

class DeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Device
        fields = [
            "id",
            "label",
            "platform",
            "app_instance_id",
            "is_active",
            "created_at"
        ]

#---------------
# delegation
#---------------


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

        # لا يمكن تفويض نفسك
        if primary_user.id == delegate_user.id:
            raise serializers.ValidationError("You cannot delegate yourself.")

        # التأكد أنه لا يوجد تفويض مكرر
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

#------------------------
# session& challenge endpoint
#------------------------

class CreateSessionSerializer(serializers.Serializer):

    organization_api_key = serializers.CharField(required=True)
    external_user_ref = serializers.CharField(required=True)
    org_operation_ref = serializers.CharField(required=True)
    operation_type = serializers.CharField(required=True)


class VerifySessionSerializer(serializers.Serializer):

    device_id = serializers.UUIDField()
    signature = serializers.CharField()


    #-----------
    # the لب
    #-----------

class DeviceKeyCreateSerializer(serializers.Serializer):

    organization_id = serializers.UUIDField()

    public_key = serializers.CharField()

    algorithm = serializers.ChoiceField(choices=["Ed25519"])# نوع الخوارزميه المستعمله للنحدي

    key_format = serializers.ChoiceField(choices=["RAW"])

    key_purpose = serializers.ChoiceField(choices=["auth"]  )
    
# للمنظمه تعرف حاله السيشن
class SessionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationSession
        fields = [
            "id",
            "status",
            "operation_type",
            "org_operation_ref",
            "verified_at",
            "expires_at",
            "failure_reason",
        ]


class RegisterDeviceKeySerializer(serializers.Serializer):
    device_id = serializers.UUIDField()
    organization_id = serializers.UUIDField()
    public_key = serializers.CharField()
    algorithm = serializers.ChoiceField(choices=["Ed25519"])
    key_format = serializers.ChoiceField(choices=["RAW"])

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WaqaUser
        fields = ['id', 'username', 'display_name', 'email', 'phone', 'status', 'created_at']

#------------------
#
#------------------
class DeviceKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceKey
        fields = [
            "id",
            "organization",
            "key_purpose",
            "algorithm",
            "key_format",
            "is_active",
            "created_at",
            "revoked_at",
            "revocation_reason",
        ]