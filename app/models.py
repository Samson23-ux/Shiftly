import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)

    class Meta:
        abstract = True


class Department(BaseModel):
    name = models.CharField(max_length=150, unique=True)
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
    email = models.EmailField(max_length=254, unique=True, editable=False)
    role = models.CharField(choices=Role.choices, max_length=20, default=Role.STAFF)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
        related_query_name="employee",
    )

    USERNAME_FIELD = "email"

    class Meta:
        db_table = "employees"

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.name


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
        related_query_name="claimed_by_sshift_claim",
    )
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shift_claims"

    def __str__(self):
        return self.name


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
        null=True,
        on_delete=models.CASCADE,
        related_name="target_swap_requests",
        related_query_name="target_swap_request",
    )
    target_shift = models.ForeignKey(
        Shift,
        null=True,
        related_name="+",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, db_index=True, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "swap_requests"

    def __str__(self):
        return self.name
