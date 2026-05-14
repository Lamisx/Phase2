from django.contrib.auth.hashers import make_password
from datetime import timedelta
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)
from core.utils_crypto import hash_national_id
from rest_framework.exceptions import ValidationError
from .models import AccountUser, RegistrationSession



# ============================================================
1. start_registration      # type: ignore
2. verify identity       # type: ignore
3. set_credentials        # type: ignore
4. set_contact           # type: ignore
5. complete_registration # type: ignore
6.create final AccountUer # type: ignore
# ============================================================

class RegistrationService:
  

    @staticmethod
    @transaction.atomic
    def start_registration(*, national_id: str):
        from core.utils_crypto import hash_national_id
        from .models import AccountUser, RegistrationSession

        national_id_hmac = hash_national_id(national_id)

        # رقم هوية موجود مسبقاً كحساب مكتمل → ارفض
        if AccountUser.objects.filter(national_id_hmac=national_id_hmac).exists():
            raise ValidationError({"national_id": "Already registered."})

        # أبطل أي جلسة نشطة قديمة لنفس الرقم
        RegistrationSession.objects.filter(
            national_id_hmac=national_id_hmac,
            status__in=RegistrationSession.ACTIVE_STATUSES,
        ).update(status=RegistrationSession.STATUS_EXPIRED)

        session = RegistrationSession.objects.create(
            national_id_hmac=national_id_hmac,
            status=RegistrationSession.STATUS_PENDING,
        )
        return session

    @staticmethod
    @transaction.atomic
    def mark_identity_verified(*, session_id):
        from .models import RegistrationSession

        try:
            session = RegistrationSession.objects.select_for_update().get(id=session_id)
        except RegistrationSession.DoesNotExist:
            raise NotFound("Registration session not found.")

        if session.is_expired:
            session.status = RegistrationSession.STATUS_EXPIRED
            session.save(update_fields=["status", "updated_at"])
            raise ValidationError({"detail": "Session expired."})

        if session.status != RegistrationSession.STATUS_PENDING:
            raise ValidationError({"detail": "Session not in pending state."})

        session.status = RegistrationSession.STATUS_IDENTITY_VERIFIED
        session.save(update_fields=["status", "updated_at"])
        return session

    @staticmethod
    @transaction.atomic
    def complete_registration(*, session_id, username, display_name, password, phone, email=None):

        try:
            session = RegistrationSession.objects.select_for_update().get(id=session_id)
        except RegistrationSession.DoesNotExist:
            raise NotFound("Registration session not found.")

        if session.is_expired:
            session.status = RegistrationSession.STATUS_EXPIRED
            session.save(update_fields=["status", "updated_at"])
            raise ValidationError({"detail": "Session expired."})

        if session.status != RegistrationSession.STATUS_IDENTITY_VERIFIED:
            raise ValidationError({"detail": "Identity not verified yet."})

        # تحقق من تكرار الحقول قبل الإنشاء
        if AccountUser.objects.filter(username=username).exists():
            raise ValidationError({"username": "Already taken."})
        if AccountUser.objects.filter(phone=phone).exists():
            raise ValidationError({"phone": "Already registered."})
        if email and AccountUser.objects.filter(email=email).exists():
            raise ValidationError({"email": "Already registered."})

        # أنشئ الحساب — كلمة المرور تُجزَّأ هنا فقط
        account = AccountUser.objects.create_user(
            username=username,
            password=password,
            display_name=display_name,
            phone=phone,
            email=email or None,
            national_id_hmac=session.national_id_hmac,
        )

        # أكمل الجلسة واربطها بالحساب
        session.status = RegistrationSession.STATUS_COMPLETED
        session.account = account
        session.username = username
        session.display_name = display_name
        session.phone = phone
        session.email = email or None
        # password_hash يبقى None — الحساب الفعلي يحوي الـ hash
        session.save(update_fields=[
            "status", "account", "username", "display_name",
            "phone", "email", "updated_at",
        ])
        return session, account
    
    @staticmethod
    def set_credentials(*, session_id, username, password):


        try:
            session = RegistrationSession.objects.get(id=session_id)

        except RegistrationSession.DoesNotExist:
            raise ValidationError("Invalid registration session")


        if session.status != RegistrationSession.STATUS_IDENTITY_VERIFIED:
            raise ValueError("Session not verified")

        session.username = username.strip().lower()

        session.password_hash = make_password(password)

        session.save(update_fields=[
            "username",
            "password_hash",
        ])

        return session

    @staticmethod
    def set_contact(*, session_id, phone, email):

        try:
            session = RegistrationSession.objects.get(id=session_id)

        except RegistrationSession.DoesNotExist:
            raise ValidationError("Invalid registration session")


        session.phone = phone
        session.email = email

        session.save(update_fields=[
            "phone",
            "email",
        ])

        return session
    

