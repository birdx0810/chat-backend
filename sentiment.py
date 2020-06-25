import os
import pickle
import traceback
import unicodedata

import jieba

jieba_dict_path = os.path.abspath(
    f"{os.path.abspath(__file__)}/../util/jieba_dict.txt"
)

jieba.initialize()
jieba.set_dictionary(jieba_dict_path)

liwc_word_dict_path = os.path.abspath(
    f"{os.path.abspath(__file__)}/../util/liwc_word_dict.pkl"
)


with open(liwc_word_dict_path, "rb") as f:
    liwc_word_dict = pickle.load(f)

sentiment_codes = {
    "pos": [31, 84],
    "neg": [32, 33, 34, 35, 85, ]
}


def liwc(text: str) -> float:
    """Chinese version LIWC analysis.

    We only consider positive and negative sentiments,
    namely, sentiment_codes["pos"] for positive and
    sentiment_codes["neg"] for negative.

    Returns:
        float: sentiment score range from -1 to +1.
    """

    sentiment_score = 0

    for character in text:
        if character in liwc_word_dict:
            for code in liwc_word_dict[character]:
                if code in sentiment_codes["pos"]:
                    sentiment_score += (1 / len(text))
                if code in sentiment_codes["neg"]:
                    sentiment_score -= (1 / len(text))

    try:
        text = unicodedata.normalize('NFKC', text)
        words = jieba.lcut(text)
    except ValueError as err:
        print(err)
        print(traceback.format_exc())
        words = []

    for word in words:
        if word in liwc_word_dict:
            for code in liwc_word_dict[word]:
                if code in sentiment_codes["pos"]:
                    sentiment_score += (1 / len(words))
                if code in sentiment_codes["neg"]:
                    sentiment_score -= (1 / len(words))

    return min(max(sentiment_score, -1), 1)
