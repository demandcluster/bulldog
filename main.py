# BULLDOG by Ron D. Lite
import os
import io
import nltk
import numpy as np
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.responses import Response
from bark.generation import (
    generate_text_semantic,
    preload_models,
)
from bark.api import semantic_to_waveform
from bark import generate_audio, SAMPLE_RATE
import pydub
import queue
import uuid
import time

# Create a queue to store the requests
audio_queue = queue.Queue()

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["SUNO_USE_SMALL_MODELS"] = "1"
os.environ["SUNO_OFFLOAD_CPU"] = "1"
nltk.download("punkt")

VERSION = "0.1"
SPEAKER = "en_speaker_9"
preload_models()


# launch 🪐
app = FastAPI(
    title="BulldogAPI", description="The Unofficial Bark API", version=VERSION
)


def generate_audio_from_tokens(sentences, speaker=SPEAKER, temp=0.7):
    # Download and load all models
    speaker = "v2/" + speaker
    silence = np.zeros(int(0.25 * SAMPLE_RATE)).astype(
        np.int16
    )  # quarter second of silence
    pieces = []
    for sentence in sentences:
        semantic_tokens = generate_text_semantic(
            sentence,
            history_prompt=speaker,
            temp=temp,
            min_eos_p=0.05,  # this controls how likely the generation is to end
        )
        audio_array = semantic_to_waveform(
            semantic_tokens,
            history_prompt=SPEAKER,
        )

        pieces += [audio_array, silence.copy()]

    audio_concatenated = np.concatenate(pieces)
    return audio_concatenated


def generate_audio_from_script(script, speaker=SPEAKER, temp=0.7):
    speaker = "v2/" + speaker
    script.replace("\n", " ").strip()
    if len(script) > 150:
        # Tokenize the script into sentences
        sentences = nltk.sent_tokenize(script)
        audio_concatenated = generate_audio_from_tokens(sentences, speaker)
    else:
        audio_concatenated = generate_audio(
            script, history_prompt=speaker, text_temp=temp
        )

    # Convert the concatenated audio to MP3 using pydub
    audio_segment = pydub.AudioSegment(
        data=(audio_concatenated * 32767).astype(np.int16).tobytes(),
        sample_width=2,
        frame_rate=SAMPLE_RATE,
        channels=1,
    )
    # audio_segment.export("output.mp3", format="mp3")

    return audio_segment


class Voice(BaseModel):
    prompt: str
    speaker: Union[str, None] = "en_speaker_6"
    temp: Union[float, None] = 0.7
    mp3: Union[bool, None] = False


@app.get("/")
def read_root():
    return {"Bulldog": "Woof! 🐶"}

@app.get("/voices")
def get_voices():
    return [{"voice_id": "en_speaker_1", "name": "Male English 1", "preview_url":"https://dl.suno-models.io/bark/prompts/prompt_audio/en_speaker_0.mp3"}]



@app.post("/text-to-speech")
def post_speech(payload: Voice):
    # Generate a unique ID for the request
    request_id = str(uuid.uuid4())

    # Add the request to the queue
    audio_queue.put((request_id, payload))

    # Check if the request is the first in the queue
    if audio_queue.qsize() == 1:
        # Generate audio for the current request
        _, payload = audio_queue.get()
        result = generate_audio_from_script(
            payload.prompt, payload.speaker, payload.temp
        )

        # Export the audio to a BytesIO object
        audio_file = io.BytesIO()
        result.export(audio_file, format="mp3")
        audio_file.seek(0)
        if payload.mp3 == False:
            return StreamingResponse(audio_file, media_type="audio/mpeg")
        else:
            return Response(
                audio_file.getvalue(),
                media_type="audio/mpeg",
                headers={"Content-Disposition": 'attachment; filename="bulldog.mp3"'},
            )

    # If the request is not the first in the queue, wait for processing
    while True:
        time.sleep(1)
        if not audio_queue.empty() and audio_queue.queue[0][0] == request_id:
            # Generate audio for the current request
            _, payload = audio_queue.get()
            result = generate_audio_from_script(
                payload.prompt, payload.speaker, payload.temp
            )

            # Export the audio to a BytesIO object
            audio_file = io.BytesIO()
            result.export(audio_file, format="mp3")
            audio_file.seek(0)

        if payload.mp3 == False:
            return StreamingResponse(audio_file, media_type="audio/mpeg")
        else:
            return Response(
                audio_file.getvalue(),
                media_type="audio/mpeg",
                headers={"Content-Disposition": 'attachment; filename="bulldog.mp3"'},
            )
