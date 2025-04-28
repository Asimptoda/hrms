from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from datetime import date, timedelta  # ✅ именно так!
from decimal import Decimal


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("HR", "HR"),
        ("Manager", "Менеджер"),
        ("Accountant", "Бухгалтер"),
        ("Employee", "Обычный работник"),
        ("Admin", "Админ"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="Employee")

    def __str__(self):
        return self.username


POSITION_CHOICES = [
    ('Manager', 'Менеджер'),
    ('Developer', 'Разработчик'),
    ('Analyst', 'Аналитик'),
    ('HR', 'HR'),
    ('Accountant', 'Бухгалтер'),
    ('Designer', 'Дизайнер'),
]

User = get_user_model()

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)  # 👈 Добавлена связь
    date_hired = models.DateField(auto_now_add=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    overtime_hours = models.PositiveIntegerField(default=0)
    unpaid_leave_days = models.PositiveIntegerField(default=0)

    def get_work_experience(self):
        today = date.today()
        years = today.year - self.date_hired.year
        months = today.month - self.date_hired.month
        if months < 0:
            years -= 1
            months += 12
        return f"{years} лет, {months} месяцев"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"


class Contract(models.Model):
    CONTRACT_TYPES = [
        ("Full-time", "Full-time"),
        ("Part-time", "Part-time"),
        ("Temporary", "Temporary"),
    ]

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)  # Дата начала автоматическая!
    end_date = models.DateField(blank=True, null=True)
    contract_type = models.CharField(max_length=50, choices=CONTRACT_TYPES, default="Full-time")

    def calculate_end_date(self):
        if self.contract_type == "Full-time":
            return self.start_date + timedelta(days=730)
        elif self.contract_type == "Part-time":
            return self.start_date + timedelta(days=365)
        elif self.contract_type == "Temporary":
            return self.start_date + timedelta(days=180)
        return None

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.calculate_end_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Contract for {self.employee.first_name} {self.employee.last_name} ({self.contract_type})"


class PositionHistory(models.Model):
    """История изменений должности"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="position_history")
    old_position = models.CharField(max_length=50)
    new_position = models.CharField(max_length=50)
    changed_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name}: {self.old_position} → {self.new_position}"


class Leave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ("Vacation", "Отпуск"),
        ("Sick", "Больничный"),
        ("Unpaid", "Неоплачиваемый отпуск"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Проверяем, не превышает ли отпуск лимит в 28 дней (для оплачиваемого отпуска)
        total_days = (self.end_date - self.start_date).days
        if self.leave_type == 'Vacation' and total_days > 28:
            raise ValueError("Оплачиваемый отпуск не может превышать 28 дней в году.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - {self.get_leave_type_display()}"


# ✅ Обновляем модель Salary: сохраняем переработки и неоплаченные отпуска
class Salary(models.Model):
    MONTH_CHOICES = [
        (1, "Январь"), (2, "Февраль"), (3, "Март"), (4, "Апрель"),
        (5, "Май"), (6, "Июнь"), (7, "Июль"), (8, "Август"),
        (9, "Сентябрь"), (10, "Октябрь"), (11, "Ноябрь"), (12, "Декабрь")
    ]
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_hours = models.PositiveIntegerField(default=0)  # ✅ Теперь сохраняем
    unpaid_leave_days = models.PositiveIntegerField(default=0)  # ✅ Теперь сохраняем
    total_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_salary(self):
        salary = Decimal(self.base_salary)

        # ➕ Учитываем переработки (1.5x от стандартной ставки)
        hourly_rate = salary / Decimal(160)
        overtime_pay = Decimal(self.overtime_hours) * hourly_rate * Decimal("1.5")
        salary += overtime_pay

        # ➖ Вычитаем неоплачиваемые отпуска (дневная ставка)
        daily_rate = salary / Decimal(30)
        unpaid_deduction = Decimal(self.unpaid_leave_days) * daily_rate
        salary -= unpaid_deduction

        # ➕ Бонусы и ➖ вычеты
        salary += Decimal(self.bonuses)
        salary -= Decimal(self.deductions)

        self.total_salary = max(salary, Decimal(0))  # 🚀 Не допускаем отрицательной зарплаты

    def save(self, *args, **kwargs):
        self.calculate_salary()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - {self.total_salary} ({self.month}/{self.year})"


class Training(models.Model):
    title = models.CharField(max_length=255, unique=True)  # Название курса
    description = models.TextField(blank=True, null=True)  # Описание курса
    start_date = models.DateField()  # Дата начала курса
    end_date = models.DateField()  # Дата окончания курса

    def __str__(self):
        return self.title


class EmployeeTraining(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)  # Сотрудник
    training = models.ForeignKey(Training, on_delete=models.CASCADE)  # Курс
    status = models.CharField(
        max_length=20,
        choices=[("assigned", "Назначен"), ("completed", "Завершён")],
        default="assigned"
    )  # Статус прохождения
    completion_date = models.DateField(blank=True, null=True)  # Дата завершения

    def __str__(self):
        return f"{self.employee} - {self.training} ({self.status})"

