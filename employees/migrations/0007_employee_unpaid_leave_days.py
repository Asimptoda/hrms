# Generated by Django 5.1.6 on 2025-03-19 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0006_salary_overtime_hours_salary_unpaid_leave_days_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='unpaid_leave_days',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
