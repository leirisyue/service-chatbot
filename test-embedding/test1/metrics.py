import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def retrieval_accuracy(embeddings):
    X = np.array(embeddings)
    sims = cosine_similarity(X, X)

    correct = 0
    for i in range(len(X)):
        sims[i][i] = -1
        if np.argmax(sims[i]) == i:
            correct += 1

    return correct / len(X)
