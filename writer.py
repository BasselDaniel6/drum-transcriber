import time
import warnings
warnings.filterwarnings("ignore")

from music21 import stream, meter, note, clef, instrument, tempo, metadata, articulations
from fractions import Fraction

from detect import detect_hits
from rhythm import get_durations, snap_all


def make_note(length, is_accent = False):
    n = note.Unpitched()
    n.displayStep = "C"
    n.displayOctave = 5
    n.quarterLength = float(length)

    if is_accent:
        n.articulations.append(articulations.Accent())

    return n

def transcribe(input_file, output_file, bpm=None):
    data = detect_hits(input_file, bpm=bpm)
    onset_times = data["refined_times"]
    bpm = data["bpm"]
    is_accent = data["is_accent"]

    durations = get_durations(onset_times, bpm)
    snapped = snap_all(durations)

    """#fix missing last note
    if len(snapped) > 0:
        snapped = list(snapped) + [snapped[-1]]
    else:
        snapped = [Fraction(1, 4)]"""

    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = "Snare Transcription"

    part = stream.Part()
    part.id = 'snare'
    part.insert(0, clef.PercussionClef())
    part.insert(0, instrument.UnpitchedPercussion())
    part.insert(0, meter.TimeSignature("3/4"))
    part.insert(0, tempo.MetronomeMark(number=int(bpm)))

    i = 0
    for length in snapped:
        part.append(make_note(length, is_accent[i]))
        i+=1

    part = part.makeMeasures()
    part = part.makeNotation()

    score.append(part)
    score.write("musicxml", fp=output_file)

    #print("Done. Open snare_output.musicxml in MuseScore.")
    print(f"Wrote {output_file}")

    return {
        "bpm": bpm,
        "notes": len(snapped),
        "output_file": output_file
    }
    

def main():
    start = time.time()
    transcribe(
        input_file="bloo_clip_cut.mp3",
        output_file="snare_output.musicxml"
    )
    end = time.time()
    latency = end - start
    print("latency", latency)

if __name__ == "__main__":
    main()
