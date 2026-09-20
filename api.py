from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os
from detect import detect_hits
from writer import transcribe

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Snare transcriber API is running"}


@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only MP3 files are supported right now.")

    input_path = None

    try:
        suffix = "." + file.filename.split(".")[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(await file.read())
            input_path = temp.name

        output_path = input_path.replace(suffix, ".musicxml")

        transcribe(input_path, output_path)

        return FileResponse(
            path=output_path,
            media_type="application/vnd.recordare.musicxml+xml",
            filename="snare_transcription.musicxml"
        )

    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
