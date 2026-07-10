import cv2
import numpy as np
import streamlit as st
import mediapipe as mp
from sklearn.svm import SVC
from src.database.db import get_all_students


# ---------------------------------------
# FACE MESH
# ---------------------------------------

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True
)


# ---------------------------------------
# EMBEDDING
# ---------------------------------------

def get_face_embeddings(image_np):

    if image_np is None:
        return []

    rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return []

    lm = results.multi_face_landmarks[0]

    emb = []

    nose = lm.landmark[1]

    for p in lm.landmark:

        emb.extend([
            p.x - nose.x,
            p.y - nose.y,
            p.z - nose.z
        ])

    emb = np.asarray(emb, dtype=np.float32)

    emb /= np.linalg.norm(emb)

    return [emb]


# ---------------------------------------
# BUILD DATASET
# ---------------------------------------

def prepare_dataset():

    students = get_all_students()

    X = []
    y = []

    for s in students:

        emb = s.get("face_embedding")

        if emb is None:
            continue

        emb = np.asarray(emb, dtype=np.float32).flatten()

        if len(emb) != 1434:
            continue

        if not np.isfinite(emb).all():
            continue

        emb /= np.linalg.norm(emb)

        X.append(emb)
        y.append(int(s["student_id"]))

    return np.array(X), np.array(y)


# ---------------------------------------
# TRAIN
# ---------------------------------------

@st.cache_resource
def get_trained_model():

    X, y = prepare_dataset()

    # No students
    if len(X) == 0:
        return None

    # Less than 2 different students
    if len(set(y)) < 2:

        return {
            "clf": None,
            "X": X,
            "y": y
        }

    clf = SVC(
        kernel="linear",
        probability=True,
        class_weight="balanced"
    )

    clf.fit(X, y)

    return {
        "clf": clf,
        "X": X,
        "y": y
    }
    


def train_classifier():

    st.cache_resource.clear()

    return True

# ---------------------------------------
# PREDICTION
# ---------------------------------------

def predict_attendance(image_np):

    encodings = get_face_embeddings(image_np)

    detected = {}

    model = get_trained_model()

    if model is None:
        return detected, [], len(encodings)

    clf = model["clf"]
    X = model["X"]
    y = model["y"]

    if clf is None:
        detected[int(y[0])] = True
        return detected, list(set(y)), len(encodings)

    all_students = sorted(list(set(y)))

    for emb in encodings:

        emb = emb.reshape(1, -1)

        prediction = int(clf.predict(emb)[0])

        probability = float(np.max(clf.predict_proba(emb)))

        indices = np.where(y == prediction)[0]

        distances = []

        for idx in indices:

            dist = np.linalg.norm(
                X[idx] - emb[0]
            )

            distances.append(dist)

        best_distance = min(distances)

        print(
            "Prediction:",
            prediction,
            "Probability:",
            probability,
            "Distance:",
            best_distance
        )

        if probability >= 0.45 and best_distance <= 0.42:
            detected[prediction] = True

    return detected, all_students, len(encodings)


# ---------------------------------------
# COMPATIBILITY
# ---------------------------------------

def get_face_embedding(image_np):
    return get_face_embeddings(image_np)