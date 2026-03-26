from detect import detect_hits
import numpy as np
from fractions import Fraction

def get_durations(onset_times, bpm):
    beat_duration = 60 / bpm
    durations_sec = np.diff(onset_times)
    durations_beats = durations_sec / beat_duration
    return durations_beats

allowed_lengths = {
    Fraction(4, 1): "whole",
    Fraction(2, 1): "half",
    Fraction(1, 1): "quarter",
    Fraction(3, 2): "dotted quarter",
    Fraction(1, 2): "eighth",
    Fraction(1, 3): "triplet",
    Fraction(1, 4): "16th",
    #Fraction(1, 5): "5-let roll",
    Fraction(1, 6): "16th-triplet",
    #Fraction(1, 8): "32nd",
    Fraction(2, 3): "quarter-note triplet",
    #Fraction(2, 5): "5-let",
    #Fraction(2, 9): "9-let",
}

def snap_duration(d):
    best = min(allowed_lengths, key=lambda x: abs(float(x) - d))
    return best


"""def snap_all(durations):
    return [snap_duration(d) for d in durations]"""

def snap_all(durations): # for debugging
    durations = [snap_duration(d) for d in durations]
    durations[86] = Fraction(1, 6)
    durations[104] = Fraction(1, 4)
    durations[114] = Fraction(1, 4)
    return durationsgit config --global user.email "your_real_email@example.com"


def group_notes(lengths, spans=(Fraction(1,1), Fraction(2,1)), tol=0.05):
    groups = []
    i = 0

    while i < len(lengths):
        found = False

        for span in spans:
            total = Fraction(0,1)
            j = i

            while j < len(lengths):
                total += lengths[j]

                if abs(float(total - span)) < tol:
                    groups.append((i, j+1, span))
                    i = j + 1
                    found = True
                    break

                if total > span:
                    break

                j += 1

            if found:
                break

        if not found:
            groups.append((i, i+1, None))
            i += 1

    return groups


def main():
    data = detect_hits()
    onset_times = data["refined_times"]
    bpm = data["bpm"]

    print("\n-------------------------------------------------------------------------------------------------------------------")
    print ("True number of notes:", 118)
    print ("True BPM:", 176)
    print ("\nEstimated number of notes: ", len(onset_times))
    print("Estimated BPM: ", bpm)

    durations = get_durations(onset_times, bpm)

    print("\nRaw durations (beats):")
    print(np.round(durations, 4))

    snapped = snap_all(durations)

    print("\nSnapped durations:")
    i = 0
    for raw, snapped_val in zip(durations, snapped):
        if snapped_val is None:
            print(f"{raw:.4f} -> None")
        else:
            print(f"{raw:.4f} -> {snapped_val} ({allowed_lengths[snapped_val]}) -> index: {i}")
        i+=1

    """groups = group_notes(snapped)

    print("\nGroups:")
    for g in groups[:10]:
        print(g)"""


if __name__ == "__main__":
    main()