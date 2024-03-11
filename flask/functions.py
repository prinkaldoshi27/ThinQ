from utils import *
from constants import *

def process_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_size = frame.shape[1], frame.shape[0]
    gray = np.expand_dims(cv2.bilateralFilter(gray, 5, 10, 10), axis=2)
    gray = np.concatenate([gray, gray, gray], axis=2)

    lms = detector.process(gray).multi_face_landmarks

    if lms:
        landmarks = _get_landmarks(lms)
        t_now = time.perf_counter()
        fps = 30

        Eye_det.show_eye_keypoints(color_frame=frame, landmarks=landmarks, frame_size=frame_size)

        ear = Eye_det.get_EAR(frame=gray, landmarks=landmarks)

        gaze = Eye_det.get_Gaze_Score(frame=gray, landmarks=landmarks, frame_size=frame_size)

        frame_det, roll, pitch, yaw = Head_pose.get_pose(frame=frame, landmarks=landmarks, frame_size=frame_size)

        asleep, looking_away, distracted = Scorer.eval_scores(t_now=time.perf_counter(), ear_score=ear,
                                                              gaze_score=gaze, head_roll=roll, head_pitch=pitch,
                                                              head_yaw=yaw)
        tired, perclos_score = Scorer.get_PERCLOS(t_now, fps, ear)
        if frame_det is not None:
            frame = frame_det

        if ear is not None:
            cv2.putText(frame, "EAR:" + str(round(ear, 3)), (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 1,
                        cv2.LINE_AA)

        if gaze is not None:
            cv2.putText(frame, "Gaze Score:" + str(round(gaze, 3)), (10, 80), cv2.FONT_HERSHEY_PLAIN, 2,
                        (255, 255, 255), 1, cv2.LINE_AA)

        cv2.putText(frame, "PERCLOS:" + str(round(perclos_score, 3)), (10, 110),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 1, cv2.LINE_AA)

        if roll is not None:
            cv2.putText(frame, "roll:" + str(roll.round(1)[0]), (450, 40), cv2.FONT_HERSHEY_PLAIN, 1.5,
                        (255, 0, 255), 1, cv2.LINE_AA)
        if pitch is not None:
            cv2.putText(frame, "pitch:" + str(pitch.round(1)[0]), (450, 70), cv2.FONT_HERSHEY_PLAIN, 1.5,
                        (255, 0, 255), 1, cv2.LINE_AA)
        if yaw is not None:
            cv2.putText(frame, "yaw:" + str(yaw.round(1)[0]), (450, 100), cv2.FONT_HERSHEY_PLAIN, 1.5,
                        (255, 0, 255), 1, cv2.LINE_AA)
            
        if tired:
            cv2.putText(frame, "TIRED!", (10, 280),
                        cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1, cv2.LINE_AA)
            tts("Tired")
        if asleep:
            cv2.putText(frame, "ASLEEP!", (10, 300), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1, cv2.LINE_AA)
            tts("Asleep")
        if looking_away:
            cv2.putText(frame, "LOOKING AWAY!", (10, 320), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1, cv2.LINE_AA)
            tts("Looking Away")
        if distracted:
            cv2.putText(frame, "DISTRACTED!", (10, 340), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1, cv2.LINE_AA)
            tts("Distracted")

    return frame


def _get_landmarks(lms):
    surface = 0
    for lms0 in lms:
        landmarks = [np.array([point.x, point.y, point.z]) for point in lms0.landmark]
        landmarks = np.array(landmarks)

        landmarks[landmarks[:, 0] < 0., 0] = 0.
        landmarks[landmarks[:, 0] > 1., 0] = 1.
        landmarks[landmarks[:, 1] < 0., 1] = 0.
        landmarks[landmarks[:, 1] > 1., 1] = 1.

        dx = landmarks[:, 0].max() - landmarks[:, 0].min()
        dy = landmarks[:, 1].max() - landmarks[:, 1].min()
        new_surface = dx * dy
        if new_surface > surface:
            biggest_face = landmarks

    return biggest_face

def generate_frames():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')