import os
import pickle
import numpy as np
import tensorflow as tf
import keras
from keras import layers, models
from src.ml.dataset_prep import generate_synthetic_dataset, CATEGORIES
from config.settings import settings

def train_and_save_model():
    os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
    
    texts, labels = generate_synthetic_dataset()
    vocab_size = 5000
    max_len = 150
    
    # 1. Initialize and adapt TextVectorization layer
    vectorize_layer = layers.TextVectorization(
        max_tokens=vocab_size,
        output_mode='int',
        output_sequence_length=max_len
    )
    vectorize_layer.adapt(texts)
    
    # 2. Vectorize text strings prior to training to avoid string tensor dtype issues in Keras 3
    X_train = vectorize_layer(np.array(texts))
    
    # 3. Build Neural Network Model (accepting integer sequences)
    model = models.Sequential([
        layers.Input(shape=(max_len,)),
        layers.Embedding(vocab_size, 32, mask_zero=True),
        layers.GlobalAveragePooling1D(),
        layers.Dense(32, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(len(CATEGORIES), activation='softmax')
    ])
    
    # 4. Wrap vectorizer and model into an end-to-end model for simple inference
    full_model = models.Sequential([
        vectorize_layer,
        model
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # 5. Train on integer-encoded inputs
    model.fit(X_train, labels, epochs=8, batch_size=8, verbose=0)
    
    # 6. Save end-to-end model (accepts raw text directly at prediction time)
    full_model.save(settings.MODEL_PATH)
    
    with open(settings.TOKENIZER_PATH, 'wb') as f:
        pickle.dump({"categories": CATEGORIES}, f)

if __name__ == "__main__":
    train_and_save_model()