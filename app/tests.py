import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import models as AppModels
from django.db import connection
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

URL_PREFIX = "/api/v1"

employee_1 = {
    "username": "test_username",
    "email": "testuser@example.com",
    "password": "test_default_password",
    "first_name": "test_first_name",
    "last_name": "test_last_name",
}

employee_2 = AppModels.Employee.objects.create_user(
    username="test_username_1",
    email="testuser1@example.com",
    password="test_default_password",
    first_name="test_first_name_1",
    last_name="test_last_name_1",
)

manager = {
    "username": "manager_test_username",
    "email": "managertestuser@example.com",
    "password": "manager_test_default_password",
    "first_name": "manager_test_first_name",
    "last_name": "manager_test_last_name",
}


class EmployeeTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = AppModels.Department.objects.create(name="test_department")
        self.employee = AppModels.Employee.objects.create_user(**employee_1)

    def auth(self):
        res = self.client.post(
            "/api/v1/auth/login/",
            data={"email": "testuser@example.com", "password": "test_default_password"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        token = res.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_employee(self):
        payload = {
            "first_name": "test_first_name",
            "last_name": "test_last_name",
            "username": "test_username",
            "email": "testuser@example.com",
            "password": "test_strong_password",
            "department": "test_department",
        }

        res = self.client.post(
            f"{URL_PREFIX}/employees/", data=payload, content_type="application/json"
        )
        self.assertEqual(res.status_code, 201)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["first_name"], "test_first_name")
        self.assertEqual(json_res["data"]["data"]["last_name"], "test_last_name")
        self.assertEqual(json_res["data"]["data"]["email"], "testuser@example.com")
        self.assertEqual(json_res["data"]["data"]["role"], "staff")

    def test_create_employee_no_username(self):
        payload = {
            "first_name": "test_first_name",
            "last_name": "test_last_name",
            "email": "testuser@example.com",
            "password": "test_strong_password",
            "department": "test_department",
        }

        res = self.client.post(
            f"{URL_PREFIX}/employees/", data=payload, content_type="application/json"
        )
        self.assertEqual(res.status_code, 201)
        json_res = res.json()
        self.assertEqual(
            json_res["data"]["data"]["username"], "test_first_name test_last_name"
        )

    def test_create_employee_department_not_found(self):
        payload = {
            "first_name": "test_first_name",
            "last_name": "test_last_name",
            "username": "test_username",
            "email": "testuser@example.com",
            "password": "test_strong_password",
            "department": "department_not_found",
        }

        res = self.client.post(
            f"{URL_PREFIX}/employees/", data=payload, content_type="application/json"
        )

        self.assertEqual(res.status_code, 404)

    def test_list_employees(self):
        res = self.client.get(f"{URL_PREFIX}/employees/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(len(json_res["data"]["data"]), 1)

    def test_retrieve_authenticated_employee(self):
        self.auth()

        res = self.client.get(f"{URL_PREFIX}/employees/{self.employee.id!s}/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["email"], "testuser@example.com")

    def test_retrieve_unauthenticated_employee(self):
        res = self.client.get(f"{URL_PREFIX}/employees/{self.employee.id!s}/")
        self.assertEqual(res.status_code, 401)

    def test_update_authenticated_employee(self):
        self.auth()

        res = self.client.patch(
            f"{URL_PREFIX}/employees/{self.employee.id!s}/",
            data={"username": "@new_test_username"},
            format="json",
        )

        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["email"], "testuser@example.com")
        self.assertEqual(json_res["data"]["data"]["username"], "@new_test_username")

    def test_update_inactive_employee(self):
        self.auth()

        AppModels.Employee.objects.update(is_active=False)

        res = self.client.patch(
            f"{URL_PREFIX}/employees/{self.employee.id!s}/",
            data={"username": "@new_test_username"},
            format="json",
        )

        self.assertEqual(res.status_code, 404)

    def test_delete_authenticated_employee(self):
        self.auth()

        res = self.client.delete(
            f"{URL_PREFIX}/employees/{self.employee.id!s}/", format="json"
        )

        self.assertEqual(res.status_code, 204)

        res = self.client.patch(
            f"{URL_PREFIX}/employees/{self.employee.id!s}/",
            data={"username": "@new_test_username"},
            format="json",
        )

        self.assertEqual(res.status_code, 404)

    def test_reactivate_authenticated_employee(self):
        self.auth()

        res = self.client.delete(
            f"{URL_PREFIX}/employees/{self.employee.id!s}/", format="json"
        )

        self.assertEqual(res.status_code, 204)

        res = self.client.patch(
            f"{URL_PREFIX}/employees/{self.employee.id!s}/reactivate/", format="json"
        )

        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["email"], "testuser@example.com")


class ShiftTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = AppModels.Department.objects.create(name="test_department")
        self.manager = AppModels.Employee.objects.create_superuser(**manager)
        self.employee = AppModels.Employee.objects.create_user(**employee_1)
        self.shift = AppModels.Shift(
            created_by=self.manager,
            department=self.department,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(days=1),
        )

    def staff_auth(self):
        res = self.client.post(
            "/api/v1/auth/login/",
            data={"email": "testuser@example.com", "password": "test_default_password"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        token = res.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def manager_auth(self):
        res = self.client.post(
            "/api/v1/auth/login/",
            data={
                "email": "managertestuser@example.com",
                "password": "manager_test_default_password",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        token = res.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_shift(self):
        self.manager_auth()

        res = self.client.post(
            f"{URL_PREFIX}/shifts/",
            data={
                "department": "test_department",
                "start_time": datetime.now(UTC).isoformat(),
                "end_time": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(res.status_code, 201)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["created_by"], self.manager.id)
        self.assertEqual(json_res["data"]["data"]["department"], self.department.id)

    def test_create_shift_no_department(self):
        self.manager_auth()

        res = self.client.post(
            f"{URL_PREFIX}/shifts/",
            data={
                "department": "test_no_department",
                "start_time": datetime.now(UTC).isoformat(),
                "end_time": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(res.status_code, 404)

    def test_list_shift(self):
        self.staff_auth()

        res = self.client.get(f"{URL_PREFIX}/shifts/")

        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(len(json_res["data"]["data"]), 1)

    def test_retrieve_shift(self):
        self.staff_auth()

        res = self.client.get(f"{URL_PREFIX}/shifts/{self.shift.id!s}/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["created_by"], self.manager.id)
        self.assertEqual(json_res["data"]["data"]["department"], self.department.id)

    def test_retrieve_shift_not_found(self):
        self.staff_auth()

        res = self.client.get(f"{URL_PREFIX}/shifts/{uuid.uuid7()!s}/")
        self.assertEqual(res.status_code, 404)

    def test_update_shift(self):
        self.manager_auth()

        two_days = (datetime.now(UTC) + timedelta(days=2)).isoformat()
        res = self.client.patch(
            f"{URL_PREFIX}/shifts/{self.shift.id!s}/",
            data={"end_time": two_days},
            format="json",
        )

        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["end_time"], two_days)

    def test_delete_shift(self):
        self.manager_auth()

        res = self.client.delete(
            f"{URL_PREFIX}/shifts/{self.shift.id!s}/", format="json"
        )

        self.assertEqual(res.status_code, 204)


class ShiftClaimTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = AppModels.Department.objects.create(name="test_department")
        self.employee = AppModels.Employee.objects.create_user(**employee_1)
        self.manager = AppModels.Employee.objects.create_superuser(**manager)
        self.shift = AppModels.Shift(
            created_by=self.manager,
            department=self.department,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(days=1),
        )

    def auth(self):
        res = self.client.post(
            "/api/v1/auth/login/",
            data={"email": "testuser@example.com", "password": "test_default_password"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        token = res.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_shift_claim(self):
        self.auth()

        res = self.client.post(
            f"{URL_PREFIX}/shifts/{self.shift.id!s}/claims/", format="json"
        )

        self.assertEqual(res.status_code, 201)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["shift"], self.shift.id)
        self.assertEqual(json_res["data"]["data"]["claimed_by"], self.employee.id)

    def test_create_shift_claim_not_found(self):
        self.auth()

        res = self.client.post(
            f"{URL_PREFIX}/shifts/{uuid.uuid7()!s}/claims/", format="json"
        )

        self.assertEqual(res.status_code, 404)

    def test_create_claim_shift_ended(self):
        self.auth()

        shift = AppModels.Shift(
            created_by=self.manager,
            department=self.department,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(seconds=1),
        )

        time.sleep(2)

        res = self.client.post(
            f"{URL_PREFIX}/shifts/{shift.id!s}/claims/", format="json"
        )

        self.assertEqual(res.status_code, 400)

    def test_list_shift_claim(self):
        self.auth()

        AppModels.ShiftClaim(shift=self.shift, claimed_by=self.employee)

        res = self.client.get(f"{URL_PREFIX}/shifts/claims/")

        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(len(json_res["data"]["data"]), 1)

    def test_list_shift_claim_not_found(self):
        self.auth()

        res = self.client.get(f"{URL_PREFIX}/shifts/claims/")

        self.assertEqual(res.status_code, 404)
        json_res = res.json()
        self.assertEqual(len(json_res["data"]["data"]), 1)

    def test_retrieve_shift_claim(self):
        self.auth()

        claim = AppModels.ShiftClaim(shift=self.shift, claimed_by=self.employee)

        res = self.client.get(f"{URL_PREFIX}/shifts/claims/{claim.id!s}/")

        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(len(json_res["data"]["data"]["shift"]), self.shift.id)
        self.assertEqual(len(json_res["data"]["data"]["claimed_by"]), self.employee.id)

    def test_delete_shift_claim(self):
        self.auth()
        claim = AppModels.ShiftClaim(shift=self.shift, claimed_by=self.employee)

        res = self.client.delete(f"{URL_PREFIX}/shifts/claims/{claim.id!s}/")

        self.assertEqual(res.status_code, 204)

    def test_unauthorized_delete_shift_claim(self):
        claim = AppModels.ShiftClaim(shift=self.shift, claimed_by=self.employee.id)

        self.client.force_authenticate(user=employee_2)

        res = self.client.delete(f"{URL_PREFIX}/shifts/claims/{claim.id!s}/")

        self.assertEqual(res.status_code, 403)


class SwapRequestTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = AppModels.Department.objects.create(name="test_department")
        self.employee_1 = AppModels.Employee.objects.create_user(**employee_1)
        self.employee_2 = AppModels.Employee.objects.create_user(**employee_1)
        self.manager = AppModels.Employee.objects.create_superuser(**manager)
        self.shift_1 = AppModels.Shift(
            created_by=self.manager,
            department=self.department,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(days=1),
        )
        self.shift_2 = AppModels.Shift(
            created_by=self.manager,
            department=self.department,
            start_time=datetime.now(UTC) + timedelta(days=1),
            end_time=datetime.now(UTC) + timedelta(days=2),
        )
        self.claim_1 = AppModels.ShiftClaim(
            shift=self.shift_1, claimed_by=self.employee_1.id
        )
        self.claim_2 = AppModels.ShiftClaim(
            shift=self.shift_2, claimed_by=self.employee_2.id
        )

    def auth(self, data):
        res = self.client.post("/api/v1/auth/login/", data=data, format="json")
        self.assertEqual(res.status_code, 201)
        token = res.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_swap_request(self):
        self.auth(
            {"email": "testuser@example.com", "password": "test_default_password"}
        )

        data = {
            "requesting_shift": str(self.shift_1.id),
            "target_shift": str(self.shift_2.id),
        }
        res = self.client.post(
            f"{URL_PREFIX}/shifts/requests/swap/", data=data, format="json"
        )

        self.assertEqual(res.status_code, 201)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["requesting_shift"], self.shift_1.id)
        self.assertEqual(json_res["data"]["data"]["target_shift"], self.shift_2.id)
        self.assertEqual(
            json_res["data"]["data"]["requesting_employee"], self.employee_1.id
        )
        self.assertEqual(
            json_res["data"]["data"]["target_employee"], self.employee_2.id
        )
        self.assertEqual(json_res["data"]["data"]["status"], "pending")

    def test_create_swap_request_requesting_shift_not_found(self):
        self.auth(
            {"email": "testuser@example.com", "password": "test_default_password"}
        )

        data = {
            "requesting_shift": str(uuid.uuid7()),
            "target_shift": str(self.shift_2.id),
        }
        res = self.client.post(
            f"{URL_PREFIX}/shifts/requests/swap/", data=data, format="json"
        )

        self.assertEqual(res.status_code, 404)

    def test_create_swap_request_requesting_shift_ended(self):
        self.auth(
            {"email": "testuser@example.com", "password": "test_default_password"}
        )

        shift_1 = AppModels.Shift(
            created_by=self.manager,
            department=self.department,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(seconds=1),
        )
        AppModels.ShiftClaim(shift=shift_1, claimed_by=self.employee_1.id)

        time.sleep(2)

        data = {
            "requesting_shift": str(shift_1.id),
            "target_shift": str(self.shift_2.id),
        }
        res = self.client.post(
            f"{URL_PREFIX}/shifts/requests/swap/", data=data, format="json"
        )

        self.assertEqual(res.status_code, 400)

    def test_create_swap_request_target_shift_not_found(self):
        self.auth(
            {"email": "testuser@example.com", "password": "test_default_password"}
        )

        data = {
            "requesting_shift": str(self.shift_1.id),
            "target_shift": str(uuid.uuid7()),
        }
        res = self.client.post(
            f"{URL_PREFIX}/shifts/requests/swap/", data=data, format="json"
        )

        self.assertEqual(res.status_code, 404)

    def test_create_swap_request_target_shift_ended(self):
        self.auth(
            {"email": "testuser@example.com", "password": "test_default_password"}
        )

        shift_2 = AppModels.Shift(
            created_by=self.manager,
            department=self.department,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(seconds=1),
        )
        AppModels.ShiftClaim(shift=shift_2, claimed_by=self.employee_2.id)

        time.sleep(2)

        data = {
            "requesting_shift": str(self.shift_1.id),
            "target_shift": str(shift_2.id),
        }
        res = self.client.post(
            f"{URL_PREFIX}/shifts/requests/swap/", data=data, format="json"
        )

        self.assertEqual(res.status_code, 400)

    def test_list_swap_request(self):
        self.auth(
            {"email": "testuser@example.com", "password": "test_default_password"}
        )

        AppModels.SwapRequest(
            requesting_employee=self.employee_1,
            requesting_shift=self.shift_1,
            target_employee=self.employee_2,
            target_shift=self.shift_2,
            status="pending",
        )

        res = self.client.get(f"{URL_PREFIX}/shifts/requests/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(len(json_res["data"]["data"]), 1)

    def test_retrieve_swap_request(self):
        self.auth(
            {"email": "testuser@example.com", "password": "test_default_password"}
        )

        swap = AppModels.SwapRequest.objects.create(
            requesting_employee=self.employee_1,
            requesting_shift=self.shift_1,
            target_employee=self.employee_2,
            target_shift=self.shift_2,
            status="pending",
        )

        res = self.client.get(f"{URL_PREFIX}/shifts/requests/{swap.id!s}/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["requesting_employee"], self.employee_1.id)
        self.assertEqual(json_res["data"]["data"]["target_employee"], self.employee_2.id)
        self.assertEqual(json_res["data"]["data"]["requesting_shift"], self.shift_1.id)
        self.assertEqual(json_res["data"]["data"]["target_shift"], self.shift_2.id)

    def test_accept_swap_request(self):
        self.auth(
            {"email": "testuser1@example.com", "password": "test_default_password"}
        )

        swap = AppModels.SwapRequest.objects.create(
            requesting_employee=self.employee_1,
            requesting_shift=self.shift_1,
            target_employee=self.employee_2,
            target_shift=self.shift_2,
            status="pending",
        )

        res = self.client.get(f"{URL_PREFIX}/shifts/requests/{swap.id!s}/accept/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["status"], "accepted_by_target")

    def test_redundant_accept_swap_request(self):
        self.auth(
            {"email": "testuser1@example.com", "password": "test_default_password"}
        )

        swap = AppModels.SwapRequest.objects.create(
            requesting_employee=self.employee_1,
            requesting_shift=self.shift_1,
            target_employee=self.employee_2,
            target_shift=self.shift_2,
            status="accepted_by_target",
        )

        res = self.client.get(f"{URL_PREFIX}/shifts/requests/{swap.id!s}/accept/")
        self.assertEqual(res.status_code, 404)

    def test_reject_swap_request(self):
        self.auth(
            {"email": "testuser1@example.com", "password": "test_default_password"}
        )

        swap = AppModels.SwapRequest.objects.create(
            requesting_employee=self.employee_1,
            requesting_shift=self.shift_1,
            target_employee=self.employee_2,
            target_shift=self.shift_2,
            status="pending",
        )

        res = self.client.get(f"{URL_PREFIX}/shifts/requests/{swap.id!s}/reject/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["status"], "rejected")

    def test_cancel_swap_request(self):
        self.auth(
            {"email": "testuser@example.com", "password": "test_default_password"}
        )

        swap = AppModels.SwapRequest.objects.create(
            requesting_employee=self.employee_1,
            requesting_shift=self.shift_1,
            target_employee=self.employee_2,
            target_shift=self.shift_2,
            status="pending",
        )

        res = self.client.get(f"{URL_PREFIX}/shifts/requests/{swap.id!s}/cancel/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["status"], "cancelled")

    def test_approve_swap_request(self):
        self.auth(
            {"email": "managertestuser@example.com", "password": "test_default_password"}
        )

        swap = AppModels.SwapRequest.objects.create(
            requesting_employee=self.employee_1,
            requesting_shift=self.shift_1,
            target_employee=self.employee_2,
            target_shift=self.shift_2,
            status="pending",
        )

        res = self.client.get(f"{URL_PREFIX}/shifts/requests/{swap.id!s}/approve/")
        self.assertEqual(res.status_code, 200)
        json_res = res.json()
        self.assertEqual(json_res["data"]["data"]["status"], "approved")

        claim_1 = AppModels.ShiftClaim.objects.get(pk=self.claim_1.id)
        claim_2 = AppModels.ShiftClaim.objects.get(pk=self.claim_2.id)

        self.assertEqual(claim_1.claimed_by, self.employee_2)
        self.assertEqual(claim_2.claimed_by, self.employee_1)


class RaceConditionTestCase(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = AppModels.Department.objects.create(name="test_department")
        self.employee = AppModels.Employee.objects.create_user(**employee_1)
        self.manager = AppModels.Employee.objects.create_superuser(**manager)
        self.shift = AppModels.Shift(
            created_by=self.manager,
            department=self.department,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(days=1),
        )

    def auth(self):
        res = self.client.post(
            "/api/v1/auth/login/",
            data={"email": "testuser@example.com", "password": "test_default_password"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        token = res.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_concurrent_shift_claim_requests(self):
        self.auth()

        n = 10
        barrier = threading.Barrier(n)

        def make_request():
            try:
                barrier.wait(timeout=5)
                
                res = self.client.post(
                    f"{URL_PREFIX}/shifts/{self.shift.id!s}/claims/", format="json"
                )
                return res.status_code
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=n) as pool:
            status_codes = list(pool.map(make_request, range(n)))

        self.assertEqual(status_codes.count(201), 1)
        self.assertEqual(status_codes.count(409), 9)
