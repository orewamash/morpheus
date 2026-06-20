"""
examples/ml_train.py — Simple scikit-learn training script.
Used for tracing machine learning scripts in Morpheus.
"""

try:
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
except ImportError:
    # Handle if sklearn is not installed yet
    pass


def prepare_data():
    X, y = make_classification(n_samples=100, n_features=10, random_state=42)
    return train_test_split(X, y, test_size=0.2, random_state=42)


def train_model(X_train, y_train):
    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    clf.fit(X_train, y_train)
    return clf


def evaluate_model(clf, X_test, y_test):
    score = clf.score(X_test, y_test)
    return score


def main():
    X_train, X_test, y_train, y_test = prepare_data()
    model = train_model(X_train, y_train)
    accuracy = evaluate_model(model, X_test, y_test)
    print(f"Model trained. Accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    try:
        import sklearn

        _ = sklearn.__version__
        main()
    except ImportError:
        print("scikit-learn is not installed. Skipping ML training execution.")
