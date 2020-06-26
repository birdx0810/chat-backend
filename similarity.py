import numpy as np
import spacy

import templates

nlp = spacy.load("zh_core_web_lg")

qa_embeddings = []

for qa_dict in templates.qa_list:
    qa_embeddings.append(nlp(qa_dict["question"]))

def question(text):
    text = text.lower()
    scores = []

    doc = nlp(text)
    # Cosine Similarity
    for embeddings in qa_embeddings:
        scores.append(doc.similarity(embeddings))

    if max(scores) >= 0.3:
        return np.argmax(scores)

    # Keyword matching
    for idx, qa_obj in enumerate(templates.qa_list):
        for keyword in qa_obj["keywords"]:
            if keyword in text:
                return idx

    return None
