import numpy as np

CATEGORIES = [
    "Artificial Intelligence",
    "Machine Learning",
    "Computer Vision",
    "Natural Language Processing",
    "Robotics",
    "Cyber Security",
    "Cloud Computing"
]

def generate_synthetic_dataset():
    data = [
        ("Deep neural networks, transformers, and large language models drive AI automation.", 0),
        ("Supervised learning algorithms, decision trees, regression models, and gradient boosting.", 1),
        ("Image segmentation, object detection, convolutional neural networks, OpenCV, and YOLO.", 2),
        ("Tokenization, POS tagging, named entity recognition, BERT, and sentiment analysis.", 3),
        ("Kinematics, trajectory planning, actuators, sensors, ROS, and autonomous rovers.", 4),
        ("Penetration testing, cryptography, firewalls, threat detection, and zero-trust security.", 5),
        ("Kubernetes, Docker, AWS EC2, microservices, serverless architecture, and distributed systems.", 6)
    ]
    texts, labels = [], []
    for text, label in data * 20:
        texts.append(text)
        labels.append(label)
        
    return texts, np.array(labels)