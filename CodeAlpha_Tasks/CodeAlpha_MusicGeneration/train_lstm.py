"""
CodeAlpha Task 3 - FINAL LSTM TRAINER
Stable + Compatible + Better Training
"""

import os
import argparse
import pickle
import numpy as np

# ── INSTALL ─────────────────────────
def install(pkg):
    import importlib, subprocess, sys
    try:
        importlib.import_module(pkg)
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install("music21")
install("tensorflow")
install("numpy")

from music21 import corpus, converter, instrument, note, chord
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping


# ── EXTRACT NOTES ───────────────────
def extract_notes(path):
    notes = []
    try:
        midi = converter.parse(path)
        parts = instrument.partitionByInstrument(midi)

        elements = parts.parts[0].recurse() if parts else midi.recurse()

        for el in elements:
            if isinstance(el, note.Note):
                notes.append(str(el.pitch))
            elif isinstance(el, chord.Chord):
                notes.append(".".join(str(n) for n in el.normalOrder))

    except Exception as e:
        print(f"Skip {path}: {e}")

    return notes


# ── LOAD DATA ───────────────────────
def load_data(midi_dir):
    notes = []

    if midi_dir and os.path.isdir(midi_dir):
        print("Loading custom MIDI dataset...")
        for f in os.listdir(midi_dir):
            if f.endswith((".mid", ".midi")):
                notes.extend(extract_notes(os.path.join(midi_dir, f)))
    else:
        print("Using music21 Bach dataset...")
        for p in corpus.getComposer('bach')[:10]:
            score = corpus.parse(p)
            for part in score.parts[:1]:
                for el in part.recurse():
                    if isinstance(el, note.Note):
                        notes.append(str(el.pitch))
                    elif isinstance(el, chord.Chord):
                        notes.append(".".join(str(n) for n in el.normalOrder))

    return notes


# ── TRAIN ───────────────────────────
def train(midi_dir=None, epochs=50, seq_length=50, output_dir="model_output"):
    os.makedirs(output_dir, exist_ok=True)

    notes = load_data(midi_dir)

    if len(notes) < seq_length:
        print("❌ Not enough data")
        return

    print(f"Total notes: {len(notes)}")

    unique = sorted(set(notes))
    n_vocab = len(unique)

    note_to_int = {n: i for i, n in enumerate(unique)}
    int_to_note = {i: n for n, i in note_to_int.items()}

    # Save mappings
    with open(f"{output_dir}/mappings.pkl", "wb") as f:
        pickle.dump((note_to_int, int_to_note), f)

    # Prepare sequences
    X, y = [], []
    for i in range(len(notes) - seq_length):
        X.append([note_to_int[n] for n in notes[i:i + seq_length]])
        y.append(note_to_int[notes[i + seq_length]])

    X = np.reshape(X, (len(X), seq_length, 1)) / float(n_vocab)
    y = to_categorical(y)

    # Train/val split
    split = int(len(X) * 0.9)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    print(f"Train samples: {len(X_train)} | Val: {len(X_val)}")

    # Model
    model = Sequential([
        LSTM(256, return_sequences=True, input_shape=(seq_length, 1)),
        Dropout(0.3),
        LSTM(256),
        Dropout(0.3),
        Dense(128, activation='relu'),
        Dense(n_vocab, activation='softmax')
    ])

    model.compile(loss='categorical_crossentropy', optimizer='adam')

    # Callbacks
    checkpoint = ModelCheckpoint(
        f"{output_dir}/best_model.keras",
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    )

    early = EarlyStopping(patience=10, restore_best_weights=True)

    # Train
    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=64,
        callbacks=[checkpoint, early]
    )

    print("✅ Training complete!")


# ── MAIN ────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--midi_dir", default=None)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--seq_length", type=int, default=50)
    parser.add_argument("--output_dir", default="model_output")

    args = parser.parse_args()

    train(args.midi_dir, args.epochs, args.seq_length, args.output_dir)
