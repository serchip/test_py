# Тестовое задание на позицию Python Developer (Billing)

**Важно**

Перед тем как взять задание в работу, оцените его по времени и сообщите нам. Для нас важно качество и выполнение всех заявленных требований.
После реализации важно прокомментировать предложенное решение, выбранные механизмы хранения и обработки данных, оценить плюсы и минусы.
Исходный код проекта нужно разместите на github или bitbucket.

Выбор библиотек, фреймворка, и системы хранения остается на Вашей стороне.

Предполагается что клиенты будут активно использовать данное АПИ для совершения большого кол-ва транзакций. Необходимо гарантировать высокую производительность АПИ и консистентность данных в любой момент времени.
В системе одна валюта - USD.

**Задание**
Необходимо разработать веб-приложение простой платежной системы (для упрощения, все переводы и зачисления без комиссии).
Требования:

1. Каждый клиент в системе имеет один "кошелек", содержащий денежные средства. (При появлении нескольких валют, по хорошему создать бы отдельный кошелек для каждой валюты???)
2. Сохраняется информация о кошельке и остатке средств на нем.
3. Клиенты могут делать друг другу денежные переводы.
4. Сохраняется информация о всех операциях на кошельке клиента.
5. Проект представляет из себя HTTP API, содержащее основные операции по "кошелькам":
    1. создание клиента с кошельком;
    2. зачисление денежных средств на кошелек клиента;
    3. перевод денежных средств с одного кошелька на другой.
6. Весь проект, со всеми зависимостями должен разворачиваться командой docker-compose up.

## Решение:

![preview](/doc/web-api-run.gif)

## How to run it locally

```bash
# Build and run docker containers
make start
```
OR
```bash
docker-compose up
```

Swagger at `http://127.0.0.1/docs`.


## Run tests

```bash
make start
make test
```


## License
This piece of code is licensed under [MIT License](/LICENSE).