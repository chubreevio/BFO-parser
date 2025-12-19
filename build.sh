#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Останавливаем и собираем заново
docker-compose -f "docker-compose.yml" -p bfo-parser down --remove-orphans
docker-compose -f "docker-compose.yml" -p bfo-parser build

# Запускаем все сервисы
docker-compose up -d bfo-parser-api--db bfo-parser-api--redis

# Ждем готовности основной БД
echo "Ожидание готовности основной БД..."
for i in {1..30}; do
    if docker exec bfo-parser-api--db pg_isready -U ${DB_USERNAME} > /dev/null 2>&1; then
        echo "Основная БД готова!"
        break
    fi
    echo -n "."
    sleep 1
done

# Запускаем тестовую БД
echo "Запуск тестовой БД..."
docker-compose up -d bfo-parser-api--db-test

# Ждем готовности тестовой БД
echo "Ожидание готовности тестовой БД..."
for i in {1..30}; do
    if docker exec bfo-parser-api--db-test pg_isready -U ${DB_USERNAME} > /dev/null 2>&1; then
        echo "Тестовая БД готова!"
        break
    fi
    echo -n "."
    sleep 1
done

# Запускаем тесты в контейнере приложения
echo "Запуск тестов..."
TEST_RESULT=$(docker-compose run --rm bfo-parser-api--app sh -c "
  export DATABASE_URL='postgresql://${DB_USERNAME}:${DB_TEST_PASSWORD}@bfo-parser-api--db-test:5432/${DB_DATABASE}'
  echo '=== Запуск тестов ==='
  pytest -v
  exit \$?
")

# Сохраняем код возврата
TEST_EXIT_CODE=$?

# Выводим результат тестов
echo "$TEST_RESULT"

# Проверяем результат тестов
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=== Тесты прошли успешно, запуск приложения ===${NC}"
    
    # Останавливаем тестовую БД (она больше не нужна)
    docker-compose stop bfo-parser-api--db-test
    
    # Запускаем приложение
    docker-compose up -d bfo-parser-api--app
    
    # Ждем запуска приложения и выводим логи
    echo "Ожидание запуска приложения..."
    sleep 3
    docker-compose logs --tail=20 bfo-parser-api--app
else
    echo -e "${RED}=== Тесты не прошли, приложение не запущено ===${NC}"
    exit 1
fi