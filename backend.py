import os
import shutil
import sqlite3

from werkzeug.utils import secure_filename

from config import bio_save_path, invitation_link_base
from utils import *

if os.path.exists(bio_save_path):
    USER_DATA_FILES = os.path.join(bio_save_path)

biography_cols = ["BiographyID",
                  "FirstName",
                  "LastName",
                  "Title",
                  "JobTitle",
                  "Email",
                  "Country",
                  "LinkedInPage",
                  "TwitterPage",
                  "FacebookPage",
                  "SocialNetworkPage",
                  "PersonalPhotoName",
                  "IEEEPage",
                  "PersonalWebPage",
                  "Organization",
                  "Region",
                  "GoogleScholarProfile",
                  "Gender",
                  "Keywords",
                  "Biography"
                  ]


class UserBiographySystem:
    def __init__(self, database_path):
        self.database_path = database_path

    def get_db(self):
        return sqlite3.connect(self.database_path)

    def generate_invitation_link(self, event_name):
        even_id = generate_id(key=event_name)

        event_cols = ['EventID', 'EventName']

        try:
            conn = self.get_db()
            events = sqlite_select(conn=conn, table='events', cols=event_cols, conds={'EventName': event_name})
            if len(events) > 0:
                even_id = events[0].get('EventID')
                link = os.path.join(invitation_link_base, even_id)
                return form_response(data={'link': link}, success_msg=f'Event {event_name} already exits')

            affected_rows = sqlite_insert(conn=conn, table='events', rows={
                'EventName': event_name,
                'EventID': even_id
            })
            link = os.path.join(invitation_link_base, even_id)
            if affected_rows:
                return form_response(data={'link': link}, success_msg=f'Event {event_name} has been created')
            return form_response(data={}, error_msg=f'Event {event_name} was not created')

        except Exception as ex:
            error_msg = f'Error generating the service link. Error {ex}'
            return form_response(data=None, error_msg=error_msg)

    def retrieve_biography(self, user_email):

        conn = self.get_db()
        user_email = user_email.lower()
        biography = sqlite_select(conn=conn, table='biography_pending', cols=biography_cols,
                                  conds={'Email': user_email})
        if biography:
            biography = biography[0]
            biography['Keywords'] = str2list(biography['Keywords'])
            return form_response(data=biography, success_msg='success')

        biography = sqlite_select(conn=conn, table='biography_validated', cols=biography_cols,
                                  conds={'Email': user_email})
        if biography:
            biography = biography[0]
            biography['Keywords'] = str2list(biography['Keywords'])
            return form_response(data=biography, success_msg='success')
        else:
            return form_response(data={}, success_msg='success')

    def accept_biography(self, user_bio, user_photo, file_flags):
        conn = self.get_db()
        user_email = user_bio.get('Email', '').lower()
        already_exists_user = sqlite_select(conn,
                                            table='biography_pending',
                                            cols=['BiographyID'],
                                            conds={'Email': f'{user_email}'})
        if already_exists_user:
            biography_id = already_exists_user[0].get('BiographyID')
        else:
            return form_response(data={},
                                 error_msg='email was not found in the pending profiles; maybe already accepted.')

        photo_folder_path = os.path.join(USER_DATA_FILES, biography_id, 'profile_photo')
        personal_photo_name = self.save_user_profile_photo(photo_folder_path, user_photo, file_flags)

        affected_rows_b = sqlite_insert(conn=conn, table='biography_validated', replace_existing=True, rows={
            "FirstName": user_bio.get('FirstName'),
            "LastName": user_bio.get('LastName'),
            "Title": user_bio.get('Title'),
            "JobTitle": user_bio.get('JobTitle'),
            "Email": user_bio.get('Email', '').lower(),
            "Country": user_bio.get('Country'),
            "LinkedInPage": user_bio.get('LinkedInPage'),
            "TwitterPage": user_bio.get('TwitterPage'),
            "FacebookPage": user_bio.get('FacebookPage'),
            "SocialNetworkPage": user_bio.get('SocialNetworkPage'),
            "BiographyID": biography_id,
            "PersonalPhotoName": personal_photo_name,
            "IEEEPage": user_bio.get('IEEEPage'),
            "PersonalWebPage": user_bio.get('PersonalWebPage'),
            "Organization": user_bio.get('Organization'),
            "Region": user_bio.get('Region'),
            "GoogleScholarProfile": user_bio.get('GoogleScholarProfile'),
            "Gender": user_bio.get('Gender'),
            "Keywords": list2str(user_bio.get('Keywords')),
            "Biography": user_bio.get('Biography'),
        })
        sqlite_delete(conn=conn, table='biography_pending', conds={"BiographyID": biography_id})

        if affected_rows_b:
            return form_response(data={}, success_msg='success; inserted')

    @staticmethod
    def save_user_profile_photo(image_save_dir, user_photo, file_flags):

        if user_photo is None:
            # if the photo_file is None --> the server did not send a file --> check what to do next based on the flag
            # if the flag is True --> delete the file
            if bool(file_flags.get('ProfilePhotoFlag', 'False')):
                if os.path.exists(image_save_dir):
                    try:
                        shutil.rmtree(image_save_dir)
                    except OSError as e:
                        print("Error: %s - %s." % (e.filename, e.strerror))
            else:
                # if the flag is False --> keep/ no change
                pass
        else:
            try:
                if not allowed_photo_file(user_photo['filename']):
                    error_msg = f'Not allowed image file type.'
                    return None, error_msg

                # create a folder for user profile photo
                if not os.path.exists(image_save_dir):
                    os.makedirs(image_save_dir, exist_ok=True)

                personal_photo_name = secure_filename(user_photo['filename'])
                filepath = os.path.join(image_save_dir, personal_photo_name)

                # example of how you can save the file
                with open(f"{filepath}", "wb") as f:
                    f.write(user_photo['contents'])
            except:
                return ''
            return personal_photo_name

    def save_biography(self, user_bio, user_photo, event_data, file_flags):
        conn = self.get_db()

        user_email = user_bio['Email'].lower()
        event_id = event_data.get('EventID')

        already_exists_event = sqlite_select(conn=conn, table='events', cols=['EventID'], conds={'EventID': event_id})
        if not already_exists_event:
            return form_response(data={}, error_msg="invalid event ID")

        already_exists_user = sqlite_select(conn,
                                            table='biography_pending',
                                            cols=['BiographyID'],
                                            conds={'Email': f'{user_email}'})
        if already_exists_user:
            biography_id = already_exists_user[0].get('BiographyID')
        else:
            biography_id = generate_id(user_bio['Email'].lower())

        photo_folder_path = os.path.join(USER_DATA_FILES, biography_id, 'profile_photo')
        personal_photo_name = self.save_user_profile_photo(photo_folder_path, user_photo, file_flags)

        affected_rows_b = sqlite_insert(conn=conn, table='biography_pending', replace_existing=True, rows={
            "FirstName": user_bio.get('FirstName'),
            "LastName": user_bio.get('LastName'),
            "Title": user_bio.get('Title'),
            "JobTitle": user_bio.get('JobTitle'),
            "Email": user_bio.get('Email', '').lower(),
            "Country": user_bio.get('Country'),
            "LinkedInPage": user_bio.get('LinkedInPage'),
            "TwitterPage": user_bio.get('TwitterPage'),
            "FacebookPage": user_bio.get('FacebookPage'),
            "SocialNetworkPage": user_bio.get('SocialNetworkPage'),
            "BiographyID": biography_id,
            "PersonalPhotoName": personal_photo_name,
            "IEEEPage": user_bio.get('IEEEPage'),
            "PersonalWebPage": user_bio.get('PersonalWebPage'),
            "Organization": user_bio.get('Organization'),
            "Region": user_bio.get('Region'),
            "GoogleScholarProfile": user_bio.get('GoogleScholarProfile'),
            "Gender": user_bio.get('Gender'),
            "Keywords": list2str(user_bio.get('Keywords')),
            "Biography": user_bio.get('Biography'),
        })
        already_exists_inv = sqlite_select(conn=conn, table='event_biography', cols=['BiographyID'], conds={
            "BiographyID": biography_id,
            "EventID": event_id
        })
        if not already_exists_inv:
            sqlite_insert(conn=conn, table='event_biography', replace_existing=True, rows={
                "BiographyID": biography_id,
                "EventID": event_id
            })
        if affected_rows_b:
            return form_response(data={}, success_msg='success; inserted')
        return form_response(data={}, success_msg='success; not inserted')

    def get_event(self):
        conn = self.get_db()
        events = sqlite_select(conn=conn, table='events', conds=dict(), cols=['EventName', 'EventID'],
                               sort_by='CreateDate')
        return form_response(data=events, success_msg='success')

    def retrieve_bios_by_event(self, event_id, biography_status):
        def get_photo_path(photo_name, biography_id):
            if photo_name:
                return os.path.join(USER_DATA_FILES, biography_id, 'profile_photo', photo_name)
            return ''

        conn = self.get_db()

        if biography_status not in ['pending', 'validated']:
            return form_response(data={},
                                 error_msg='Invalid biography status. It must be either "pending" or "validated."')

        already_exists_event = sqlite_select(conn=conn, table='events', cols=['EventID'], conds={'EventID': event_id})
        if not already_exists_event:
            return form_response(data={}, error_msg="invalid event ID.")

        sql = f"""
        SELECT {', '.join([f'biography_{biography_status}.' + x for x in biography_cols])}
         FROM biography_{biography_status} JOIN  event_biography
        WHERE LOWER(biography_{biography_status}.BiographyID)=LOWER(event_biography.BiographyID) 
        AND LOWER(event_biography.EventID)=LOWER(:EventID)
        ORDER BY biography_{biography_status}.LastName, biography_{biography_status}.FirstName
        """

        result = conn.cursor().execute(sql, {'EventID': event_id})
        biographies = get_list_of_dict(keys=biography_cols, list_of_tuples=result)
        for b in biographies:
            b['PersonalPhotoName'] = get_photo_path(biography_id=b.get('BiographyID'),
                                                    photo_name=b.get('PersonalPhotoName'))
            b['Keywords'] = str2list(b['Keywords'])
        return form_response(data=biographies, success_msg='success')

    def get_itu_keywords(self, query, top_x=10):

        sql = f"""
                SELECT KwText FROM itu_keywords
                WHERE lower(KwText) like ? LIMIT ? 
                """
        conn = self.get_db()
        cur = conn.cursor()
        cur.execute(sql, ("%" + query.lower() + "%", top_x))
        result = cur.fetchall()
        result = [x[0] for x in result]
        return result

    def append_bios_to_event(self, event_id, bio_emails):
        conn = self.get_db()
        already_exists_event = sqlite_select(conn=conn, table='events', cols=['EventID'], conds={'EventID': event_id})
        if not already_exists_event:
            return form_response(data={}, error_msg="invalid event ID")

        pending_validation, inserted_emails, missing_bio = [], [], []
        for bio_email in bio_emails:
            bio_email = bio_email.lower()
            already_exists_user_v = sqlite_select(conn,
                                                  table='biography_validated',
                                                  cols=['BiographyID'],
                                                  conds={'Email': f'{bio_email}'})
            already_exists_user_p = sqlite_select(conn,
                                                  table='biography_pending',
                                                  cols=['BiographyID'],
                                                  conds={'Email': f'{bio_email}'})
            if already_exists_user_v:
                biography_id = already_exists_user_v[0].get('BiographyID')
                sqlite_insert(conn=conn, table='event_biography', rows={
                    'EventID': event_id,
                    'BiographyID': biography_id
                }, replace_existing=True)
                inserted_emails.append(bio_email)

            elif already_exists_user_p:
                pending_validation.append(bio_email)
            else:
                missing_bio.append(bio_email)

        return form_response(data={
            'linked_bios': inserted_emails,
            'pending_validation': pending_validation,
            'missing_bio': missing_bio},
            success_msg='success; if you have items in the pending_validation it means these emails are not validated yet. '
                        'Missing bio means that we do not have the bio in the database. You have to request it.')
