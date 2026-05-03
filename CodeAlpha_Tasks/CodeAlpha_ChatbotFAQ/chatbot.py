"""
CodeAlpha Internship - Task 2: FINAL VERSION
Improved FAQ Chatbot using TF-IDF + Cosine Similarity
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import re
import math
from collections import Counter

# ── FAQ DATA ─────────────────────────────────────────────
FAQ_DATA = [
    {"q": "What is CodeAlpha?",
     "a": "CodeAlpha is a leading software development company focused on innovation and emerging technologies."},
    {"q": "How do I apply for the internship?",
     "a": "Apply via www.codealpha.tech or through the WhatsApp group."},
    {"q": "What is the duration of the internship?",
     "a": "The internship lasts about 1 month."},
    {"q": "What tasks are assigned in the AI internship?",
     "a": "Tasks include Chatbot, Music Generation, Object Detection, and Translation Tool."},
    {"q": "Will I get a certificate?",
     "a": "Yes! You will receive a QR-verified certificate and optional LOR."},
    {"q": "How do I submit my project?",
     "a": "Upload to GitHub, post on LinkedIn, and submit via the official form."},
    {"q": "Is the internship paid?",
     "a": "It may be unpaid but offers certificates, LOR, and experience."},
    {"q": "What programming languages can I use?",
     "a": "Python is commonly used with libraries like OpenCV, TensorFlow, and NLTK."},
    {"q": "How do I contact CodeAlpha?",
     "a": "Email: services@codealpha.tech | WhatsApp: +91 9336576683"},
    {"q": "What happens if I submit only one task?",
     "a": "You must complete at least 2 tasks to get the certificate."},
    {"q": "Hello",
     "a": "Hello! 👋 I'm your FAQ bot. Ask me anything!"},
    {"q": "Thank you",
     "a": "You're welcome! 😊"},
]

# ── SYNONYMS ─────────────────────────────────────────────
SYNONYMS = {
    "register": "apply",
    "enroll": "apply",
    "upload": "submit",
    "send": "submit",
    "proof": "certificate"
}

# ── TOKENIZER ────────────────────────────────────────────
def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    tokens = [t for t in tokens if len(t) > 2]
    return [SYNONYMS.get(t, t) for t in tokens]

# ── TF-IDF ───────────────────────────────────────────────
def tfidf_vectors(corpus, query):
    docs = corpus + [query]
    N = len(docs)

    df = Counter()
    for doc in docs:
        for word in set(doc):
            df[word] += 1

    idf = {w: math.log(N / (1 + df[w])) for w in df}

    def tfidf(doc):
        tf = Counter(doc)
        total = len(doc) or 1
        return {w: (tf[w] / total) * idf[w] for w in tf}

    return [tfidf(doc) for doc in docs]

def cosine(v1, v2):
    keys = set(v1) | set(v2)
    dot = sum(v1.get(k, 0) * v2.get(k, 0) for k in keys)
    mag1 = math.sqrt(sum(x*x for x in v1.values()))
    mag2 = math.sqrt(sum(x*x for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0
    return dot / (mag1 * mag2)

# ── CHATBOT ──────────────────────────────────────────────
class Chatbot:
    def __init__(self):
        self.questions = [x["q"] for x in FAQ_DATA]
        self.answers = [x["a"] for x in FAQ_DATA]
        self.corpus = [tokenize(q) for q in self.questions]

    def reply(self, msg):
        if msg.lower() in ["exit", "quit", "bye"]:
            return "Goodbye! 👋"

        query = tokenize(msg)
        if not query:
            return "Please rephrase your question."

        vecs = tfidf_vectors(self.corpus, query)
        q_vec = vecs[-1]
        docs = vecs[:-1]

        scores = [cosine(d, q_vec) for d in docs]
        best = max(range(len(scores)), key=lambda i: scores[i])

        if scores[best] < 0.15:
            return "Try asking about: tasks, certificate, apply, submission, contact."

        return self.answers[best]

# ── GUI ──────────────────────────────────────────────────
class App:
    def __init__(self, root):
        self.bot = Chatbot()
        self.root = root
        self.root.title("FAQ Chatbot")
        self.root.geometry("700x550")
        self.root.configure(bg="#0d1117")

        self.chat = scrolledtext.ScrolledText(
            root, wrap="word", bg="#161b22", fg="#c9d1d9",
            font=("Consolas", 11), state="disabled"
        )
        self.chat.pack(fill="both", expand=True, padx=10, pady=10)

        frame = tk.Frame(root, bg="#161b22")
        frame.pack(fill="x")

        self.entry = tk.Entry(frame, font=("Consolas", 12),
                              bg="#21262d", fg="white")
        self.entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", lambda e: self.send())

        tk.Button(frame, text="Send", bg="#238636", fg="white",
                  command=self.send).pack(side="right", padx=10)

        # Suggestions
        sug_frame = tk.Frame(root, bg="#0d1117")
        sug_frame.pack()
        for s in ["Certificate", "Apply", "Submit", "Contact"]:
            tk.Button(sug_frame, text=s,
                      command=lambda s=s: self.send(s)).pack(side="left", padx=5)

        self.bot_msg("Hello! 👋 Ask me anything.")

    def send(self, text=None):
        msg = text or self.entry.get().strip()
        if not msg:
            return
        self.entry.delete(0, tk.END)
        self.user_msg(msg)

        threading.Thread(target=self.respond, args=(msg,), daemon=True).start()

    def respond(self, msg):
        res = self.bot.reply(msg)
        self.root.after(0, lambda: self.bot_msg(res))

    def user_msg(self, msg):
        self.chat.config(state="normal")
        self.chat.insert("end", f"\nYou: {msg}\n", "user")
        self.chat.config(state="disabled")
        self.chat.see("end")

    def bot_msg(self, msg):
        self.chat.config(state="normal")
        self.chat.insert("end", f"Bot: {msg}\n")
        self.chat.insert("end", "-"*50 + "\n")
        self.chat.config(state="disabled")
        self.chat.see("end")

# ── RUN ──────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
