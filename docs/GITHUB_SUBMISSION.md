# Посилання для здавання роботи

- Репозиторій: [AlexPakn/rest-microservices-bughunt](https://github.com/AlexPakn/rest-microservices-bughunt).
- Готова версія: [гілка solution](https://github.com/AlexPakn/rest-microservices-bughunt/tree/solution).
- Звіт із 15 скриншотами pytest: [BUG_REPORT.md](https://github.com/AlexPakn/rest-microservices-bughunt/blob/solution/docs/BUG_REPORT.md).
- Початковий код із помилками: [тег baseline](https://github.com/AlexPakn/rest-microservices-bughunt/tree/baseline).
- Тести: [tests/](https://github.com/AlexPakn/rest-microservices-bughunt/tree/solution/tests).
- Протоколи скриншотів: [docs/evidence/pytest/](https://github.com/AlexPakn/rest-microservices-bughunt/tree/solution/docs/evidence/pytest).
- Успішна автоматична перевірка: [GitHub Actions](https://github.com/AlexPakn/rest-microservices-bughunt/actions/runs/39423880736).

Репозиторій відкритий (public), головна гілка — `solution`.
На початковому коді 53 failed / 3 passed, після виправлень 56 passed.
Скриншоти показують реальний вивід pytest на початковому коді для кожного B01–B13
та загальні результати до/після. GitHub Actions додатково перевірив pytest і реальний HTTP
трьох сервісів на Ubuntu із Python 3.11. Docker-запуск не виконувався.

## Окремі pull request

PR залишено відкритими для перевірки. Кожен порівнюється з попередньою fix-гілкою,
перший — із `main`; у кожному порівнянні рівно одне нове виправлення.

| Дефект | Виправлення | Pull request |
|---|---|---|
| B01 | Перенести login у POST із JSON | [PR #1](https://github.com/AlexPakn/rest-microservices-bughunt/pull/1) |
| B02 | Повертати 401 для неправильних облікових даних | [PR #2](https://github.com/AlexPakn/rest-microservices-bughunt/pull/2) |
| B03 | Читати Authorization із заголовка | [PR #3](https://github.com/AlexPakn/rest-microservices-bughunt/pull/3) |
| B04 | Повертати 401 при відсутній авторизації | [PR #4](https://github.com/AlexPakn/rest-microservices-bughunt/pull/4) |
| B05 | Перевіряти видані Bearer-токени та строк дії | [PR #5](https://github.com/AlexPakn/rest-microservices-bughunt/pull/5) |
| B06 | Повертати 404 для відсутнього товару | [PR #6](https://github.com/AlexPakn/rest-microservices-bughunt/pull/6) |
| B07 | Зафіксувати контракт Product | [PR #7](https://github.com/AlexPakn/rest-microservices-bughunt/pull/7) |
| B08 | Заборонити створення замовлення після відмови Auth | [PR #8](https://github.com/AlexPakn/rest-microservices-bughunt/pull/8) |
| B09 | Валідувати вхідне замовлення | [PR #9](https://github.com/AlexPakn/rest-microservices-bughunt/pull/9) |
| B10 | Перевіряти існування замовленого товару | [PR #10](https://github.com/AlexPakn/rest-microservices-bughunt/pull/10) |
| B11 | Перевіряти доступний залишок | [PR #11](https://github.com/AlexPakn/rest-microservices-bughunt/pull/11) |
| B12 | Обробляти збої та контракти залежностей | [PR #12](https://github.com/AlexPakn/rest-microservices-bughunt/pull/12) |
| B13 | Обмежити список замовлень їхнім власником | [PR #13](https://github.com/AlexPakn/rest-microservices-bughunt/pull/13) |

Не потрібно об'єднувати PR, щоб переглянути готову систему: повна версія вже є у `solution`.
Правила послідовного об'єднання — у [PULL_REQUESTS.md](PULL_REQUESTS.md).
