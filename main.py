import json

import uvicorn
from fastapi import FastAPI, Request

from backend import UserBiographySystem

biography = UserBiographySystem(database_path='itu_event_biography_db.db')
app = FastAPI()


@app.get("/biography/generate_invitation")
async def generate_invitation(even_name):
    return biography.generate_invitation_link(event_name=even_name)


@app.get("/biography/retrieve_bio_by_email")
async def retrieve_bio_by_email(user_email: str):
    return biography.retrieve_bio_by_email(user_email=user_email)


@app.get("/biography/retrieve_bio_by_id")
async def retrieve_bio_by_id(bio_id: str):
    return biography.retrieve_bio_by_id(bio_id=bio_id)


@app.get('/biography/get_events')
async def get_event():
    return biography.get_event()


@app.get('/biography/retrieve_bios_by_event')
async def retrieve_bios_by_event(event_id: str, biography_status: str):
    return biography.retrieve_bios_by_event(event_id, biography_status)


@app.post('/biography/append_bio_to_event')
async def append_bio_to_event(request: Request):
    form_data = await request.form()
    event_id = form_data['event_id']
    bio_email = form_data['bio_email']
    return biography.append_bio_to_event(event_id, bio_email)


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

    if 'event_id' in form_data:
        event_id = form_data['event_id']
    else:
        event_id = None

    if 'photo_flag' in form_data:
        photo_flag = eval(form_data['photo_flag'])
    else:
        photo_flag = False

    response = biography.save_biography(user_data, user_photo,
                                        event_id,
                                        photo_flag)
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

    if 'photo_flag' in form_data:
        photo_flag = eval(form_data['photo_flag'])
    else:
        photo_flag = False

    response = biography.accept_biography(user_data, user_photo, photo_flag)
    return response


@app.get('/biography/keywords')
async def query_itu_keywords(q):
    response = biography.get_itu_keywords(q)
    return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8971, log_level="info")
