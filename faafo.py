
from pathlib import Path
import pickle


p = Path("data/train/train.pkl")
X_train, lengths, labels = pickle.loads(p.read_bytes())

print(labels)