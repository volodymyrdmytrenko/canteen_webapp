# Canteen Web App

Web-застосунок для:
- редагування таблиці `employees`
- побудови місячного звіту на основі таблиць `employees` + `visits`
- перегляду відвідувань конкретного співробітника

## Логіка розрахунку

У таблиці `visits` немає окремої колонки з сумою.
Тому сума рахується так:
- 1 відвідування = `employees.money` цього співробітника
- день = сума `money` всіх співробітників, які відвідали їдальню цього дня
- місяць = сума всіх денних значень
- співробітник за місяць = `COUNT(visits) * employees.money`

## Структура таблиць

### employees
- `id`
- `rfid`
- `full_name`
- `active`
- `updated_at`
- `money`

### visits
- `id`
- `employee_id`
- `visit_time`
- `source`

## Запуск у Docker

1. Скопіюйте `.env.example` у `.env`
2. Заповніть доступ до вашої MySQL
3. Запустіть:

```bash
docker compose up --build -d
```

4. Відкрийте в браузері:

```bash
http://localhost:8000
```

## Важливо

Якщо MySQL працює на хості, часто зручно використовувати:
- `DB_HOST=host.docker.internal`

Для Linux інколи треба або:
- додати `extra_hosts`
- або вказати реальну IP-адресу сервера MySQL



Для створення оператора з паролем admin123
from werkzeug.security import generate_password_hash
print(generate_password_hash("admin123"))