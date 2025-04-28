from django.shortcuts import render, redirect, get_list_or_404
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from .models import Employee, Salary, Leave, Contract, PositionHistory, Training, EmployeeTraining,Department
from .serializers import (
    EmployeeSerializer, SalarySerializer, LeaveSerializer, ContractSerializer,
    PositionHistorySerializer, TrainingSerializer, EmployeeTrainingSerializer, DepartmentSerializer
)
from django.utils.decorators import method_decorator
from .permissions import (
    IsAdmin, IsHR, ManagerEmployeeContractPermission, LeavePermission,
    AccountantPermission, IsEmployee, IsManager, IsAccountant
)
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import EmployeeRegistrationForm
from datetime import date, timedelta, datetime  # ✅ ОБЯЗАТЕЛЬНО добавь!
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
import io
import pandas as pd


# 🔹 Проверяем, является ли пользователь HR или администратором
def is_hr_or_admin(user):
    return user.is_authenticated and (user.role in ["HR", "Admin"])


# 🔹 Проверяем, является ли пользователь бухгалтером
def is_accountant(user):
    return user.is_authenticated and user.role == "Accountant"


# 🔹 Проверяем, является ли пользователь руководителем
def is_manager(user):
    return user.is_authenticated and user.role == "Manager"


# 🔹 Проверяем, является ли пользователь сотрудником (обычный работник)
def is_employee(user):
    return user.is_authenticated and user.role == "Employee"


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/')  # Редирект после входа
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"]
            )
            employee = form.save(commit=False)
            employee.user = user  # 👈 Связываем с пользователем
            employee.save()
            login(request, user)  # 👈 Автоматически входим после регистрации
            return redirect('/')
    else:
        form = EmployeeRegistrationForm()

    return render(request, "register.html", {"form": form})


def calculate_salary_deductions(employee):
    """Функция вычитает неоплачиваемые дни из зарплаты"""
    unpaid_leaves = Leave.objects.filter(employee=employee, leave_type="Unpaid")

    total_unpaid_days = sum((leave.end_date - leave.start_date).days for leave in unpaid_leaves)

    daily_rate = employee.base_salary / 30  # Считаем дневную ставку
    deduction = total_unpaid_days * daily_rate

    return deduction


def add_overtime(request, employee_id, hours):
    employee = Employee.objects.get(id=employee_id)
    employee.overtime_hours += hours
    employee.save()
    return JsonResponse({'status': 'success', 'overtime_hours': employee.overtime_hours})


@login_required
def redirect_after_login(request):
    user = request.user

    if not user.is_authenticated:
        return redirect("/login/")  # Если не авторизован – отправляем на страницу входа

    role = user.role  # ✅ Берём роль прямо из CustomUser

    if role == "HR":
        return redirect("/employees/")  # HR видит сотрудников
    elif role == "Accountant":
        return redirect("/salaries/")  # Бухгалтер видит зарплаты
    elif role == "Manager":
        return redirect("/leaves/")  # Менеджер видит отпуска
    elif role == "Employee":
        return redirect("/leaves/")  # Обычный сотрудник видит только свои отпуска

    return redirect("/")  # Если роль не найдена – на главную страницу


def logout_view(request):
    logout(request)
    return redirect('/login/')
# 🔹 HTML-страницы

def home(request):
    return render(request, 'home.html')

@login_required
@user_passes_test(lambda u: u.role in ["HR"])
def position_history_list(request):
    history = PositionHistory.objects.all().order_by("-changed_at")  # Загружаем данные из базы
    return render(request, 'employees/position_history.html', {"history": history})


@login_required
@user_passes_test(lambda u: u.role in ["HR", "Admin", "Manager"])
def employees_list(request):
    return render(request, 'employees/employees.html')


@login_required
@user_passes_test(lambda u: u.role in ["Accountant", "Manager"])
def salaries_list(request):
    return render(request, 'employees/salaries.html')


@login_required
@user_passes_test(lambda u: u.role in ["HR", "Admin", "Manager"])
def contracts_list(request):
    return render(request, 'employees/contracts.html')


@login_required
def leaves_list(request):
    user = request.user
    if user.role in ["HR", "Manager"]:
        return render(request, 'employees/leaves.html')
    return render(request, 'employees/leaves.html', {"employee_id": user.employee.id})


@login_required
def position_history_page(request):
    history = PositionHistory.objects.all().order_by("-changed_at")  # 👈 Загружаем данные из БД
    return render(request, 'employees/position_history.html', {"history": history})


