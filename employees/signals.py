from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Employee, Contract, PositionHistory
from datetime import date


# @receiver(post_save, sender=Employee)
# pdef create_contract(sender, instance, created, **kwargs):
#    if created:
#        Contract.objects.create(
#            employee=instance,
#            start_date=date.today(),  # ✅ теперь обязательно указываем явно дату начала
#            contract_type="Full-time"
#        )

@receiver(pre_save, sender=Employee)
def track_position_change(sender, instance, **kwargs):
    """Записывает изменения должности сотрудника в историю"""
    if instance.pk:  # Если сотрудник уже существует
        old_employee = Employee.objects.get(pk=instance.pk)
        if old_employee.position != instance.position:
            PositionHistory.objects.create(
                employee=instance,
                old_position=old_employee.position,
                new_position=instance.position
            )