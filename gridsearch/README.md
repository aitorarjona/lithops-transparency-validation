# Gridsearch validation

Original work by Scikit-learn and joblib contributors.
- [https://github.com/scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn)
- [https://github.com/joblib/joblib](https://github.com/joblib/joblib).

## Run experiment

Build a Lithops container runtime using `Dockerfile.lambda`. Replace the `workers` attribute under the `lithops` section in [Lithops configuration file](https://github.com/lithops-cloud/lithops/blob/master/config/config_template.yaml) with the desired number of parallel workers.

You may find a copy of the dataset used [here](https://www.kaggle.com/bittlingmayer/amazonreviews).


Execute the experiment using the following command:

```
python gridsearch.py --backend lithops --mib 30 
```
