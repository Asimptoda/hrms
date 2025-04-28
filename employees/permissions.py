from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.is_superuser


class IsHR(BasePermission):
    def has_permission(self, request, view):
        print(f"Permission check: user={request.user.username}, role={request.user.role}, has_permission=True")
        return request.user.is_authenticated and request.user.role == "HR"

    def has_object_permission(self, request, view, obj):
        print("Object permission check:", request.user.username, request.user.role)
        return request.user.is_authenticated and request.user.role == "HR"


class IsAccountant(BasePermission):
    def has_permission(self, request, view):
        print(f"🔵 [has_permission] Accountant: {request.user.username}, method: {request.method}")
        return request.user.is_authenticated and request.user.role == "Accountant"

    def has_object_permission(self, request, view, obj):
        print(f"🟡 [has_object_permission] Accountant: {request.user.username}, method: {request.method}, Object: {obj}")
        return request.method in ["GET", "DELETE"] and request.user.role == "Accountant"


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "Manager"

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == "Manager"


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "Employee"

    def has_object_permission(self, request, view, obj):
        # Обычный сотрудник может видеть только свои объекты
        return request.user.is_authenticated and obj.employee.user == request.user


# Manager permissions:
class ManagerEmployeeContractPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.role == "Manager"
        elif request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user.role == "Manager"
        return False


# Accountant permissions:
class AccountantPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            return request.user.is_authenticated and request.user.role == "Accountant"
        return False


class LeavePermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ["HR", "Manager", "Admin"]:
            return True  # полный доступ для HR, Manager и Admin
        elif user.role == "Employee":
            return obj.employee.user == request.user  # только свои отпуска
        return False

