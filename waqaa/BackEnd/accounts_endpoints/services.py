from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)
import secrets 
 
from core.utils_crypto import hash_national_id
 
from .models import AccountUser, RegistrationSession, UserDelegation,DelegationCode
 
 
# ============================================================
# RegistrationService
# ============================================================

class RegistrationService:
  

    @staticmethod
    @transaction.atomic
    def start_registration(*, national_id: str):

        national_id_hmac = hash_national_id(national_id)

        # National ID already linked to a completed account → reject.
        if AccountUser.objects.filter(national_id_hmac=national_id_hmac).exists():
            raise ValidationError({"national_id": "Already registered."})

        # Expire any older active sessions for this national_id.
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
    def set_credentials(*, session_id, username, password) -> RegistrationSession:
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
 
        session.username = username.strip().lower()
        session.password_hash = make_password(password)
        session.save(update_fields=["username", "password_hash", "updated_at"])
        return session
    

    @staticmethod
    @transaction.atomic
    def set_contact(*, session_id, phone, email):

        try:
            session = RegistrationSession.objects.select_for_update().get(id=session_id)

        except RegistrationSession.DoesNotExist:
            raise NotFound("Registration session not found.")

        if session.is_expired:
            session.status = RegistrationSession.STATUS_EXPIRED
            session.save(update_fields=["status", "updated_at"])
            raise ValidationError({"detail": "Session expired."})

        session.phone = phone
        session.email = email or None
        session.save(update_fields=["phone", "email", "updated_at"])
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

        # Duplicate checks before creation (clearer errors than IntegrityError).
        if AccountUser.objects.filter(username=username).exists():
            raise ValidationError({"username": "Already taken."})
        if AccountUser.objects.filter(phone=phone).exists():
            raise ValidationError({"phone": "Already registered."})
        if email and AccountUser.objects.filter(email=email).exists():
            raise ValidationError({"email": "Already registered."})

        # create_user calls set_password() → password is hashed here, once.
        account = AccountUser.objects.create_user(
            username=username,
            password=password,
            display_name=display_name,
            phone=phone,
            email=email or None,
            national_id_hmac=session.national_id_hmac,
        )
        
        # Complete the session, link it to the account, and clear the
        session.status = RegistrationSession.STATUS_COMPLETED
        session.account = account
        session.username = username
        session.display_name = display_name
        session.phone = phone
        session.email = email or None
        session.save(update_fields=[
            "status", "account", "username", "display_name",
            "phone", "email", "updated_at",
        ])
        return session, account
    
# ============================================================
# AccountService
# ============================================================
class AccountService:

    @staticmethod
    @transaction.atomic
    def register_account(*, username, display_name, email, phone, national_id, password)-> AccountUser:
        
        national_id_hmac = hash_national_id(national_id)

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


# ============================================================
# DelegationService
# ============================================================
class DelegationService:

    DEFAULT_EXPIRY_DAYS = 30

    @staticmethod
    @transaction.atomic
    def create_delegation(*, owner: AccountUser, delegated_account_id,
                            delegation_method, expires_at=None)-> UserDelegation:

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
    def revoke_delegation(*, delegation_id, owner: AccountUser) -> UserDelegation:
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
           .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
            .first()
        )


# ============================================================
# DelegationCodeService
# ============================================================
#
class DelegationCodeService:
    """
    رمز تفويض 6 أرقام بين شخصين:
        A يولّد رمز  →  يعطيه لـ B شفهياً  →  B يدخله  →  يُنشأ UserDelegation(A→B)

    قواعد:
      - الرمز يصلح 5 دقائق فقط
      - يُستخدم مرة واحدة (is_used)
      - توليد رمز جديد لـ A يلغي الرموز القديمة غير المستخدمة
      - لا يقدر المستخدم يفوّض نفسه (يُتحقّق ضمن DelegationService.create_delegation)
    """

    CODE_TTL_MINUTES = 5
    DELEGATION_EXPIRY_DAYS = 30  # مدة صلاحية التفويض بعد القبول

    @staticmethod
    @transaction.atomic
    def generate_for(*, owner: AccountUser):
        """
        A يولّد رمزاً جديداً.
        يلغي أي رموز سابقة غير مستخدمة (عشان ما يبقى عند المستخدم رمزان نشطان).
        """
        # نظافة: ألغِ الرموز السابقة (غير مستخدمة) لنفس المستخدم
        DelegationCode.objects.filter(
            owner_account=owner,
            is_used=False,
        ).delete()

        # توليد رمز عشوائي آمن من 6 أرقام (secrets أقوى من random لإنتاج)
        code = f"{secrets.randbelow(1_000_000):06d}"

        dcode = DelegationCode.objects.create(
            owner_account=owner,
            code=code,
            expires_at=timezone.now() + timedelta(
                minutes=DelegationCodeService.CODE_TTL_MINUTES
            ),
        )
        return dcode

    @staticmethod
    @transaction.atomic
    def accept(*, code: str, delegated: AccountUser) -> UserDelegation:
        """
        B يدخل الرمز:
          - يلقى DelegationCode بهذا الرمز (لو موجود وغير منتهي وغير مستخدم)
          - يستخدم DelegationService.create_delegation عشان ينشئ التفويض
            (نفس المسار، نفس constraints — لا تكرار منطق)
          - يحدّد الرمز كـ used
        """
        code = (code or "").strip()
        if len(code) != 6 or not code.isdigit():
            raise ValidationError({"code": "Invalid code format."})

        # ابحث عن الرمز — قفل الصف ضد race conditions
        try:
            dcode = (
                DelegationCode.objects
                .select_for_update()
                .select_related("owner_account")
                .get(code=code, is_used=False)
            )
        except DelegationCode.DoesNotExist:
            raise ValidationError({"code": "Invalid or already used code."})

        # تحقّق من الصلاحية
        if dcode.is_expired:
            raise ValidationError({"code": "Code expired."})

        owner = dcode.owner_account

        # لا يقدر يفوّض نفسه
        if owner.id == delegated.id:
            raise ValidationError({"code": "Cannot accept your own code."})

        # ادمج في DelegationService الموجود (نفس constraints، نفس default expiry)
        delegation = DelegationService.create_delegation(
            owner=owner,
            delegated_account_id=delegated.id,
            delegation_method=UserDelegation.METHOD_OTP,
            expires_at=timezone.now() + timedelta(
                days=DelegationCodeService.DELEGATION_EXPIRY_DAYS
            ),
        )

        # علّم الرمز كمستخدم
        dcode.is_used = True
        dcode.save(update_fields=["is_used"])

        return delegation