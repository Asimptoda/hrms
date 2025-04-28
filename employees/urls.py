from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login_view, logout_view, redirect_after_login, PositionHistoryViewSet, position_history_list,
    EmployeeViewSet, SalaryViewSet, LeaveViewSet, ContractViewSet, position_history_page, add_overtime,
    employees_list, salaries_list, leaves_list, contracts_list, generate_salary,
    generate_salary_report, TrainingViewSet, EmployeeTrainingViewSet, training_page, courses_page, DepartmentViewSet,home
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'salaries', SalaryViewSet)
router.register(r'leaves', LeaveViewSet)
router.register(r'contracts', ContractViewSet)
router.register(r'position-history', PositionHistoryViewSet)
router.register(r'training', TrainingViewSet)
router.register(r'employee-training', EmployeeTrainingViewSet)
router.register(r'departments', DepartmentViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('employees/', employees_list, name='employees_list'),
    path('salaries/', salaries_list, name='salaries_list'),
    path('report/salary/<str:report_format>/', generate_salary_report, name='salary_report_all'),
    path('report/salary/<str:report_format>/<int:year>/', generate_salary_report, name='salary_report_year'),
    path('report/salary/<str:report_format>/<int:month>/<int:year>/', generate_salary_report, name='salary_report_month'),
    path('leaves/', leaves_list, name='leaves_list'),
    path('contracts/', contracts_list, name='contracts_list'),
    path('position-history/', position_history_list, name='position_history'),
    path('training/', training_page, name='training_page'),
    path('courses/', courses_page, name='courses_page'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path("redirect-after-login/", redirect_after_login, name="redirect_after_login"),
    path('position-history/', position_history_page, name='position-history'),
    path('add-overtime/<int:employee_id>/<int:hours>/', add_overtime, name='add_overtime'),
    path('generate-salary/<int:employee_id>/', generate_salary, name='generate_salary'),
    path('', include(router.urls)),
    path('api/', include(router.urls)),
]
