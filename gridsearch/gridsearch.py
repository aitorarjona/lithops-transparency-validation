import joblib
import argparse
import bz2

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from pprint import pprint
from time import time


def load_data(mib):
    # Download the dataset at
    # https://www.kaggle.com/bittlingmayer/amazonreviews

    print("Loading Amazon reviews dataset:")
    compressed = bz2.BZ2File('train.ft.txt.bz2')

    X = []
    y = []
    total_size = 0
    for _ in range(3_600_000):
        line = compressed.readline().decode('utf-8')
        X.append(line[11:])
        y.append(int(line[9]) - 1)  # __label__1, __label__2

        total_size += len(line[11:])
        if (total_size / 2**20) > mib:
            break

    print("\t%d reviews" % len(X))
    print("\t%0.2f MiB of data" % (total_size / 2**20))
    return X, y


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backend', default='loky', choices=['loky', 'lithops'])
    parser.add_argument('--n_jobs', default=-1, type=int, help='Limit the total number of processes, -1 for no limit')
    parser.add_argument('--mib', default=10, type=int, help='Use X MB of the dataset')
    parser.add_argument('--refit', default=False, action='store_true', help='Fit the final model with the best configuration and print score')
    args = parser.parse_args()

    X, y = load_data(args.mib)

    n_features = 2**18
    pipeline = Pipeline([
        ('vect', HashingVectorizer(n_features=n_features,
                                   alternate_sign=False)),
        ('clf', SGDClassifier()),
    ])

    parameters = {
        'vect__norm': ('l1', 'l2'),
        'vect__ngram_range': ((1, 1), (1, 2)),
        'clf__alpha': (1e-2, 1e-3, 1e-4, 1e-5),
        'clf__max_iter': (10, 30, 50, 80),
        'clf__penalty': ('l2', 'l1', 'elasticnet')
    }

    if args.backend == 'lithops':
        from sklearn.model_selection import GridSearchCV
        from lithops.util.joblib import register_lithops
        register_lithops()
        grid_search = GridSearchCV(pipeline,
                                   parameters,
                                   error_score='raise',
                                   refit=args.refit,
                                   cv=5,
                                   n_jobs=args.n_jobs)
    elif args.backend == 'loky':
        from sklearn.model_selection import GridSearchCV
        grid_search = GridSearchCV(pipeline,
                                   parameters,
                                   error_score='raise',
                                   refit=args.refit,
                                   cv=5,
                                   n_jobs=args.n_jobs)
    else:
        raise Exception('Unknown backend {}'.format(backend))

    print("pipeline:", [name for name, _ in pipeline.steps])
    print("parameters: ", end='')
    pprint(parameters)

    with joblib.parallel_backend(args.backend):
        print("Performing grid search...")
        t0 = time()
        grid_search.fit(X, y)
        total_time = time() - t0
        print("Done in {}".format(total_time))

    if refit:
        print("Best score: %0.3f" % grid_search.best_score_)
        print("Best parameters set:")
        best_parameters = grid_search.best_estimator_.get_params()
        for param_name in sorted(parameters.keys()):
            print("\t%s: %r" % (param_name, best_parameters[param_name]))

if __name__ == "__main__":
    main()
