# Generated by Django 5.1.6 on 2025-03-19 15:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0008_alter_salary_base_salary_alter_salary_month'),
    ]

    operations = [
        migrations.CreateModel(
            name='Training',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название курса')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('start_date', models.DateField(verbose_name='Дата начала')),
                ('end_date', models.DateField(verbose_name='Дата окончания')),
                ('is_mandatory', models.BooleanField(default=False, verbose_name='Обязательный')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeTraining',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completion_date', models.DateField(blank=True, null=True, verbose_name='Дата завершения')),
                ('status', models.CharField(choices=[('assigned', 'Назначен'), ('completed', 'Завершен'), ('failed', 'Не сдал')], default='assigned', max_length=20, verbose_name='Статус')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trainings', to=settings.AUTH_USER_MODEL, verbose_name='Сотрудник')),
                ('training', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendees', to='employees.training', verbose_name='Курс')),
            ],
        ),
    ]
