#!/usr/bin/env python3
"""
CLI-прототип платёжного сервиса — кейс 1.

Использование:
    python 05_app.py payment.json
"""
import csv
import hashlib
import json
import os
import sys
import re  

# Настроука путей
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Проверяем, лежит ли скрипт в папке "03_код" или в корне
if os.path.basename(CURRENT_DIR) == "03_код":
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR) 
else:
    PROJECT_ROOT = CURRENT_DIR 

# Ищем папку с данными
DATA_DIR = os.path.join(PROJECT_ROOT, "01_данные")
if not os.path.exists(DATA_DIR):
    DATA_DIR = CURRENT_DIR # Если папки нет, ищем рядом

RECIPIENTS_CSV = os.path.join(DATA_DIR, "recipients.csv")
OUT_CSV = os.path.join(DATA_DIR, "payments_out.csv")


def load_active_recipients():
    """Прочитать recipients.csv, вернуть set() активных ID."""
    active = set()
    try:
        with open(RECIPIENTS_CSV, encoding="utf-8-sig") as f:            
            for row in csv.DictReader(f):
                if row.get("status") == "ACTIVE":
                    active.add(row["recipient_id"])
    except FileNotFoundError:
        print(f"WARN: {RECIPIENTS_CSV} не найден", file=sys.stderr)
    return active


def validate(payload, active_recipients):
    """Проверка V-1...V-5 (упрощенная версия для защиты)."""
    errors = []
    
    # V-1: Обязательные поля
    for field in ["order_id", "recipient", "purpose", "amount", "currency"]:
        if not payload.get(field):
            errors.append((field, "VALIDATION_ERROR"))
            
    # V-2: Regex для order_id
    if payload.get("order_id"):
        if not re.match(r"^[A-Za-z0-9_\-]{1,64}$", str(payload["order_id"])):
            errors.append(("order_id", "INVALID_FORMAT"))
            
    # V-3: Диапазон суммы
    if payload.get("amount") is not None:
        try:
            amt = float(payload["amount"])
            if amt <= 0 or amt > 1_000_000:
                errors.append(("amount", "AMOUNT_OUT_OF_RANGE"))
        except ValueError:
            errors.append(("amount", "VALIDATION_ERROR"))

    # V-4: Валюта
    if payload.get("currency") and payload["currency"] != "RUB":
        errors.append(("currency", "UNSUPPORTED_CURRENCY"))
        
    # V-5: Проверка получателя
    if payload.get("recipient") and payload["recipient"] not in active_recipients:
        errors.append(("recipient", "RECIPIENT_NOT_FOUND"))

    return errors


def emulate_gateway(order_id):
    """4 сценария (SUCCESS / INSUFFICIENT_FUNDS / CARD_DECLINED / TIMEOUT)."""
    h = int(hashlib.md5(order_id.encode()).hexdigest(), 16) % 10
    
    if h <= 6:
        return "SUCCESS", None
    elif h == 7:
        return "DECLINED", "INSUFFICIENT_FUNDS"
    elif h == 8:
        return "DECLINED", "CARD_DECLINED"
    else: # h == 9
        return "TIMEOUT", "GATEWAY_TIMEOUT"


def main():
    if len(sys.argv) < 2:
        print("Использование: python 05_app.py payment.json")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8-sig") as f:
       payload = json.load(f)
        
    active = load_active_recipients()
    errors = validate(payload, active)

    # Если есть ошибки валидации
    if errors:
        print(json.dumps({
            "status": "ERROR",
            "error_code": "VALIDATION_ERROR",
            "errors": [{"field": f, "code": c} for f, c in errors],
        }, ensure_ascii=False, indent=2))
        sys.exit(2)

    # Если валидация пройдена — идем в шлюз
    status, error_code = emulate_gateway(payload["order_id"])
    
    result = {
        "payment_id": "pay_demo_" + str(payload["order_id"])[-4:],
        "status": status,
        "error_code": error_code,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Запись в CSV (append)
    try:
        with open(OUT_CSV, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([result["payment_id"], payload["order_id"], payload["recipient"], 
                             payload["purpose"], payload["amount"], payload["currency"], 
                             result["status"], result["error_code"]])
    except Exception as e:
        print(f"Ошибка записи в CSV: {e}", file=sys.stderr)

    # Выход с кодом 3 при таймауте
    if status == "TIMEOUT":
        sys.exit(3)
    sys.exit(0 if status == "SUCCESS" else 1)


if __name__ == "__main__":
    main()