class AccountService:

    @staticmethod
    @transaction.atomic
    def register_account(*, username, display_name, email, phone, national_id, password):
        
        national_id_hmac = hash_national_id(national_id)

        # فحوصات تكرار
        if AccountUser.objects.filter(username=username).exists():
            raise ValidationError({"username": "Already taken."})
        if email and AccountUser.objects.filter(email=email).exists():
            raise ValidationError({"email": "Already registered."})
        if phone and AccountUser.objects.filter(phone=phone).exists():
            raise ValidationError({"phone": "Already registered."})
        if AccountUser.objects.filter(national_id_hmac=national_id_hmac).exists():
            raise ValidationError({"national_id": "Already registered."})

        try:
            account = AccountUser.objects.create_user(
                username=username,
                password=password,
                display_name=display_name,
                email=email or None,
                phone=phone,
                national_id_hmac=national_id_hmac,
            )
        except IntegrityError as exc:
            raise ValidationError({"detail": "Conflict creating account."}) from exc

        return account


class DelegationService:

    DEFAULT_EXPIRY_DAYS = 30

    @staticmethod
    @transaction.atomic
    def create_delegation(*, owner: AccountUser, delegated_account_id,
                            delegation_method, expires_at=None):

        if owner.id == delegated_account_id:
            raise ValidationError(
                {"delegated_account_id": "Cannot delegate to self."}
            )

        try:
            delegated = AccountUser.objects.get(
                id=delegated_account_id,
                status=AccountUser.STATUS_ACTIVE,
            )
        except AccountUser.DoesNotExist:
            raise NotFound("Delegated account not found or not active.")

        # هل في تفويض نشط بالفعل؟
        already_exists = UserDelegation.objects.filter(
            owner_account=owner,
            delegated_account=delegated,
            status=UserDelegation.STATUS_ACTIVE,
        ).exists()
        if already_exists:
            raise ValidationError({"detail": "Active delegation already exists."})

        # default expiry
        if expires_at is None:
            expires_at = timezone.now() + timedelta(days=DelegationService.DEFAULT_EXPIRY_DAYS)

        delegation = UserDelegation(
            owner_account=owner,
            delegated_account=delegated,
            delegation_method=delegation_method,
            expires_at=expires_at,
            status=UserDelegation.STATUS_ACTIVE,
        )
        try:
            delegation.full_clean()  # يستدعي clean() ويفحص constraints
            delegation.save()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict) from exc

        return delegation

    @staticmethod
    def list_delegations(*, owner: AccountUser):
        return (
            UserDelegation.objects
            .filter(owner_account=owner)
            .select_related("owner_account", "delegated_account")
            .order_by("-created_at")
        )

    @staticmethod
    @transaction.atomic
    def revoke_delegation(*, delegation_id, owner: AccountUser):
        try:
            delegation = UserDelegation.objects.select_for_update().get(id=delegation_id)
        except UserDelegation.DoesNotExist:
            raise NotFound("Delegation not found.")

        if delegation.owner_account_id != owner.id:
            raise PermissionDenied("Not the delegation owner.")

        if delegation.status != UserDelegation.STATUS_ACTIVE:
            raise ValidationError({"detail": "Delegation is not active."})

        delegation.status = UserDelegation.STATUS_REVOKED
        delegation.revoked_at = timezone.now()
        delegation.save(update_fields=["status", "revoked_at", "updated_at"])
        return delegation

    @staticmethod
    def find_active_delegation(*, owner: AccountUser, delegated: AccountUser):
        return (
            UserDelegation.objects
            .filter(
                owner_account=owner,
                delegated_account=delegated,
                status=UserDelegation.STATUS_ACTIVE,
            )
            .filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
            )
            .first()
        )


