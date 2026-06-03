# Анекдот в Тему — VK Mini App

## Деплой в VK Mini Apps

### 1. Создание приложения

1. Перейдите на [vk.com/editapp?act=create](https://vk.com/editapp?act=create)
2. Выберите платформу **Mini Apps**
3. Заполните данные:
   - **Название:** `Анекдот в тему`
   - **Описание:** `112K+ анекдотов по контексту`
4. После создания скопируйте **App ID** из настроек

### 2. Настройка хостинга

Приложение состоит из одного файла `index.html` и может быть размещено на любом статическом хостинге:

**Вариант A — VK Mini Apps Hosting (рекомендуется):**

```bash
# Установите CLI
npm install -g @vkontakte/vk-miniapps-deploy

# Авторизуйтесь
vk-miniapps-deploy

# Деплой
vk-miniapps-deploy --appId YOUR_APP_ID
```

**Вариант B — GitHub Pages:**

1. Загрузите `index.html` и `manifest.json` в репозиторий GitHub
2. Включите GitHub Pages в настройках репозитория
3. Скопируйте URL (например, `https://username.github.io/repo/`)

**Вариант C — Netlify / Vercel:**

1. Создайте новый проект из папки `vkapp/`
2. Деплой произойдёт автоматически
3. Скопируйте URL

### 3. Подключение приложения в VK

1. Откройте [vk.com/editapp](https://vk.com/editapp) → ваше приложение
2. В разделе **Настройки** укажите:
   - **URL приложения:** ваш хостинг URL
   - **API:** включите `VKWebAppShare` и другие нужные методы
3. В файле `index.html` замените `__APP_ID__` в функции `shareJoke()` на ваш App ID
4. В файле `manifest.json` замените `YOUR_APP_ID` на ваш App ID

### 4. Настройка API

Приложение ожидает backend API по адресу из параметра `?api=` в URL или `http://localhost:8000` по умолчанию.

Необходимые эндпоинты:

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/joke/random` | Случайная шутка (`?category=` опционально) |
| GET | `/api/jokes/context` | Подбор по контексту (`?q=тема`) |
| GET | `/api/categories` | Список категорий |
| GET | `/api/jokes/social/top` | Топ шуток (`?limit=5`) |
| POST | `/api/joke/{id}/rate` | Оценка шутки (`{"score":1}`) |

При деплое передавайте URL API:
```
https://your-hosting.com/index.html?api=https://api.your-domain.com
```

### 5. Тестирование

Для локальной разработки используйте [VK Mini Apps Dev](https://dev.vk.com/mini-apps/development/Testing):

```bash
# Локальный сервер
npx serve vkapp/

# Откройте в VK Dev через localhost URL
```

### 6. Публикация

1. После тестирования переведите приложение в статус **Опубликовано** в настройках
2. Пройдите модерацию VK
3. После одобрения приложение будет доступно всем пользователям VK

---

## Структура файлов

```
vkapp/
├── index.html      # Полное приложение (inline JS + CSS)
├── manifest.json   # Манифест VK Mini App
└── README.md       # Эта инструкция
```
