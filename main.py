import json

import uvicorn
from fastapi import FastAPI, Request

from backend import UserBiographySystem

biography = UserBiographySystem(database_path='itu_event_biography_db.db')
app = FastAPI()


@app.get("/biography/generate_invitation")
async def generate_invitation(even_name):
    return biography.generate_invitation_link(event_name=even_name)


@app.get("/biography/retrieve_biography")
async def retrieve_biography(user_email: str):
    return biography.retrieve_biography(user_email=user_email)


@app.get('/biography/get_events')
async def get_event():
    return biography.get_event()


@app.get('/biography/retrieve_bios_by_event')
async def retrieve_bios_by_event(event_id: str, biography_status: str):
    return biography.retrieve_bios_by_event(event_id, biography_status)


@app.post('/biography/append_bios_to_event')
async def append_bios_to_event(request: Request):
    form_data = await request.form()
    event_id = form_data['event_id']
    bio_emails = form_data['bio_emails']
    return biography.append_bios_to_event(event_id, json.loads(bio_emails).get('emails', []))


@app.post("/biography/save_bio")
async def save_bio(request: Request):
    form_data = await request.form()

    if 'user_data' in form_data:
        user_data = json.loads(form_data['user_data'])
    else:
        user_data = None

    if 'photo_file' in form_data and form_data['photo_file'].filename:
        user_photo = form_data['photo_file']
        contents = await user_photo.read()  # <-- Important!
        fn = user_photo.filename
        user_photo = dict()
        user_photo['filename'] = fn
        user_photo['contents'] = contents
    else:
        user_photo = None

    if 'event_data' in form_data:
        event_data = json.loads(form_data['event_data'])
    else:
        event_data = None

    if 'file_flags' in form_data:
        file_flags = json.loads(form_data['file_flags'])
    else:
        file_flags = {}

    response = biography.save_biography(user_data, user_photo,
                                        event_data,
                                        file_flags)
    return response


@app.post("/biography/accept_bio")
async def accept_bio(request: Request):
    form_data = await request.form()

    if 'user_data' in form_data:
        user_data = json.loads(form_data['user_data'])
    else:
        user_data = None

    if 'photo_file' in form_data and form_data['photo_file'].filename:
        user_photo = form_data['photo_file']
        contents = await user_photo.read()  # <-- Important!
        fn = user_photo.filename
        user_photo = dict()
        user_photo['filename'] = fn
        user_photo['contents'] = contents
    else:
        user_photo = None

    if 'file_flags' in form_data:
        file_flags = json.loads(form_data['file_flags'])
    else:
        file_flags = {}

    response = biography.accept_biography(user_data, user_photo, file_flags)
    return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8971, log_level="info")
