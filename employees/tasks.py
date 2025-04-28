from celery import shared_task
from .models import Salary, Employee
from datetime import datetime


@shared_task
def generate_salaries():
    today = datetime.today()
    month = today.strftime("%B")  # Получаем текущий месяц (например, "March")
    year = today.year

    employees = Employee.objects.all()

    for employee in employees:
        Salary.objects.create(
            employee=employee,
            base_salary=employee.base_salary,
            bonuses=0.00,
            deductions=0.00,
            month=month,
            year=year
        )

    return f"Salaries for {month} {year} generated successfully."
