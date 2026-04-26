import base64
import io
import threading
import os
from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog
from PIL import Image

# Налаштування загальної теми
set_appearance_mode("dark")
set_default_color_theme("blue")


class MainWindow(CTk):
    def __init__(self):
        super().__init__()

        self.geometry('700x500')
        self.title("Neon Chat Client")

        self.username = "Artem"

        # --- МЕНЮ (Frame) ---
        # Колір фону меню: темно-синій
        self.menu_frame = CTkFrame(self, width=0, height=500, fg_color="#1A1A2E", corner_radius=0)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)

        self.is_show_menu = False
        self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu,
                             width=35, fg_color="#16213E", hover_color="#0F3460")
        self.btn.place(x=5, y=5)

        # --- ОСНОВНИЙ ЧАТ ---
        self.chat_field = CTkScrollableFrame(self, fg_color="#16213E", corner_radius=10)

        # --- ЕЛЕМЕНТИ ВВОДУ ---
        self.message_entry = CTkEntry(self, placeholder_text='Напишіть щось...',
                                      height=45, fg_color="#0F3460", border_color="#E94560")

        self.send_button = CTkButton(self, text='SEND', width=60, height=45,
                                     fg_color="#E94560", hover_color="#C62841", font=("Arial", 12, "bold"),
                                     command=self.send_message)

        self.open_img_button = CTkButton(self, text='📷', width=50, height=45,
                                         fg_color="#0F3460", hover_color="#533483",
                                         command=self.open_image)

        # Прив'язка адаптивності
        self.bind("<Configure>", lambda e: self.adaptive_ui())

        # Елементи меню
        self.menu_label = CTkLabel(self.menu_frame, text='PROFILE', font=("Arial", 16, "bold"), text_color="#E94560")
        self.name_entry = CTkEntry(self.menu_frame, placeholder_text="Новий нік...", fg_color="#0F3460")
        self.save_button = CTkButton(self.menu_frame, text="SAVE", fg_color="#533483", command=self.save_name)

        # Підключення
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} увійшов(ла) в мережу\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            # ВИПРАВЛЕНО: передаємо помилку через замикання err=e
            self.after(200, lambda err=e: self.add_message(f"SYSTEM: Помилка мережі -> {err}"))

    def toggle_show_menu(self):
        self.is_show_menu = not self.is_show_menu
        self.btn.configure(text='◀️' if self.is_show_menu else '▶️')
        self.animate_menu()

    def animate_menu(self):
        curr = self.menu_frame.winfo_width()
        target = 180 if self.is_show_menu else 0

        if self.is_show_menu and curr < target:
            self.menu_frame.configure(width=curr + 20)
            self.after(10, self.animate_menu)
            if curr > 100:
                self.menu_label.pack(pady=(50, 10))
                self.name_entry.pack(pady=5, padx=10, fill="x")
                self.save_button.pack(pady=20)
        elif not self.is_show_menu and curr > target:
            self.menu_frame.configure(width=curr - 20)
            self.after(10, self.animate_menu)
            self.menu_label.pack_forget()
            self.name_entry.pack_forget()
            self.save_button.pack_forget()

    def save_name(self):
        val = self.name_entry.get().strip()
        if val:
            self.username = val
            self.add_message(f"SYSTEM: Ви змінили ім'я на {val}")

    def adaptive_ui(self):
        w, h = self.winfo_width(), self.winfo_height()
        mw = self.menu_frame.winfo_width()

        self.menu_frame.configure(height=h)
        self.chat_field.place(x=mw + 10, y=10)
        self.chat_field.configure(width=w - mw - 35, height=h - 80)

        y_bot = h - 60
        self.message_entry.place(x=mw + 10, y=y_bot)
        self.message_entry.configure(width=w - mw - 145)

        self.open_img_button.place(x=w - 125, y=y_bot)
        self.send_button.place(x=w - 70, y=y_bot)

    def add_message(self, message, img=None):
        # Колір повідомлень: темний з рамкою
        frame = CTkFrame(self.chat_field, fg_color="#0F3460", border_width=1, border_color="#533483")
        frame.pack(pady=5, padx=10, anchor='w', fill='x')

        # Розрахунок ширини тексту
        wrap = self.chat_field.winfo_width() - 50
        if wrap < 100: wrap = 400

        lbl = CTkLabel(frame, text=message, wraplength=wrap,
                       text_color="#FFFFFF", justify='left', compound='top')
        if img:
            lbl.configure(image=img)
        lbl.pack(padx=15, pady=8)

        # Прокрутка
        self.after(10, lambda: self.chat_field._parent_canvas.yview_moveto(1.0))

    def send_message(self):
        msg = self.message_entry.get()
        if msg:
            self.add_message(f"YOU: {msg}")
            try:
                self.sock.sendall(f"TEXT@{self.username}@{msg}\n".encode())
            except:
                self.add_message("SYSTEM: Втрачено зв'язок.")
            self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096)
                if not data: break
                buffer += data.decode('utf-8', errors='ignore')
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.after(0, self.handle_line, line.strip())
            except:
                break

    def handle_line(self, line):
        if not line: return
        p = line.split("@", 3)
        if p[0] == "TEXT" and len(p) >= 3:
            if p[1] != self.username:
                self.add_message(f"{p[1]}: {p[2]}")
        elif p[0] == "IMAGE" and len(p) >= 4:
            if p[1] != self.username:
                try:
                    raw = base64.b64decode(p[3])
                    img = CTkImage(Image.open(io.BytesIO(raw)), size=(250, 250))
                    self.add_message(f"{p[1]} надіслав(ла) фото:", img=img)
                except:
                    pass

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Зображення", "*.png *.jpg *.jpeg")])
        if not path: return
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            self.sock.sendall(f"IMAGE@{self.username}@{os.path.basename(path)}@{b64}\n".encode())
            self.add_message("Ви надіслали фото:", img=CTkImage(Image.open(path), size=(250, 250)))
        except Exception as e:
            self.add_message(f"SYSTEM: Помилка файлу: {e}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()