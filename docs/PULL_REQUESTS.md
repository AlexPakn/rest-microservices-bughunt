# Гілки та pull request

Усі гілки опубліковано в [AlexPakn/rest-microservices-bughunt](https://github.com/AlexPakn/rest-microservices-bughunt).
**Створено 13 відкритих PR №1–13**; [повна таблиця посилань](GITHUB_SUBMISSION.md).
Тексти PR готові в `docs/prs/`, машинозчитуваний план — `docs/pr-plan.json`,
окремі поштові Git-патчі — `patches/B01.patch` … `patches/B13.patch`.
Патчі застосовуються послідовно з `baseline`, а не незалежно один від одного.

## План

| ID | Гілка head | База PR | Commit | Текст |
|---|---|---|---|---|
| B01 | `fix/b01-post-login-body` | `main` | `082e3dc` | [опис](prs/B01.md) |
| B02 | `fix/b02-login-unauthorized` | `fix/b01-post-login-body` | `49a581e` | [опис](prs/B02.md) |
| B03 | `fix/b03-authorization-header` | `fix/b02-login-unauthorized` | `19f5baf` | [опис](prs/B03.md) |
| B04 | `fix/b04-whoami-unauthorized` | `fix/b03-authorization-header` | `f67d272` | [опис](prs/B04.md) |
| B05 | `fix/b05-validate-issued-bearer-tokens` | `fix/b04-whoami-unauthorized` | `e35c5d8` | [опис](prs/B05.md) |
| B06 | `fix/b06-product-not-found` | `fix/b05-validate-issued-bearer-tokens` | `bfef2d7` | [опис](prs/B06.md) |
| B07 | `fix/b07-product-contract` | `fix/b06-product-not-found` | `e7840e2` | [опис](prs/B07.md) |
| B08 | `fix/b08-enforce-order-authentication` | `fix/b07-product-contract` | `1736b59` | [опис](prs/B08.md) |
| B09 | `fix/b09-validate-order-input` | `fix/b08-enforce-order-authentication` | `bd3e94e` | [опис](prs/B09.md) |
| B10 | `fix/b10-require-existing-product` | `fix/b09-validate-order-input` | `54ae37b` | [опис](prs/B10.md) |
| B11 | `fix/b11-check-available-stock` | `fix/b10-require-existing-product` | `64f77a0` | [опис](prs/B11.md) |
| B12 | `fix/b12-handle-upstream-failures` | `fix/b11-check-available-stock` | `f46912a` | [опис](prs/B12.md) |
| B13 | `fix/b13-isolate-user-orders` | `fix/b12-handle-upstream-failures` | `bd5e3c0` | [опис](prs/B13.md) |

`main` і тег `baseline` містять початковий код із багами та регресійними тестами.
`solution` містить B01–B13 і документацію. Гілки fix утворюють ланцюжок,
щоб кожен PR показував один новий патч. Це залежні PR, а не 13 незалежних виправлень.

## Повторна публікація в інший репозиторій

Поточний репозиторій уже опубліковано. Наведені нижче команди для створення нового репозиторію
виконувати не потрібно; вони залишені як інструкція для перенесення.

Потрібні GitHub CLI (`gh`) та його авторизований обліковий запис.
Створювати GitHub-репозиторій вручну слід **порожнім**, без README та початкового комміту.
Паролі, токени доступу та коди входу у файли проєкту не додаються.

Новий приватний репозиторій і 13 PR (замініть `ACCOUNT` на власний акаунт):

```powershell
gh auth login
.\scripts\publish_github.ps1 -Repository ACCOUNT/rest-microservices-bughunt -Visibility private -CreateRepository
```

Для вже створеного порожнього репозиторію:

```powershell
.\scripts\publish_github.ps1 -Repository ACCOUNT/rest-microservices-bughunt
```

Для відкритого репозиторію при створенні явно вкажіть `-Visibility public`.
Сценарій перевіряє чистий стан `solution`, адресу origin, надсилає потрібні гілки й тег,
створює PR за планом. Він не об'єднує PR та не виконує force-push.
При повторному запуску на тому самому репозиторії без `-CreateRepository`
використовує вже наявні PR із тією самою парою head/base.
Адреси PR записуються в `artifacts/pull-requests.json` після кожного успішного кроку.
PowerShell-сценарій синтаксично перевірено, але з реальним GitHub не виконувався.
Поточну публікацію виконано через Git, а PR створено сценарієм `scripts/create_github_prs.py`,
який використовує вже виконаний вхід Git без виведення чи збереження секретів.
Для перевірки вже опублікованих PR без встановлення `gh` можна виконати:

```powershell
python scripts/create_github_prs.py AlexPakn/rest-microservices-bughunt --check
```

## Перегляд та об'єднання

1. Відкрийте B01: база `main`, head `fix/b01-post-login-body`.
2. Для B02 база — B01, і так далі за таблицею.
3. Об'єднуйте в порядку B01 → B13. Після об'єднання попереднього PR
   змініть базу наступного на `main` через GitHub. До цього не видаляйте попередню гілку.
4. Використовуйте **Create a merge commit**, щоб зберегти ancestry для залежних PR.
   Squash/rebase для цього підготовленого ланцюжка можуть повторно показати попередні зміни.
5. Матеріали з `solution` можна додати в main окремим PR після всіх виправлень.
   Поточний сценарій створює саме 13 PR з виправленнями; PR документації до нього не включено.

На частково виправлених гілках повний набір тестів ще падає — це очікувано.
Для окремого PR запускайте `python -m pytest -q -k b01` (або відповідний номер).
На `solution` усі 56 перевірок мають пройти. GitHub Actions налаштовано на push у `solution`
та ручний запуск. [Віддалена перевірка на Ubuntu / Python 3.11 успішна](https://github.com/AlexPakn/rest-microservices-bughunt/actions/runs/39423880736).

## Резервна копія історії

Поруч із папкою проєкту підготовлено `rest-microservices-bughunt.bundle`.
Перенесення зі збереженням усіх fix-гілок:

```powershell
git clone --mirror rest-microservices-bughunt.bundle restored.git
git -C restored.git worktree add ../restored solution
cd restored
```

Перший клон зберігає всі локальні гілки; друга команда відкриває робочу копію `solution`.
Папку `restored.git` потрібно зберігати поруч: вона містить Git-історію цієї робочої копії.
Без Git-історії (наприклад, лише ZIP вихідних файлів) `scripts/verify.py` не зможе отримати baseline.
