import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)

    class Meta:
        abstract = True


class Department(BaseModel):
    name = models.CharField(max_length=150, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "departments"

    def __str__(self):
        return self.name


class Employee(AbstractUser):
    class Role(models.TextChoices):
        STAFF = "staff", "Staff"
        MANAGER = "manager", "Manager"

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    email = models.EmailField(max_length=254, unique=True, blank=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    username = models.CharField(max_length=150, blank=True)
    role = models.CharField(choices=Role.choices, max_length=20, default=Role.STAFF)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
        related_query_name="employee",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "username"]  # noqa: RUF012

    class Meta:
        db_table = "employees"
        indexes = [  # noqa: RUF012
            models.Index(fields=["email"], name="idx_employee_email"),
            models.Index(fields=["first_name"], name="idx_employee_first_name"),
            models.Index(fields=["last_name"], name="idx_employee_last_name"),
            models.Index(fields=["date_joined"], name="idx_employee_date_joined"),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Shift(BaseModel):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="shifts",
        related_query_name="shift",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        db_table = "shifts"
        indexes = [  # noqa: RUF012
            models.Index(fields=["start_time"], name="idx_shift_start_time"),
            models.Index(fields=["end_time"], name="idx_shift_end_time"),
        ]


class ShiftClaim(BaseModel):
    shift = models.OneToOneField(
        Shift,
        related_name="shift_claims",
        related_query_name="shift_claim",
        on_delete=models.CASCADE,
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="claimed_by_shift_claims",
        related_query_name="claimed_by_shift_claim",
    )
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shift_claims"
        indexes = [  # noqa: RUF012
            models.Index(fields=["created_at"], name="idx_shift_claim_created_at"),
        ]


class SwapRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        ACCEPTED_BY_TARGET = "accepted_by_target", "Accepted_By_Target"

    requesting_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requesting_swap_requests",
        related_query_name="requesting_swap_request",
    )
    requesting_shift = models.OneToOneField(
        Shift,
        related_name="+",
        on_delete=models.CASCADE,
    )
    target_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="target_swap_requests",
        related_query_name="target_swap_request",
    )
    target_shift = models.ForeignKey(
        Shift,
        related_name="+",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, db_index=True, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "swap_requests"
        indexes = [  # noqa: RUF012
            models.Index(fields=["created_at"], name="idx_swap_request_created_at"),
            models.Index(fields=["resolved_at"], name="idx_swap_request_resolved_at"),
        ]
