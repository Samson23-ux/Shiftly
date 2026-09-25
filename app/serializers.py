from rest_framework import serializers

from .models import Department, Employee, Shift, ShiftClaim, SwapRequest

# Department


class DepartmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["name"]  # noqa: RUF012

    def create(self, validated_data):
        employee = Department.objects.create(**validated_data)
        return employee


class DepartmentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class DepartmentUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150, required=False)

    class Meta:
        model = Department

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        return instance


# Employee


class EmployeeCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=254, required=False)

    class Meta:
        model = Employee
        fields = ["first_name", "last_name", "email", "department", "password"]  # noqa: RUF012

    def create(self, validated_data):
        employee = Employee.objects.create(**validated_data)
        return employee


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    username = serializers.CharField(max_length=150, required=False)

    class Meta:
        model = Employee

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.username = validated_data.get("username", instance.username)
        return instance


class EmployeeReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"
        exclude = ["password"]  # noqa: RUF012


# Shift


class ShiftCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ["department", "start_time", "end_time"]  # noqa: RUF012

    def create(self, validated_data):
        shift = Shift.objects.create(**validated_data)
        return shift


class ShiftReadSerializer(serializers.ModelSerializer):
    department = DepartmentReadSerializer()

    class Meta:
        model = Shift
        fields = "__all__"


class ShiftUpdateSerializer(serializers.ModelSerializer):
    department = serializers.CharField(max_length=150, required=False)
    start_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField(required=False)

    class Meta:
        model = Shift

    def update(self, instance, validated_data):
        instance.start_time = validated_data.get("start_time", instance.start_time)
        instance.end_time = validated_data.get("end_time", instance.end_time)
        instance.department = validated_data.get("department", instance.department)
        return instance


# Shift Claim


class ShiftClaimReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftClaim
        fields = "__all__"


# SwapRequest


class SwapRequestCreateSerializer(serializers.ModelSerializer):
    requesting_shift = serializers.UUIDField()
    target_employee = serializers.UUIDField(required=False)
    target_shift = serializers.UUIDField(required=False)

    class Meta:
        model = SwapRequest

    def create(self, validated_data):
        swap = SwapRequest.objects.create(**validated_data)
        return swap


class SwapRequestReadSerializer(serializers.ModelSerializer):
    requesting_employee = EmployeeReadSerializer()
    requesting_shift = ShiftReadSerializer()
    target_employee = EmployeeReadSerializer()
    target_shift = ShiftReadSerializer()

    class Meta:
        model = SwapRequest
        fields = ["status", "created_at", "resolved_at"]  # noqa: RUF012


class SwapRequestUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=SwapRequest.Status.choices, required=False)

    class Meta:
        model = SwapRequest

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        return instance
