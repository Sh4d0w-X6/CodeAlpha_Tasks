"""
CodeAlpha Task 3 - FINAL FIXED VERSION
AI Music Generator (Markov + Stable GUI + Playback)
"""

import os
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

# Install deps
def install(pkg):
    import importlib, subprocess, sys
    try:
        importlib.import_module(pkg)
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install("music21")

from music21 import stream, note, chord, duration, tempo, instrument

# ── MARKOV GENERATOR ───────────────────────────
class MarkovMusicGenerator:
    SCALES = {
        "C Major": ["C4","D4","E4","F4","G4","A4","B4","C5"],
        "A Minor": ["A3","B3","C4","D4","E4","F4","G4","A4"],
        "Pentatonic": ["C4","D4","E4","G4","A4","C5"]
    }

    def generate(self, scale_name, num_notes=40, bpm=120):
        scale = self.SCALES.get(scale_name, self.SCALES["C Major"])

        transition = {}  # FIX: reset every time

        for i in range(len(scale)-1):
            transition.setdefault(scale[i], []).append(scale[i+1])

        s = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Piano())
        p.insert(0, tempo.MetronomeMark(number=bpm))

        current = random.choice(scale)

        for _ in range(num_notes):
            if random.random() < 0.2:
                c = chord.Chord(random.sample(scale, 3))
                c.duration = duration.Duration(random.choice([0.5, 1]))
                p.append(c)
            else:
                n = note.Note(current)
                n.duration = duration.Duration(random.choice([0.25, 0.5, 1]))
                p.append(n)

            current = random.choice(transition.get(current, scale))

        s.append(p)
        return s


# ── GUI ───────────────────────────────────────
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 AI Music Generator")
        self.root.geometry("650x500")

        self.gen = MarkovMusicGenerator()
        self.score = None

        self.build()

    def build(self):
        tk.Label(self.root, text="🎵 AI Music Generator",
                 font=("Arial", 18, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack()

        tk.Label(frame, text="Scale").grid(row=0, column=0)
        self.scale = ttk.Combobox(frame, values=list(self.gen.SCALES.keys()))
        self.scale.set("C Major")
        self.scale.grid(row=0, column=1)

        tk.Label(frame, text="Notes").grid(row=0, column=2)
        self.notes = tk.IntVar(value=40)
        ttk.Spinbox(frame, from_=20, to=100, textvariable=self.notes).grid(row=0, column=3)

        tk.Label(frame, text="BPM").grid(row=0, column=4)
        self.bpm = tk.IntVar(value=120)
        ttk.Spinbox(frame, from_=60, to=200, textvariable=self.bpm).grid(row=0, column=5)

        # Buttons
        btn = tk.Frame(self.root)
        btn.pack(pady=10)

        tk.Button(btn, text="Generate", command=self.generate).grid(row=0, column=0, padx=5)
        tk.Button(btn, text="Play", command=self.play).grid(row=0, column=1, padx=5)
        tk.Button(btn, text="Save MIDI", command=self.save).grid(row=0, column=2, padx=5)

        # Log
        self.log = tk.Text(self.root, height=10)
        self.log.pack(fill="both", expand=True)

    def log_msg(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def generate(self):
        self.log_msg("Generating...")
        threading.Thread(target=self._gen_thread, daemon=True).start()

    def _gen_thread(self):
        try:
            score = self.gen.generate(
                self.scale.get(),
                self.notes.get(),
                self.bpm.get()
            )
            self.score = score

            # FIX: .flat replaced
            notes = []
            for e in score.recurse().notes:
                if isinstance(e, note.Note):
                    notes.append(e.nameWithOctave)
                elif isinstance(e, chord.Chord):
                    notes.append("Chord")

            preview = " ".join(notes[:10])

            self.root.after(0, lambda: self.log_msg(f"Done: {preview}..."))

        except Exception as e:
            self.root.after(0, lambda: self.log_msg(f"Error: {e}"))

    def play(self):
        if not self.score:
            messagebox.showwarning("No music", "Generate first!")
            return
        self.log_msg("Playing...")
        threading.Thread(target=lambda: self.score.show('midi'), daemon=True).start()

    def save(self):
        if not self.score:
            messagebox.showwarning("No music", "Generate first!")
            return

        path = filedialog.asksaveasfilename(defaultextension=".mid")
        if path:
            self.score.write("midi", fp=path)
            self.log_msg(f"Saved: {os.path.basename(path)}")


# ── RUN ───────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
