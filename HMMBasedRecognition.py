from collections import defaultdict
from pathlib import Path
import pickle
from hmmlearn import hmm
import numpy as np

class HMMBasedRecognition():
    def __init__(self):
        self.models = {}

    @classmethod
    def _extract_sequence(self, X, lengths):
        assert sum(lengths) == len(X), "Invalid dimensions"
        sequences = []
        start = 0
        for l in lengths:
            end = start + l
            sequences.append(X[start:end])
            start = end
        return sequences

    @classmethod
    def _separate_data(self, X, lengths, labels):
        assert len(lengths) == len(labels), "Invalid dimensions"
        sequences = self._extract_sequence(X, lengths)
        grouped = defaultdict(list)
        for seq, label in zip(sequences, labels):
            grouped[label].append(seq)

        separated = {}
        for label, seqs in grouped.items():
            label_lengths = [len(s) for s in seqs]
            label_X = np.concatenate(seqs, axis=0)

            separated[label] = (label_X, label_lengths)

        return separated

    def _fit_separated(self, separated_data: dict):
        self.models = {}

        for label in self.classes_:
            X_l, lengths_l = separated_data[label]

            model = hmm.GaussianHMM(
                n_components=3,
                covariance_type="diag",
                n_iter=200,
                random_state=42,
                # min_covar=1e-4
            )

            self.models[label] = model.fit(X_l, lengths_l)

    def fit_separated(self, separated_data: dict):
        self.classes_ = sorted(separated_data.keys())
        self._fit_separated(separated_data)
        return self

    def fit(self, X, lengths, labels):
        separated_data = self._separate_data(X, lengths, labels)
        self.fit_separated(separated_data)
        return self

    def decision_function(self, X, lengths=None):
        if lengths is None: lengths = [len(X)]
        sequences = self._extract_sequence(X, lengths)
        scores = np.zeros((len(sequences), len(self.classes_)))
        for i, seq in enumerate(sequences):
            for j, label in enumerate(self.classes_):
                scores[i, j] = self.models[label].score(seq)
        return scores

    def predict(self, X, lengths=None):
        scores = self.decision_function(X, lengths)
        indices = scores.argmax(axis=1)
        return [self.classes_[i] for i in indices]

    def save(self, path: str|Path):
        with Path(path).open("wb") as f:
            pickle.dump((self.classes_, self.models), f)

    @classmethod
    def load(cls, path: str|Path):
        self = cls()
        with Path(path).open("rb") as f:
            self.classes_, self.models = pickle.load(f)
        return self


if __name__ == "__main__":
    p = Path("data/train/train.pkl")
    X_train, lengths, labels = pickle.loads(p.read_bytes())

    def train():
        mm = HMMBasedRecognition()
        mm.fit(X_train, lengths, labels)
        mm.save("data/hmm.pkl")

    def evaluate():
        from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
        import matplotlib.pyplot as plt
        mm = HMMBasedRecognition.load(Path("data/hmm.pkl"))
        y_true = labels
        y_pred = mm.predict(X_train, lengths)
        cm = confusion_matrix(y_true, y_pred, labels=mm.classes_)

        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=mm.classes_)
        disp.plot()
        plt.show()

    train()
    evaluate()

