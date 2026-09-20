import librosa
import librosa.display
import matplotlib.pyplot as plt
import cv2
import numpy as np
from sklearn.cluster import KMeans
from pydub import AudioSegment, effects

def detect_hits(input_path):
    # Load audio with pydub
    audio = AudioSegment.from_file(input_path, format="mp3")
    #audio = audio[100:16635]
    audio.export("raw_clip.wav", format="wav")

    # preprocessing
    compressed = effects.compress_dynamic_range(audio, threshold=-2.0, ratio=0.2)
    normalized = effects.normalize(compressed)
    normalized.export("processed.wav", format="wav")

    # Load audio files
    y, sr = librosa.load("processed.wav", sr = None) # For onset detection 
    y_raw, sr2 = librosa.load("raw_clip.wav", sr=None) # For accent detection

    # Detect hits
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=64)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=64, backtrack=False, pre_max = 1, post_max = 1, delta = 0.049)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=64)

    refined_times = refine_hits(y, sr, onset_times)
    refined_times = remove_duplicates(y, sr, refined_times)

    # detect accents
    stengths = get_hit_strengths(y_raw, sr2, refined_times)
    is_accent = detect_accents(stengths)

    # detect bpm
    y = librosa.effects.preemphasis(y)
    #intervals = np.diff(refined_times).reshape(-1, 1)[:40]
    intervals = np.diff(refined_times).reshape(-1, 1)
    # Cluster into 2 groups: main beats vs fast ornaments
    kmeans = KMeans(n_clusters=2, random_state=0).fit(intervals)
    labels = kmeans.labels_
    # Find which cluster has the longest median interval (likely main tempo)
    cluster_medians = [np.median(intervals[labels==i]) for i in range(2)]
    main_interval = max(cluster_medians)

    #bpm = round(60 / (main_interval*2))
    bpm = 90

    return {
        "onset_times": onset_times,
        "refined_times": refined_times,
        "is_accent": is_accent,
        "bpm": bpm,
        "y": y,
        "y_raw": y_raw,
        "sr": sr
    }


def refine_hits(y, sr, onset_times, window_sec=0.005):
    onset_times = np.asarray(onset_times, dtype=float)
    refined_times = []

    radius = int(window_sec * sr)

    for t in onset_times:
        center = int(round(t * sr))

        start = max(0, center - radius)
        end = min(len(y), center + radius + 1)

        segment = y[start:end]

        if len(segment) == 0:
            refined_times.append(t)
            continue

        local_idx = np.argmax(segment)
        refined_sample = start + local_idx
        refined_time = refined_sample / sr

        refined_times.append(refined_time)

    return np.array(refined_times)

def remove_duplicates(y, sr, onset_times, min_spacing_sec=0.035):
    onset_times = np.sort(np.asarray(onset_times, dtype=float))
    min_spacing_samples = int(round(min_spacing_sec * sr))

    i = 0
    while i < len(onset_times) - 1:
        s1 = int(round(onset_times[i] * sr))
        s2 = int(round(onset_times[i + 1] * sr))

        if s2 - s1 < min_spacing_samples:
            if abs(y[s1]) >= abs(y[s2]):
                onset_times = np.delete(onset_times, i + 1)
            else:
                onset_times = np.delete(onset_times, i)
        else:
            i += 1

    return onset_times


def get_hit_strengths(y, sr, onset_times, window_sec=0.05):
    strengths = []
    radius = int(window_sec * sr)

    for t in onset_times:
        center = int(round(t * sr))
        start = max(0, center - radius)
        end = min(len(y), center + radius + 1)

        segment = y[start:end]

        if len(segment) == 0:
            strengths.append(0.0)
            continue

        rms = np.sqrt(np.mean(segment ** 2))
        strengths.append(float(rms))

    return np.array(strengths)


def detect_accents(strengths, neighborhood=5, ratio_threshold=1.35):
    accents = []
    for i, s in enumerate(strengths):
        start = max(0, i - neighborhood)
        end = min(len(strengths), i + neighborhood + 1)

        local = np.concatenate([strengths[start:i], strengths[i+1:end]])

        if len(local) == 0:
            accents.append(False)
            continue

        local_mean = np.mean(local)

        if local_mean == 0:
            accents.append(False)
            continue

        accents.append(s >= ratio_threshold * local_mean)

    return accents

def main():
    data = detect_hits()
    onset_times = data["onset_times"]
    refined_times = data["refined_times"]
    bpm = data["bpm"]
    y = data["y"]
    sr = data["sr"]

    print("\n-------------------------------------------------------------------------------------------------------------------")
    print ("True number of notes:", 118)
    print ("True BPM:", 176)
    #print ("\nIntervals: ",cluster_medians)
    print ("\nEstimated number of notes: ", len(refined_times))
    print("Estimated BPM: ", bpm)

    """t1 = refined_times[29]
    idx = int(round(t1 * sr))
    t2 = onset_times[30]
    idy = int(round(t2 * sr))
    print("ref time:", t1)
    print("og time:", t2)
    print("ref amp:", y[idx])
    print("og amp:", y[idy])"""

    # normal plot
    plt.figure(figsize=(10, 4))
    librosa.display.waveshow(y, sr=sr, alpha=0.6)
    plt.vlines(onset_times, -1, 1, color='r', linestyle='--')
    plt.vlines(refined_times, -1, 1, color='g', linestyle='--')
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.title('Onset Detection')
    plt.show()

    # raw wave plot
    """times = np.arange(len(y)) / sr

    plt.figure(figsize=(10, 4))
    plt.plot(times, y)

    # original onsets (red)
    for t in onset_times:
        plt.axvline(t, color='red', linestyle='--')

    # refined onsets (green)
    for t in refined_times:
        plt.axvline(t, color='green', linestyle='--')

    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.title("Raw Waveform")
    plt.tight_layout()
    plt.show()"""

    """# Load video file
    video_path = 'bloo_clip.mp4'
    cap = cv2.VideoCapture(video_path)

    if cap.isOpened():
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = round(cap.get(cv2.CAP_PROP_FPS))
        print(f"Video loaded. Total frames: {frame_count}, FPS: {fps}")
    else:
        print("Error: Could not open video.")
    cap.release()"""


if __name__ == "__main__":
    main()

