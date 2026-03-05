import pickle
from pathlib import Path
import numpy as np

f = Path("record/test.pickle")
assert f.exists(), "Record file does not exist"
t = Path("data/train/train.pkl")
if not t.parent.exists():
    t.parent.mkdir(exist_ok=True, parents=True)
if t.exists():
    train, lengths, labels = pickle.loads(t.read_bytes())
    t.with_suffix(".old").unlink(missing_ok=True)
else:
    print("Creating new train file")
    train= np.empty((0, 5))
    lengths = []
    labels = []
assert len(lengths) == len(labels) and sum(lengths) == len(train), "Invalid dimensions"
raw=pickle.loads(f.read_bytes())
data = []

while raw["preprocessor"]:
    sub = []
    while raw["preprocessor"]:
        d = raw["preprocessor"].pop(0)
        if d is None or d.get("preprocessor") is None: d = []
        if len(d) > 0: break
    if len(d) > 0:
        sub.append(d)
    lost = 0
    while raw["preprocessor"]:
        d = raw["preprocessor"].pop(0)
        if d is None or d.get("preprocessor") is None: d = []
        if len(d) <= 0:
            lost += 1
            if lost > 20: break
        else:
            sub.append(d)
    if len(sub) > 10:
        data.append(sub)

normalized = [[p["preprocessor"] for p in d] for d in data]
current_lengths = [len(d) for d in normalized]
assert int(input("How many times did you do it? >> ")) == len(current_lengths), f"Invalid length i saw {len(current_lengths)}"
current_labels = [input("Label: >> ")] * len(current_lengths)
current_train = np.vstack(normalized)

train=np.vstack((train, current_train))
lengths.extend(current_lengths)
labels.extend(current_labels)
if t.exists():
    t.rename(t.with_suffix(".old"))
t.write_bytes(pickle.dumps((train, lengths, labels)))

