# Canteen App

Модульна версія Flask-застосунку для адміністрування їдальні.

## Структура

```
canteen_app/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── decorators.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── employees.py
│   │   ├── main.py
│   │   └── reports.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── employee_service.py
│   │   └── report_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── employees.html
│   │   ├── report.html
│   │   ├── factory_report.html
│   │   └── employee_visits.html
│   └── utils/
│       └── date_utils.py
├── .env.example
├── requirements.txt
└── run.py
```

## Запуск

1. Створіть venv та встановіть залежності:

   ```bash
   pip install -r requirements.txt
   ```

2. Заповніть змінні середовища або використайте `.env.example`.

3. Запуск:

   ```bash
   python run.py
   ```

## Що змінено

- винесено конфігурацію в `config.py`
- підключення до БД винесено в `db.py`
- маршрути поділено на blueprints
- SQL-логіка винесена в `services/`
- HTML перенесено у `templates/`
- утиліти роботи з датами винесено окремо
