
from utils import make_logger
import torch
from torch.nn.utils.rnn import pad_sequence
import nltk
nltk.download("punkt")
nltk.download("punkt_tab")
from nltk.tokenize import word_tokenize
import json


logger = make_logger("ml-model")


sentiment_model = torch.jit.load("ml-models/sentiment-analysis.pt", map_location="cpu")
logger.info(f"Loaded sentiment model")
verifier_model = torch.jit.load("ml-models/check-fake.pt", map_location="cpu") 
logger.info(f"Loaded verifier model")
vocab = json.load(open("ml-models/vocab.json"))
logger.info(f"Loaded model vocabulary: {len(vocab)} words")


def get_sentiment_scores(text_list: list[str]) -> list[float]:
    return _use_model(sentiment_model, text_list)


def get_verifier_scores(text_list: list[str]) -> list[float]:
    return _use_model(verifier_model, text_list)


def _use_model(model, text_list: list[str]):
    tensors = _batch_tensors(text_list)
    model.eval()
    with torch.no_grad():
        return model(tensors).numpy().tolist()


def _encode_text(text):
    return torch.tensor([
        vocab.get(tk, 1)
        for tk in word_tokenize(text)
    ])


def _batch_tensors(reviews):
    batched_tensors = pad_sequence([
        _encode_text(text)
        for text in reviews
    ], batch_first=True)

    return batched_tensors


if __name__ == "__main__":
    reviews = [
        "i really enjoyed this product, the quality is great",
        "labubu dolls are so bad at their job",
        "i liked the delivery guy, send him again",
        "good frame quality, wished it was cheaper though, great buy"
    ]
    for text, score in zip(reviews, get_sentiment_scores(reviews)):
        print(text, score)
