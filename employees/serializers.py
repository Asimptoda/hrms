from rest_framework import serializers
from .models import Employee, Contract, Leave, Salary, PositionHistory, Training, EmployeeTraining,Department



class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'


class SalarySerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)  # ✅ Читаем объект
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='employee', write_only=True
    )  # ✅ Передаем ID при записи

    class Meta:
        model = Salary
        fields = [
            "id", "employee", "employee_id", "month", "year",
            "base_salary", "overtime_hours", "unpaid_leave_days",  # ✅ Добавлено
            "bonuses", "deductions", "total_salary"
        ]


class LeaveSerializer(serializers.ModelSerializer):
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="employee", write_only=True
    )  # Принимает ID сотрудника
    employee = serializers.SerializerMethodField()  # Возвращает объект

    class Meta:
        model = Leave
        fields = ["id", "employee", "employee_id", "leave_type", "start_date", "end_date", "approved"]

    def get_employee(self, obj):
        return {
            "id": obj.employee.id,
            "first_name": obj.employee.first_name,
            "last_name": obj.employee.last_name
        }


class ContractSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)  # Читаем объект
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='employee', write_only=True
    )  # Записываем через ID

    class Meta:
        model = Contract
        fields = ["id", "employee", "employee_id", "start_date", "end_date", "contract_type"]


class PositionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PositionHistory
        fields = '__all__'


class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = '__all__'


class EmployeeTrainingSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.first_name", read_only=True)
    training_title = serializers.CharField(source="training.title", read_only=True)

    class Meta:
        model = EmployeeTraining
        fields = ['id', 'employee', 'training', 'status', 'completion_date', 'employee_name', 'training_title']
