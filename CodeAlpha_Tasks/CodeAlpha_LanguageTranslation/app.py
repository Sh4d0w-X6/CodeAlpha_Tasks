"""
CodeAlpha Task 1 - FINAL PRO VERSION
Real-Time Language Translator (Auto + Live + TTS)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Install if missing
try:
    from deep_translator import GoogleTranslator
except:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "deep-translator"])
    from deep_translator import GoogleTranslator

try:
    import pyttsx3
    TTS_AVAILABLE = True
except:
    TTS_AVAILABLE = False


class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 Real-Time Translator")
        self.root.geometry("850x600")
        self.root.configure(bg="#1a1a2e")

        self.last_text = ""
        self.typing_delay = 600  # ms
        self.typing_job = None

        # 🌍 Get ALL supported languages dynamically
        self.languages = GoogleTranslator().get_supported_languages(as_dict=True)

        self._build_ui()

    def _build_ui(self):
        tk.Label(self.root, text="🌐 Real-Time Translator",
                 font=("Helvetica", 20, "bold"),
                 fg="#e94560", bg="#1a1a2e").pack(pady=10)

        # Language selectors
        frame = tk.Frame(self.root, bg="#1a1a2e")
        frame.pack()

        self.src = ttk.Combobox(frame, values=["auto"] + list(self.languages.keys()), width=25)
        self.src.set("auto")
        self.src.grid(row=0, column=0, padx=10)

        tk.Label(frame, text="→", fg="white", bg="#1a1a2e",
                 font=("Arial", 14)).grid(row=0, column=1)

        self.tgt = ttk.Combobox(frame, values=list(self.languages.keys()), width=25)
        self.tgt.set("hindi")
        self.tgt.grid(row=0, column=2, padx=10)

        tk.Button(frame, text="Swap", command=self.swap).grid(row=0, column=3, padx=10)

        # Text boxes
        text_frame = tk.Frame(self.root, bg="#1a1a2e")
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.input = tk.Text(text_frame, font=("Consolas", 12),
                             bg="#16213e", fg="white")
        self.input.grid(row=0, column=0, sticky="nsew", padx=5)

        self.output = tk.Text(text_frame, font=("Consolas", 12),
                              bg="#16213e", fg="#4ecca3", state="disabled")
        self.output.grid(row=0, column=1, sticky="nsew", padx=5)

        text_frame.columnconfigure(0, weight=1)
        text_frame.columnconfigure(1, weight=1)
        text_frame.rowconfigure(0, weight=1)

        # Buttons
        btn = tk.Frame(self.root, bg="#1a1a2e")
        btn.pack()

        tk.Button(btn, text="Translate", command=self.translate).grid(row=0, column=0, padx=10)
        tk.Button(btn, text="Clear", command=self.clear).grid(row=0, column=1, padx=10)
        tk.Button(btn, text="Copy", command=self.copy).grid(row=0, column=2, padx=10)

        if TTS_AVAILABLE:
            tk.Button(btn, text="Speak", command=self.speak).grid(row=0, column=3, padx=10)

        # Status
        self.status = tk.Label(self.root, text="Ready",
                               bg="#0f3460", fg="white", anchor="w")
        self.status.pack(fill="x", side="bottom")

        # 🎯 REAL-TIME TRANSLATION TRIGGER
        self.input.bind("<KeyRelease>", self.on_typing)

    # ── REAL-TIME HANDLER ─────────────────────────
    def on_typing(self, event):
        if self.typing_job:
            self.root.after_cancel(self.typing_job)
        self.typing_job = self.root.after(self.typing_delay, self.translate)

    # ── TRANSLATION ───────────────────────────────
    def translate(self):
        text = self.input.get("1.0", "end").strip()

        if not text or text == self.last_text:
            return

        self.last_text = text
        self.status.config(text="Translating...")

        threading.Thread(target=self._translate_thread, args=(text,), daemon=True).start()

    def _translate_thread(self, text):
        try:
            src = self.src.get()
            tgt = self.tgt.get()

            result = GoogleTranslator(source=src, target=tgt).translate(text)

            self.root.after(0, lambda: self.update_output(result))

        except Exception as e:
            self.root.after(0, lambda: self.status.config(text=f"Error: {e}"))

    def update_output(self, text):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.config(state="disabled")
        self.status.config(text="Done")

    # ── FEATURES ────────────────────────────────
    def swap(self):
        s = self.src.get()
        t = self.tgt.get()
        if s != "auto":
            self.src.set(t)
            self.tgt.set(s)

    def clear(self):
        self.input.delete("1.0", "end")
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")
        self.status.config(text="Cleared")

    def copy(self):
        text = self.output.get("1.0", "end").strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status.config(text="Copied!")

    def speak(self):
        text = self.output.get("1.0", "end").strip()
        if text:
            threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()


# ── RUN ─────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    TranslatorApp(root)
    root.mainloop()
