# SEIBELGRAM FUTURE CARS — технический запуск

Проект полностью отделён от APP24K / FLOW24K.

**Пока нет реального подключения к Cloudflare, Buffer, TikTok или Instagram.**
Все публикации отключены по умолчанию. Рабочий процесс умеет сгенерировать явно помеченный демонстрационный MP4, не обращаясь к платным API.

## Этап A. Безопасный тест (уже можно запускать)

GitHub → Actions → **SEIBELGRAM — safe generator** → Run workflow → оставь **demo=true, publish=false**.
После выполнения скачай artifact **seibelgram-preview**. Он содержит MP4 и JSON.
Это демонстрация без AI-изображений и без публикации.

## Этап B. Cloudflare Free

Создай бесплатный Workers AI API Token и получи Cloudflare Account ID.
GitHub → Settings → Secrets and variables → Actions → Repository secrets:
- CF_ACCOUNT_ID
- CF_API_TOKEN

Запусти workflow вручную с demo=false, publish=false. Он сгенерирует AI-картинки и MP4, но ничего не опубликует. Не пересылай токены в чат.

## Этап C. Buffer Free (после проверки AI-видео)

Подключи свой TikTok @seibelgram к Buffer. Instagram можно добавить позже.
Полученный API ключ сохрани в Repository secrets как BUFFER_API_KEY.
ID каналов сохрани в Repository variables: BUFFER_CHANNEL_TIKTOK и, по желанию, BUFFER_CHANNEL_INSTAGRAM.

Программа проверяет, что TikTok-канал Buffer действительно называется seibelgram. Демонстрационные ролики публиковать запрещено.

## Этап D. Публичный хостинг и публикация

Для отправки в Buffer видео должно размещаться по общедоступной HTTPS-ссылке, например на GitHub Pages.
Включение GitHub Pages и настройка хранения архива публикаций — отдельный следующий шаг. Публикация по умолчанию выключена.

**Не вводи ключи прямо в GitHub файлы или чат. Никакие платные планы не включай.**
