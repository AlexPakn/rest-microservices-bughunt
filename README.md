# REST мікросервіси

Готова виправлена версія навчальної системи AuthService, ProductService та OrderService.
Сервіси перевіряють авторизацію, вхідні дані, існування товару й доступний залишок;
помилки залежностей повертаються з явними HTTP статусами.

[Звіт Word зі скриншотами pytest та поясненнями](report.docx)

## Запуск

```powershell
docker compose up --build
```

| Сервіс | Документація API |
|---|---|
| Auth | http://localhost:8001/docs |
| Product | http://localhost:8002/docs |
| Order | http://localhost:8003/docs |

Вхід: `POST /login`, JSON `{"email":"alice@example.com","password":"alice123"}`.
Токен із поля `access_token` передається в заголовку `Authorization: Bearer <token>`.
Створення замовлення: `POST /orders`, JSON `{"productId":100,"qty":1}`.

## Тести

Потрібен Python 3.11 або 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/smoke_http.py --start
```

Результат: **56 passed**. HTTP перевірка трьох сервісів також успішна.
Тести всередині Docker:

```powershell
docker compose -f compose.test.yml run --build --rm tests
```

Дані та сесії зберігаються в пам’яті й зникають після перезапуску.
Залишок товару перевіряється без резервування чи списання.
Паролі демонстраційні, контейнерний запуск локально не перевірявся.
