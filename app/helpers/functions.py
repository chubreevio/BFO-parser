def validate_inn(inn: str) -> tuple[bool, str]:
    """
    Проверка ИНН юридических лиц

    :param inn: Строка с ИНН организации

    :return: Корректен ИНН или нет
    :return: Текст с результатом валидации
    """
    inn = inn.strip()
    if not inn.isdigit():
        return False, "ИНН должен содержать только цифры"
    if len(inn) != 10:
        return False, "ИНН юридического лица должен содержать 10 цифр"
    # Проверка контрольной суммы
    coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    control_sum = sum(int(inn[i]) * coefficients[i] for i in range(9))
    control_digit = control_sum % 11 % 10

    if int(inn[9]) != control_digit:
        return False, "Неверная контрольная сумма ИНН"

    if inn[0] == "0":
        return False, "Первая цифра ИНН не может быть нулем"

    return True, inn
