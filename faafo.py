

from pathlib import Path
import pickle


p = Path("data/train/train.pkl")
X, lengths, lables = pickle.loads(p.read_bytes())
# p.write_bytes(pickle.dumps((X, lengths, lables)))
print()