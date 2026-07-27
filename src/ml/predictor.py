import os
import pickle
import numpy as np
import tensorflow as tf
from config.settings import settings

class DocumentClassifier:
    def __init__(self):
        self.model = None
        self.categories = []
        self._load_model()

    def _load_model(self):
        if os.path.exists(settings.MODEL_PATH) and os.path.exists(settings.TOKENIZER_PATH):
            self.model = tf.keras.models.load_model(settings.MODEL_PATH)
            with open(settings.TOKENIZER_PATH, 'rb') as f:
                data = pickle.load(f)
                self.categories = data.get("categories", [])
        else:
            self.model = None

    def predict(self, text: str) -> str:
        if not self.model or not self.categories:
            return "General / Unclassified"
        
        predictions = self.model.predict([text[:1000]], verbose=0)
        class_idx = np.argmax(predictions[0])
        return self.categories[class_idx]