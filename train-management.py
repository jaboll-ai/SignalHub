# import cv2

# cam = cv2.VideoCapture(2)

# frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
# frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
# print(frame_width, frame_height)
# while True:
#     ret, frame = cam.read()
#     if not ret: continue
#     cv2.imshow('Camera', frame)
#     if cv2.waitKey(1) == ord('q'):
#         break

# # Release the capture and writer objects
# cam.release()
# cv2.destroyAllWindows()


from pathlib import Path
import pickle
import random
import numpy as np
from HMMBasedRecognition import HMMBasedRecognition

def load_train(p: Path):
    X_train, lengths, labels = pickle.loads(p.read_bytes())
    sep = HMMBasedRecognition._separate_data(X_train, lengths, labels)
    return sep

def keep(p: Path, label: list[str]):
    sep = load_train(p)
    print(f"Before: {list(sep.keys())}")
    return rebuild(label, sep)

def remove(p: Path, label: list[str]):
    sep = load_train(p)
    print(f"Before: {list(sep.keys())}")
    for k in label:
        sep.pop(k, None)
    return rebuild(sep.keys(), sep)

def rebuild(label: list[str], sep):
    X_new = []
    labels_new = []
    lengths_new = []
    for k in label:
        X, l = sep[k]
        X_new.append(X)
        labels_new += [k] * len(l)
        lengths_new += l
    print(f"After: {list(label)}")
    X_new = np.vstack(X_new)
    assert len(lengths_new) == len(labels_new), "Invalid dimensions"
    assert sum(lengths_new) == len(X_new), f"Invalid dimensions {sum(lengths_new), len(X_new)}"
    return X_new, lengths_new, labels_new

def compare(p: Path, label: list[str]):
    sep = load_train(p)
    for k in label:
        lst_X = HMMBasedRecognition._extract_sequence(*sep[k])
        print("-"*20)
        print(k)
        print(random.choice(lst_X))




if __name__ == "__main__":
    p = Path("data/train/train.pkl")
    pog = Path("data/train/isok.pkl")
    np.set_printoptions(suppress=True)
    # X_train, lengths, labels = pickle.loads(p.read_bytes())
    # X, l, l_ = pickle.loads(pog.read_bytes())
    # X_train[:,-1] = X_train[:,-1] / 10_000
    # X_train[:,-2] = X_train[:,-2] / 100
    # print(X[:,-1])
    # print(X_train[:,-1])
    # print(X.shape, X_train.shape)
    # p.write_bytes(pickle.dumps((X_train, lengths, labels)))
    # p.write_bytes(pickle.dumps(remove(p, ["B"])))
    # compare(p, ["E", "F"])
