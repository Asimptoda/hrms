from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Employee, Contract, Leave, Salary, PositionHistory, Training, EmployeeTraining


# ✅ Кастомная админка для пользователей (теперь можно менять роль)
class CustomUserAdmin(UserAdmin):
    fieldsets = list(UserAdmin.fieldsets) + [
        ('Дополнительная информация', {'fields': ('role',)}),  # ✅ Теперь `role` можно менять
    ]
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')  # ✅ Показываем роль в списке
    list_filter = ('role', 'is_staff', 'is_active')  # ✅ Добавляем фильтр по ролям
    search_fields = ('username', 'email', 'role')  # ✅ Теперь можно искать по ролям
    ordering = ('username',)


admin.site.register(CustomUser, CustomUserAdmin)


# ✅ Админка для сотрудников
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'position', 'get_contract', 'get_work_experience',  'get_role', 'get_username')
    search_fields = ('first_name', 'last_name', 'email')

    def get_contract(self, obj):
        contract = Contract.objects.filter(employee=obj).first()
        return contract.contract_type if contract else "Нет контракта"

    get_contract.short_description = "Контракт"

    def get_work_experience(self, obj):
        return obj.get_work_experience()

    get_work_experience.short_description = "Стаж работы"

    def get_role(self, obj):
        return obj.user.role if obj.user else "Нет роли"
    get_role.short_description = "Роль"

    def get_username(self, obj):
        return obj.user.username if obj.user else "Нет пользователя"
    get_username.short_description = "Логин"


class TrainingAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date")
    search_fields = ("title",)


class EmployeeTrainingAdmin(admin.ModelAdmin):
    list_display = ("employee", "training", "status", "completion_date")
    list_filter = ("status",)
    search_fields = ("employee__first_name", "employee__last_name", "training__title")


admin.site.register(Employee, EmployeeAdmin)
admin.site.register(PositionHistory)
admin.site.register(Contract)
admin.site.register(Leave)
admin.site.register(Salary)
admin.site.register(Training, TrainingAdmin)
