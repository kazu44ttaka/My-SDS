import cv2
import insightface
import numpy as np
from numpy.linalg import norm
import time

# モデル読み込み（検出＋識別）
model = insightface.app.FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider"])
model.prepare(ctx_id=0)

# 事前登録：顔データ（名前＋ベクトル）
known_faces = {
    "Alice": None,
    "Bob": None,
}

# 1回だけ登録（最初のフレームなどで）
def register_face(frame, name):
    faces = model.get(frame)
    if faces:
        known_faces[name] = faces[0].embedding / norm(faces[0].embedding)

def identify_face(frame):
    faces = model.get(frame)
    if not faces:
        return frame
    for face in faces:
        emb = face.embedding / norm(face.embedding)
        # 類似度比較（コサイン類似度）
        results = {name: np.dot(emb, ref) for name, ref in known_faces.items() if ref is not None}
        name = max(results, key=results.get) if results else "Unknown"
        x, y, w, h = map(int, face.bbox)
        cv2.rectangle(frame, (x, y), (w, h), (0, 255, 0), 2)
        cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    return frame

# カメラ
cap = cv2.VideoCapture(0)
print("Press 'r' to register Alice, 't' for Bob, 'q' to quit")

prev_time = time.time()
while True:
    ret, frame = cap.read()
    if not ret:
        break

    key = cv2.waitKey(1)
    if key == ord('r'):
        register_face(frame, "Alice")
        print("✅ Registered Alice")
    elif key == ord('t'):
        register_face(frame, "Bob")
        print("✅ Registered Bob")
    elif key == ord('q'):
        break

    frame = identify_face(frame)
    cv2.imshow("Face ID", frame)

cap.release()
cv2.destroyAllWindows()
