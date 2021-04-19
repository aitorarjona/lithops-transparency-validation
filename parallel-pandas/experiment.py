import pandas as pd
import time
from pandarallel import pandarallel
import numpy as np
import math
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import re
from textblob import TextBlob
import sys
import csv

if __name__ == '__main__':
    workers = int(sys.argv[1])
    print(workers)

    pandarallel.initialize(use_memory_fs=False, nb_workers=workers)

    # Download the dataset from https://www.kaggle.com/kazanova/sentiment140
    df = pd.read_csv('tweeter.csv', header=None, sep=',', names=['target', 'id', 'date', 'flag', 'user', 'text'], engine='python')
    print(df.info)
    serie = df['text']


    def preprocess_tweet(text):
        text = re.sub('@[A-Za-z\d]+', '', text)  # Removing @mentions
        text = re.sub('#[A-Za-z\d]+', '', text)  # Removing hashtag
        text = re.sub('https?:\/\/\S+', '', text)  # Removing hyperlink
        # Removing emojis
        text = re.sub(
            '[\u2600-\u26FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '',
            text)
        return text

    def discretize_sentiment(text):
        text = preprocess_tweet(text)
        polarity = TextBlob(text).sentiment.polarity
        if polarity < 0:
            return 'negative'
        if polarity == 0:
            return 'neutral'
        if polarity > 0:
            return 'positive'

    t1 = time.time()
    polarity = serie.parallel_apply(discretize_sentiment)
    t2 = time.time()

    print(f'{t2-t1} seconds')

