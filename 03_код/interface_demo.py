import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import os
import sys

def process_payment():
    btn_pay.config(state=tk.DISABLED, text="Обработка...")
    root.update()
    root.after(500, perform_request) # Небольшая задержка для реализма

def perform_request():
    # 1. Формируем JSON как в реальном запросе
    payload = {
        "order_id": entry_order.get(),
        "recipient": "clinic_medservice",
        "purpose": "Приём терапевта",
        "amount": 2500.00,
        "currency": "RUB"
    }
    
    # Сохраняем во временный файл
    temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_payment.json")    
    
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    try:
        # 2. ВЫЗЫВАЕМ НАШ БЭКЕНД (05_app.py)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(base_dir, "05_app.py")
        result = subprocess.run(
            [sys.executable, "05_app.py", temp_file], 
            capture_output=True, text=True, encoding="utf-8"
        )
        
        # 3. Читаем ответ от бэкенда
        if result.stdout:
            response = json.loads(result.stdout)
            
            if response["status"] == "SUCCESS":
                messagebox.showinfo("Успех", f"Платеж {response['payment_id']} прошел!")
            elif response["status"] == "DECLINED":
                messagebox.showerror("Отказ", f"Ошибка: {response['error_code']}")
            elif response["status"] == "TIMEOUT":
                messagebox.showwarning("Таймаут", f"Ошибка: {response['error_code']}")
            elif response["status"] == "ERROR":
                messagebox.showerror("Ошибка валидации", "Проверьте введенные данные.")
        else:
            messagebox.showerror("Ошибка", f"Сбой сервиса. Ошибка: {result.stderr}")

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось связаться с сервисом: {e}")
    finally:
        # Убираем временный файл
        if os.path.exists(temp_file):
            os.remove(temp_file)
        # Возвращаем кнопку
        btn_pay.config(state=tk.NORMAL, text="Оплатить")

    
# --- Настройка окна (Tkinter) ---
root = tk.Tk()
root.title("Мед-Сервис: Оплата")
root.geometry("350x650")
root.configure(bg="#f0f2f5")
root.resizable(False, False)

header_frame = tk.Frame(root, bg="#007bff", height=80)
header_frame.pack(fill=tk.X)
header_frame.pack_propagate(False)
lbl_header = tk.Label(header_frame, text="Клиника\nМед-Сервис", font=("Segoe UI", 16, "bold"), bg="#007bff", fg="white")
lbl_header.pack(expand=True)

card_frame = tk.Frame(root, bg="white", bd=1, relief=tk.SOLID)
card_frame.pack(pady=20, padx=20, fill=tk.X)

lbl_title = tk.Label(card_frame, text="Услуга: Приём терапевта", font=("Segoe UI", 14), bg="white", anchor="w")
lbl_title.pack(pady=(15, 5), padx=15, fill=tk.X)
lbl_price = tk.Label(card_frame, text="2 500,00 ₽", font=("Segoe UI", 24, "bold"), fg="#007bff", bg="white", anchor="w")
lbl_price.pack(pady=(0, 5), padx=15, fill=tk.X)
lbl_recipient = tk.Label(card_frame, text="Получатель: clinic_medservice", font=("Segoe UI", 10), fg="#888", bg="white", anchor="w")
lbl_recipient.pack(pady=(0, 15), padx=15, fill=tk.X)

tk.Label(root, text="Тестовый order_id:", bg="#f0f2f5", font=("Segoe UI", 9)).pack(pady=(10,0))
entry_order = tk.Entry(root, justify="center")
entry_order.insert(0, "ord_1001")
entry_order.pack(pady=5)

btn_pay = tk.Button(root, text="Оплатить", font=("Segoe UI", 16, "bold"), bg="#28a745", fg="white", 
                    activebackground="#218838", activeforeground="white", bd=0, height=2, cursor="hand2",
                    command=process_payment)
btn_pay.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=30)

root.mainloop()