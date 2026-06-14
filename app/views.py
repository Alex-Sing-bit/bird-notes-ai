import datetime
from datetime import datetime
import json
from urllib.parse import urlparse, urljoin

import flask
import requests
from flask import render_template, request, flash, redirect, url_for, Blueprint
from flask_login import login_user, current_user, login_required, logout_user

from app import db, client
from app.models import User, Note, Bird
from config import GOOGLE_DISCOVERY_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from app.forms import MakeNoteForm, NoteForm

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    form_obs = MakeNoteForm(request.form)
    form_note = NoteForm(request.form)
    if request.method == 'POST':
        if 'note_submit' in request.form and form_note.validate_on_submit():
            if current_user.is_authenticated:
                try:
                    continue_flag = True
                    note = Note()
                    note.user_id = current_user.id
                    note.date_created = datetime.today()
                    note.date = form_note.date.data
                    note.time = form_note.time.data
                    note.geo = form_note.geo.data.strip()

                    birds_list = form_note.birds.data.strip().split(',')
                    # TODO: поиск независимо от размера букв
                    for bird_name in birds_list:
                        bird = Bird.query.filter_by(name=bird_name).first()

                        if bird:
                            note.birds.append(bird)
                        else:
                            continue_flag = False

                    if continue_flag:
                        db.session.add(note)
                        db.session.commit()
                except Exception as e:
                    flash(e)
                    flash(form_obs.note_text.data)
                    flash(form_note.birds.data)
            else:
                return redirect(url_for('main.login'))

        elif 'obs_submit' in request.form and form_obs.validate_on_submit():
            form_note.birds.data = form_obs.note_text.data
            flash(f'Наблюдение скопировано в заметку: {form_obs.note_text.data}')

    if current_user.is_authenticated:
        return render_template("index.html",
                               title='TextBirds',
                               user={'nickname': current_user.nickname},
                               form_obs=form_obs,
                               form_note=form_note)
    else:
        return render_template("index.html",
                               title='TextBirds',
                               user=None,
                               form_obs=form_obs,
                               form_note=form_note)


@bp.route('/login', methods = ['GET', 'POST'])
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@bp.route("/login/callback")
def callback():
    code = request.args.get("code")

    if not code:
        flash("Authorization code not received from Google", "error")
        return redirect(url_for("main.index"))

    try:
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
        )

        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            users_name = userinfo_response.json()["given_name"]
        else:
            return "User email not available or not verified by Google.", 400

        user = User.query.get(unique_id)
        if not user:
            user = User(id=unique_id, nickname=users_name, email=users_email)
            db.session.add(user)
            db.session.commit()
            flash(f"Welcome {users_name}! Your account has been created.", "success")

        login_user(user, remember=True)
        next_page = flask.request.args.get('next')
        if not url_has_allowed_host_and_scheme(next_page):
            next_page = None
        flash(f"Successfully logged in as {users_name}!", "success")
        return redirect(next_page or url_for("main.index"))

    except Exception as e:
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("main.index"))

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@bp.route('/notes')
@login_required
def notes():
    if not current_user.is_authenticated:
        return render_template("notes.html",
                               title='TextBirds',
                               user=None,
                               notes=None)
    else:
        user_notes = Note.query.filter_by(user_id=current_user.id).all()

        '''for user_note in user_notes:
            bird_ids = user_note.birds
            bird_names = []
            for bird_id in bird_ids:
                bird_names.append(Bird.query.filter_by(name=bird_id).name)
            user_note.birds = bird_names'''

        return render_template("notes.html",
                           title='TextBirds',
                           user=current_user,
                           notes=user_notes)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

def url_has_allowed_host_and_scheme(target):
    if not target:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc