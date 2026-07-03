import numpy as np
import cv2
import streamlit as st
import mediapipe as mp
from sklearn.svm import SVC

from src.database.db import get_all_students

# -------------------------
# FACE MESH INIT
# -------------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True
)

# -------------------------
# EMBEDDING (STABLE FIX)
# -------------------------
def get_face_embeddings(image_np):

    if image_np is None:
        return []

    rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return []

    lm = results.multi_face_landmarks[0]

    embedding = []

    for point in lm.landmark:
        embedding.extend([point.x, point.y, point.z])

    emb = np.array(embedding, dtype=np.float32)

    return [emb]


# -------------------------
# DATASET BUILDER (ROBUST FIX)
# -------------------------
def _prepare_dataset():

    students = get_all_students()

    X, y = [], []

    for s in students:

        emb = s.get("face_embedding")

        if emb is None:
            continue

        try:
            emb = np.array(emb, dtype=np.float32).flatten()

            if not np.isfinite(emb).all():
                continue

            X.append(emb)
            y.append(s["student_id"])

        except Exception:
            continue

    if len(X) == 0:
        return np.array([]), np.array([])

    # enforce SAME DIMENSION dynamically (IMPORTANT FIX)
    min_dim = min(len(x) for x in X)

    X_fixed = [x[:min_dim] for x in X]

    return np.array(X_fixed), np.array(y)


# -------------------------
# TRAIN MODEL
# -------------------------
@st.cache_resource
def get_trained_model():

    X, y = _prepare_dataset()

    if len(X) < 2:
        return None, None, None

    clf = SVC(kernel="linear", probability=True)
    clf.fit(X, y)

    return clf, X, y


# -------------------------
# TRAIN WRAPPER
# -------------------------
def train_classifier():
    st.cache_resource.clear()
    model = get_trained_model()
    return model[0] is not None if model else False


# -------------------------
# PREDICT ATTENDANCE (FIXED LOGIC)
# -------------------------
def predict_attendance(image_np):

    encodings = get_face_embeddings(image_np)

    detected = {}

    model_data = get_trained_model()

    if model_data is None or model_data[0] is None or len(encodings) == 0:
        return detected, [], 0

    clf, X_train, y_train = model_data

    all_students = list(set(y_train))

    for enc in encodings:

        enc = enc.reshape(1, -1)

        pred = clf.predict(enc)[0]
        proba = max(clf.predict_proba(enc)[0])

        # similarity fallback (IMPORTANT FIX)
        idx = list(y_train).index(pred)
        stored_emb = X_train[idx]

        distance = np.linalg.norm(stored_emb - enc)

        # FINAL DECISION (FIXED)
        if proba > 0.55 or distance < 0.65:
            detected[int(pred)] = True

    return detected, all_students, len(encodings)


# -------------------------
# SAFE ACCESSOR
# -------------------------
def get_face_embedding(image_np):
    return get_face_embeddings(image_np)