# ✅ Исправление ошибки: генерация зарплаты с переработками и неоплаченным отпуском
def generate_salary(request, employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)

        # Получаем данные о переработках и неоплаченном отпуске
        overtime_hours = getattr(employee, "overtime_hours", 0)
        unpaid_leave_days = getattr(employee, "unpaid_leave_days", 0)

        # Создаём новую зарплату
        salary = Salary.objects.create(
            employee=employee,
            base_salary=employee.base_salary,
            bonuses=0,
            deductions=0,
            overtime_hours=overtime_hours,  # ✅ Теперь сохраняем данные
            unpaid_leave_days=unpaid_leave_days,  # ✅ Теперь сохраняем данные
            month=str(datetime.now().month),  # ✅ Сохраняем месяц как ID
            year=datetime.now().year
        )

        return JsonResponse({"status": "ok", "total_salary": salary.total_salary})
    except Employee.DoesNotExist:
        return JsonResponse({"error": "Сотрудник не найден"}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_salary_report(request, report_format, month=None, year=None):
    """
    Генерирует отчет по зарплатам и налогам в Excel или PDF.
    """
    # Фильтруем данные по месяцу и году, если переданы параметры
    salaries = Salary.objects.all()
    if month:
        salaries = salaries.filter(month=month)
    if year:
        salaries = salaries.filter(year=year)

    if not salaries.exists():
        return HttpResponse("Нет данных за указанный период", status=404)

    # Подготавливаем данные
    data = [
        {
            "Сотрудник": f"{s.employee.first_name} {s.employee.last_name}",
            "Месяц": s.month,
            "Год": s.year,
            "Базовая зарплата": s.base_salary,
            "Переработки": s.overtime_hours,
            "Неоплач. отпуск": s.unpaid_leave_days,
            "Бонусы": s.bonuses,
            "Вычеты": s.deductions,
            "Итоговая зарплата": s.total_salary
        }
        for s in salaries
    ]

    df = pd.DataFrame(data)  # Преобразуем в таблицу

    if report_format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Отчет по зарплате")
        output.seek(0)
        response = HttpResponse(output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="salary_report_{month or "all"}_{year or "all"}.xlsx"'
        return response

    elif report_format == "pdf":
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="salary_report.pdf"'

        p = canvas.Canvas(response)

        # ✅ Регистрируем шрифт с поддержкой кириллицы
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        p.setFont("Arial", 12)  # Устанавливаем шрифт

        p.drawString(100, 800, "Отчет по зарплатам")

        salaries = Salary.objects.all()
        y = 780
        for salary in salaries:
            text = f"{salary.employee.first_name} {salary.employee.last_name}: {salary.total_salary} $"
            p.drawString(100, y, text)
            y -= 20

        p.showPage()
        p.save()
        return response

    else:
        return HttpResponse("Формат не поддерживается", status=400)


def training_page(request):
    return render(request, 'employees/training.html')


def courses_page(request):
    return render(request, 'employees/courses.html')


# 🔹 API для управления сотрудниками
# Employees ViewSet
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAdmin | IsHR | IsManager | IsAccountant | AccountantPermission]
        elif self.action in ['create']:
            permission_classes = [IsAdmin | IsHR | ManagerEmployeeContractPermission]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAdmin | IsHR | ManagerEmployeeContractPermission]
        elif self.action == 'destroy':
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Создаём сотрудника и автоматически создаём для него контракт"""
        employee = serializer.save()  # ✅ Сохраняем сотрудника

        # ✅ Определяем параметры контракта
        contract_type = "Full-time"  # 👈 По умолчанию Full-time
        start_date=date.today()   # 👈 Контракт начинается сегодня
        end_date = None  # По умолчанию бессрочный

        if contract_type == "Full-time":
            end_date = start_date + timedelta(days=730)  # 2 года
        elif contract_type == "Part-time":
            end_date = start_date + timedelta(days=365)  # 1 год
        elif contract_type == "Temporary":
            end_date = start_date + timedelta(days=180)  # 6 месяцев

        # Создаём контракт с явной датой начала
        Contract.objects.create(
            employee=employee,
            contract_type="Full-time",
            start_date=date.today()  # ✅ исправлено здесь!
        )


# ✅ Обновляем SalaryViewSet: теперь сохраняем переработки и неоплаченный отпуск
class SalaryViewSet(viewsets.ModelViewSet):
    queryset = Salary.objects.all()
    serializer_class = SalarySerializer
    permission_classes = [IsAuthenticated, IsAccountant]

    # ✅ Добавляем фильтрацию по сотруднику, месяцу и году
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['employee', 'year']
    ordering_fields = ["year", "month", "total_salary"]

    def get_queryset(self):
        queryset = Salary.objects.all()
        month = self.request.query_params.get("month", None)
        employee = self.request.query_params.get("employee", None)

        if month:
            try:
                month = int(month)  # ✅ Приводим к int
                queryset = queryset.filter(month=month)
            except ValueError:
                pass  # Если ошибка, пропускаем

        if employee:
            queryset = queryset.filter(employee=employee)

        return queryset

    def get_permissions(self):
        print(
            f"🟢 [get_permissions] method: {self.action}, user: {self.request.user.username}, role: {self.request.user.role}")

        if self.request.method in ["GET"]:
            permission_classes = [IsAdmin | IsAccountant | IsHR | IsManager]
        elif self.request.method in ["POST", "PUT", "PATCH"]:
            permission_classes = [IsAdmin | IsAccountant]
        elif self.action == "DELETE":  # Добавляем отдельную проверку
            permission_classes = [IsAdmin | IsAccountant]
        else:
            permission_classes = [IsAdmin]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        data = self.request.data

        employee_id = data.get("employee_id")
        month = data.get("month")
        year = data.get("year")
        base_salary = Decimal(data.get("base_salary", 0))
        bonuses = Decimal(data.get("bonuses", 0))
        deductions = Decimal(data.get("deductions", 0))
        overtime_hours = int(data.get("overtime_hours", 0))
        unpaid_leave_days = int(data.get("unpaid_leave_days", 0))

        try:
            employee = Employee.objects.get(id=employee_id)

            salary = Salary.objects.create(
                employee=employee,
                base_salary=base_salary,
                bonuses=bonuses,
                deductions=deductions,
                overtime_hours=overtime_hours,  # ✅ Теперь сохраняем
                unpaid_leave_days=unpaid_leave_days,  # ✅ Теперь сохраняем
                month=int(month),  # ✅ Храним как число
                year=int(year)
            )
            salary.save()
        except Employee.DoesNotExist:
            raise serializers.ValidationError({"employee": "Сотрудник не найден"})

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.calculate_salary()  # ✅ Теперь обновляется зарплата при редактировании
        instance.save()

    def perform_destroy(self, instance):
        print(
            f"🔴 [perform_destroy] Удаление зарплаты: user={self.request.user.username}, role={self.request.user.role}, instance={instance}")
        instance.delete()


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer
    permission_classes = [LeavePermission]  # <-- теперь используем наш новый класс разрешений!

    def get_queryset(self):
        user = self.request.user
        if user.role in ["Manager", "HR", "Admin"]:
            return Leave.objects.all()
        return Leave.objects.filter(employee=user.employee)


# Contract ViewSet
class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAdmin | IsHR | IsManager]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsAdmin | IsHR | IsManager]
        elif self.action == 'destroy':
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]


class EmployeeRestrictedViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsEmployee]

    def get_queryset(self):
        return Employee.objects.filter(id=self.request.user.employee.id)  # 👈 Работник видит **только свои данные**!


class PositionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PositionHistory.objects.all()
    serializer_class = PositionHistorySerializer
    permission_classes = [IsHR | IsAdmin]  # Только HR/Admin могут видеть историю


# ✅ API для управления курсами
class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [IsHR]  # Только HR может управлять курсами


class EmployeeTrainingViewSet(viewsets.ModelViewSet):
    queryset = EmployeeTraining.objects.all()
    serializer_class = EmployeeTrainingSerializer

    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        employees = request.data.get('employees', [])
        departments = request.data.get('departments', [])
        assign_all = request.data.get('assign_all', False)
        trainings = request.data.get('trainings', [])

        employee_qs = Employee.objects.none()

        if assign_all:
            employee_qs = Employee.objects.all()
        else:
            if departments:
                employee_qs |= Employee.objects.filter(department_id__in=departments)
            if employees:
                employee_qs |= Employee.objects.filter(id__in=employees)

        assigned = []
        for employee in employee_qs.distinct():
            for training_id in trainings:
                training = Training.objects.get(pk=training_id)
                obj, created = EmployeeTraining.objects.get_or_create(
                    employee=employee, training=training)
                if created:
                    assigned.append(obj)

        serializer = self.get_serializer(assigned, many=True)
        return Response(serializer.data, status=201)

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

