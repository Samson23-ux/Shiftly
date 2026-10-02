from datetime import UTC, datetime

from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from . import models as AppModels
from . import serializers as AppSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    lookup_url_kwarg = "id"
    queryset = AppModels.Employee.objects.all()
    ordering_fields = ["first_name", "last_name", "date_joined"]  # noqa: RUF012
    ordering = ["date_joined"]  # noqa: RUF012
    filterset_fields = ["email", "first_name", "last_name", "date_joined"]  # noqa: RUF012
    serializer_class = AppSerializer.EmployeeReadSerializer

    def get_permissions(self):
        permission_classes = []
        if self.action in ["list", "retrieve", "partial_update", "destroy"]:
            permission_classes.append(IsAuthenticated)

            if self.action == "list":
                permission_classes.append(IsAdminUser)
        return [p() for p in permission_classes]

    def get_queryset(self):
        return AppModels.Employee.objects.filter(role="staff")

    def create(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()

        serializer = AppSerializer.EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        department = AppModels.Department.objects.filter(
            name=serializer.validated_data["department"]
        ).first()

        if not department:
            return Response(
                data={"status": "error", "message": "Department not found"},
                status=404,
            )

        serializer.validated_data["department"] = department

        if not serializer.validated_data.get("username"):
            serializer.validated_data["username"] = (
                serializer.validated_data["first_name"]
                + " "
                + serializer.validated_data["last_name"]
            )

        saved_employee = serializer.save()
        return Response(
            data={
                "status": "success",
                "message": "Employee created successfully",
                "data": read_serializer(saved_employee).data,
            },
            status=201,
        )

    def list(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        employees = self.get_queryset()

        if not employees:
            return Response(
                data={"status": "error", "message": "Employees not found"},
                status=404,
            )

        return Response(
            data={
                "status": "success",
                "message": "Employee list retrieved successfully",
                "data": read_serializer(employees, many=True).data,
            },
            status=200,
        )

    def retrieve(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        return Response(
            data={
                "status": "success",
                "message": "Employee retrieved successfully",
                "data": read_serializer(request.user).data,
            },
            status=200,
        )

    def partial_update(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        employee = self.get_object()

        serializer = AppSerializer.EmployeeUpdateSerializer(
            employee, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        updated_employee = serializer.save()
        return Response(
            data={
                "status": "success",
                "message": "Employee updated successfully",
                "data": read_serializer(updated_employee).data,
            },
            status=200,
        )

    def destroy(self, request, *args, **kwargs):
        employee = self.get_object()

        employee.is_active = False
        employee.save()

        return Response(
            data={
                "status": "success",
                "message": "Employee deactivated successfully",
            },
            status=204,
        )

    @action(methods=["patch"], detail=True)
    def reactivate(self, request, id=None):
        employee = AppModels.Employee.objects.filter(pk=id).first()

        if not employee:
            return Response(
                data={
                    "status": "success",
                    "message": "Employee not found",
                },
                status=404,
            )

        read_serializer = self.get_serializer()

        if not employee.is_active:
            employee.is_active = True
            employee.save()

        serializer = read_serializer(employee)

        return Response(
            data={
                "status": "success",
                "message": "Employee reactivated successfully",
                "data": serializer.data,
            },
            status=200,
        )


class ShiftViewSet(viewsets.ModelViewSet):
    lookup_url_kwarg = "id"
    queryset = AppModels.Shift.objects.all()
    ordering_fields = ["start_time", "end_time"]  # noqa: RUF012
    ordering = ["start_time"]  # noqa: RUF012
    serializer_class = AppSerializer.ShiftReadSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_permissions(self):
        permission_classes = []
        if self.action in ["create", "partial_update", "destroy"]:
            permission_classes.append(IsAdminUser)
        return [p() for p in permission_classes]

    def create(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()

        serializer = AppSerializer.ShiftCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        department = AppModels.Department.objects.filter(
            name=serializer.validated_data["department"]
        ).first()

        if not department:
            return Response(
                data={"status": "error", "message": "Department not found"},
                status=404,
            )

        saved_shift = serializer.save(created_by=request.user)

        return Response(
            data={
                "status": "success",
                "message": "Shift created successfully",
                "data": read_serializer(saved_shift).data,
            },
            status=201,
        )

    def list(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        shifts = self.get_queryset()

        if not shifts:
            return Response(
                data={"status": "error", "message": "Shifts not found"},
                status=404,
            )

        return Response(
            data={
                "status": "success",
                "message": "Shift list retrieved successfully",
                "data": read_serializer(shifts, many=True).data,
            },
            status=200,
        )

    def retrieve(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        shift = self.get_object()

        return Response(
            data={
                "status": "success",
                "message": "Shift retrieved successfully",
                "data": read_serializer(shift).data,
            },
            status=200,
        )

    def partial_update(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        shift = AppModels.Shift.objects.filter(pk=self.kwargs["id"]).first()

        if not shift:
            return Response(
                data={"status": "error", "message": "Shift not found"},
                status=404,
            )

        serializer = AppSerializer.ShiftUpdateSerializer(shift, data=request.data)
        serializer.is_valid(raise_exception=True)

        saved_shift = serializer.save()
        return Response(
            data={
                "status": "success",
                "message": "Shift updated successfully",
                "data": read_serializer(saved_shift).data,
            },
            status=200,
        )

    def destroy(self, request, *args, **kwargs):
        shift = AppModels.Shift.objects.filter(pk=self.kwargs["id"]).first()

        if not shift:
            return Response(
                data={"status": "error", "message": "Shift not found"},
                status=404,
            )

        AppModels.Shift.objects.delete(shift)
        return Response(
            data={
                "status": "success",
                "message": "Shift deleted successfully",
            },
            status=204,
        )


class ShiftClaimViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    queryset = AppModels.ShiftClaim.objects.all()
    ordering_fields = ["created_at"]  # noqa: RUF012
    ordering = ["created_at"]  # noqa: RUF012
    serializer_class = AppSerializer.ShiftClaimReadSerializer

    def get_queryset(self):
        return AppModels.ShiftClaim.objects.filter(claimed_by_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        shift = AppModels.Shift.objects.filter(pk=self.kwargs["shift_id"]).first()

        if not shift:
            return Response(
                data={"status": "error", "message": "Shift not found"},
                status=404,
            )

        if shift.end_time <= datetime.now(UTC):
            return Response(
                data={"status": "error", "message": "Requesting shift already ended"},
                status=400,
            )

        create_claim = AppModels.ShiftClaim(
            shift_id=shift.id, claimed_by_id=request.user.id
        )
        AppModels.ShiftClaim.objects.bulk_create(
            [create_claim],
            update_conflicts=True,
            unique_fields=["shift"],
            update_fields=["shift"],
        )

        inserted_claim = AppModels.ShiftClaim.objects.filter(shift_id=shift.id).first()
        if inserted_claim.claimed_by_id != request.user.id:
            return Response(
                data={
                    "status": "error",
                    "message": "Shift already claimed by another staff",
                },
                status=409,
            )

        return Response(
            data={
                "status": "success",
                "message": "Shift claimed successfully",
                "data": read_serializer(inserted_claim).data,
            },
            status=201,
        )

    def list(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        claims = self.get_queryset()

        if not claims:
            return Response(
                data={"status": "error", "message": "Shift claims not found"},
                status=404,
            )

        return Response(
            data={
                "status": "success",
                "message": "Claim list retrieved successfully",
                "data": read_serializer(claims, many=True).data,
            },
            status=200,
        )

    def retrieve(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        claim = AppModels.ShiftClaim.objects.filter(pk=self.kwargs["claim_id"]).first()

        if not claim:
            return Response(
                data={"status": "error", "message": "Shift claim not found"},
                status=404,
            )

        return Response(
            data={
                "status": "success",
                "message": "Shift claim retrieved successfully",
                "data": read_serializer(claim).data,
            },
            status=200,
        )

    def destroy(self, request, *args, **kwargs):
        claim = (
            AppModels.ShiftClaim.objects.select_related("shift")
            .filter(pk=self.kwargs["claim_id"])
            .first()
        )

        if (
            claim.shift.created_by_id != request.user.id
            and request.user.role != "manager"
        ):
            return Response(
                data={
                    "status": "error",
                    "message": "Unauthorized request",
                },
                status=403,
            )

        AppModels.ShiftClaim.objects.delete(claim)
        return Response(
            data={
                "status": "success",
                "message": "Shift claim cancelled successfully",
            },
            status=204,
        )


class SwapRequestViewSet(viewsets.ModelViewSet):
    queryset = AppModels.SwapRequest.objects.all()
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    ordering_fields = ["created_at", "resolved_at"]  # noqa: RUF012
    ordering = ["created_at"]  # noqa: RUF012
    serializer_class = AppSerializer.SwapRequestReadSerializer

    def create(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        serializer = AppSerializer.SwapRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requesting_shift_claim = (
            AppModels.ShiftClaim.objects.select_related("shift", "claimed_by")
            .filter(
                shift_id=serializer.validated_data["requesting_shift"],
                claimed_by_id=request.user.id,
            )
            .first()
        )

        if not requesting_shift_claim:
            return Response(
                data={"status": "error", "message": "Requesting shift not found"},
                status=404,
            )

        if requesting_shift_claim.shift.end_time <= datetime.now(UTC):
            return Response(
                data={"status": "error", "message": "Requesting shift already ended"},
                status=400,
            )

        target_shift_claim = (
            AppModels.ShiftClaim.objects.select_related("shift", "claimed_by")
            .filter(shift_id=serializer.validated_data["target_shift"])
            .first()
        )

        if not target_shift_claim:
            return Response(
                data={"status": "error", "message": "Target shift not found"},
                status=404,
            )

        if target_shift_claim.shift.end_time <= datetime.now(UTC):
            return Response(
                data={"status": "error", "message": "Target shift already ended"},
                status=400,
            )

        swap = AppModels.SwapRequest(
            requesting_employee=requesting_shift_claim.claimed_by,
            requesting_shift=requesting_shift_claim.shift,
            target_employee=target_shift_claim.claimed_by,
            target_shift=target_shift_claim.shift,
        )
        created_swap = swap.objects.create()

        return Response(
            data={
                "status": "success",
                "message": "Swap request created successfully",
                "data": read_serializer(created_swap).data,
            },
            status=201,
        )

    def list(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()

        queryset = AppModels.SwapRequest.objects.all()

        if not queryset:
            return Response(
                data={"status": "error", "message": "Swap requests not found"},
                status=404,
            )

        if request.user.role == "staff":
            queryset = queryset.filter(
                Q(requesting_employee_id=request.user.id)
                | Q(target_employee_id=request.user.id)
            )

        return Response(
            data={
                "status": "success",
                "message": "Swap requests retrieved successfully",
                "data": read_serializer(queryset, many=True).data,
            },
            status=200,
        )

    def retrieve(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        swap = AppModels.SwapRequest.objects.filter(pk=self.kwargs["swap_id"]).first()

        if not swap:
            return Response(
                data={"status": "error", "message": "Swap request not found"},
                status=404,
            )

        return Response(
            data={
                "status": "success",
                "message": "Swap request retrieved successfully",
                "data": read_serializer(swap).data,
            },
            status=200,
        )

    def accept_swap_request(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        swap = AppModels.SwapRequest.objects.filter(
            pk=self.kwargs["swap_id"],
            target_employee_id=request.user.id,
            status="pending",
        ).first()

        if not swap:
            return Response(
                data={"status": "error", "message": "Swap request not found"},
                status=404,
            )

        swap.status = "accepted_by_target"
        swap.save(update_fields=["status"])

        return Response(
            data={
                "status": "success",
                "message": "Swap request accepted successfully",
                "data": read_serializer(swap).data,
            },
            status=200,
        )

    def reject_swap_request(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        swap = AppModels.SwapRequest.objects.filter(
            pk=self.kwargs["swap_id"],
            target_employee_id=request.user.id,
            status="pending",
        ).first()

        if not swap:
            return Response(
                data={"status": "error", "message": "Swap request not found"},
                status=404,
            )

        swap.status = "rejected"
        swap.save(update_fields=["status"])

        return Response(
            data={
                "status": "success",
                "message": "Swap request rejected successfully",
                "data": read_serializer(swap).data,
            },
            status=200,
        )

    def approve_swap_request(self, request, *args, **kwargs):
        if request.user.role != "manager":
            return Response(
                data={
                    "status": "success",
                    "message": "Unauthorized request",
                },
                status=403,
            )

        read_serializer = self.get_serializer()

        with transaction.atomic():
            swap = (
                AppModels.SwapRequest.objects.select_related(
                    "requesting_employee",
                    "requesting_shift",
                    "target_employee",
                    "target_shift",
                )
                .filter(
                    pk=self.kwargs["swap_id"],
                    status="accepted_by_target",
                )
                .first()
            )

            if not swap:
                return Response(
                    data={"status": "error", "message": "Swap request not found"},
                    status=404,
                )

            requesting_claim = AppModels.ShiftClaim.objects.get(
                shift_claim__shift=swap.requesting_shift
            )
            target_claim = AppModels.ShiftClaim.objects.get(
                shift_claim__shift=swap.target_shift
            )

            swap.status = "approved"
            swap.resolved_at = datetime.now(UTC)

            requesting_claim.claimed_by = swap.target_employee
            target_claim.claimed_by = swap.requesting_employee

            swap.save(update_fields=["status", "resolved_at"])
            requesting_claim.save(update_fields=["claimed_by"])
            target_claim.save(update_fields=["claimed_by"])

        return Response(
            data={
                "status": "success",
                "message": "Swap request approved successfully",
                "data": read_serializer(swap).data,
            },
            status=200,
        )

    def cancel_swap_request(self, request, *args, **kwargs):
        read_serializer = self.get_serializer()
        swap = AppModels.SwapRequest.objects.filter(
            pk=self.kwargs["swap_id"],
            requesting_employee_id=request.user.id,
            status="pending",
        ).first()

        if not swap:
            return Response(
                data={"status": "error", "message": "Swap request not found"},
                status=404,
            )

        swap.status = "cancelled"
        swap.save(update_fields=["status"])

        return Response(
            data={
                "status": "success",
                "message": "Swap request cancelled successfully",
                "data": read_serializer(swap).data,
            },
            status=200,
        )
