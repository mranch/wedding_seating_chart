import flask.cli
import os
import psycopg2
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request
)
from flask_basicauth import BasicAuth
from flask_login import LoginManager
from werkzeug.utils import secure_filename

from forms import GuestForm, GuestEditForm
from model import (
    get_all_guests,
    insert_guest,
    get_guest_by_id,
    get_guests_by_table,
    update_guest,
    delete_guest_by_id
)

PREV_URL = ""


def create_app():
    load_dotenv()
    flask.cli.load_dotenv()

    login_manager = LoginManager()

    app = Flask(__name__)
    app.config["BASIC_AUTH_USERNAME"] = os.environ.get("BASIC_AUTH_USERNAME")
    app.config["BASIC_AUTH_PASSWORD"] = os.environ.get("BASIC_AUTH_PASSWORD")
    app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER")
    basic_auth = BasicAuth(app)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    @app.route("/")
    def welcome():
        all_guests_per_table_seat = {
            table_number: {seat_number: None for seat_number in list(range(1, 12)) + ["--"]}
            for table_number in range(1, 6)
        }
        all_guests_per_table_seat["--"] = []
        for guest in get_all_guests():
            if guest.table_number == "--":
                all_guests_per_table_seat[guest.table_number].append(guest)
            elif guest.seat_number == "--":
                all_guests_per_table_seat[guest.table_number][guest.seat_number] = \
                    all_guests_per_table_seat[guest.table_number][guest.seat_number] or []
                all_guests_per_table_seat[guest.table_number][guest.seat_number].append(guest)
            else:
                all_guests_per_table_seat[guest.table_number][guest.seat_number] = guest
        return render_template("welcome.html", basic_auth=basic_auth, guests=all_guests_per_table_seat)

    @app.route("/admin")
    @basic_auth.required
    def admin():
        return redirect(url_for("welcome"))

    @app.route("/guests")
    def guests_list():
        guests = get_all_guests()
        return render_template("guests.html", guests=guests, basic_auth=basic_auth)

    @app.route("/add", methods=["GET", "POST"])
    @basic_auth.required
    def add_guest():
        form = GuestForm()
        if form.validate_on_submit():
            f = form.profile_image.data
            if f:
                filename = os.path.join("photos", secure_filename(f.filename))
                f.save(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"], filename))
            else:
                filename = os.getenv("DEFAULT_PROFILE_IMAGE_NAME")
            insert_data = form.data
            insert_data["profile_image"] = filename
            try:
                insert_guest(**insert_data)
            except psycopg2.errors.UniqueViolation as e:
                print(e)

            return redirect(url_for('welcome'))
        return render_template("add_guest.html", form=form, basic_auth=basic_auth)

    @app.route("/tables")
    def tables():
        return render_template("tables.html", basic_auth=basic_auth)

    @app.route("/tables/<int:table_id>")
    def table_info(table_id):
        table_guests = get_guests_by_table(table_id)
        return render_template("table_info.html", table_guests=table_guests, table_id=table_id, basic_auth=basic_auth)

    @app.route("/guests/<int:guest_id>")
    def guest_info(guest_id):
        guest = get_guest_by_id(guest_id)
        return render_template("guest_info.html", guest=guest, basic_auth=basic_auth)

    @app.route("/edit/<int:guest_id>", methods=["GET", "POST"])
    @basic_auth.required
    def edit_guest(guest_id):
        global PREV_URL
        guest = get_guest_by_id(guest_id)
        form = GuestEditForm(data=guest.__dict__)

        if request.method == "GET":
            PREV_URL = request.referrer
        else:
            if form.cancel.data:
                return redirect(PREV_URL)

        if form.validate_on_submit():
            f = form.profile_image.data
            if f != guest.profile_image:
                filename = os.path.join("photos", secure_filename(f.filename))
                f.save(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"], filename))
            else:
                filename = guest.profile_image
            update_data = form.data
            update_data["profile_image"] = filename
            update_data['id'] = guest_id
            update_guest(**update_data)

            return redirect(url_for('welcome'))
        return render_template("edit_guest.html", form=form, guest=guest, basic_auth=basic_auth)

    @app.route("/delete/<int:guest_id>", methods=["GET", "POST"])
    @basic_auth.required
    def delete_guest(guest_id):
        guest = get_guest_by_id(guest_id, escape_none=True)
        form = GuestEditForm(data=guest.__dict__)

        global PREV_URL
        if request.method == "GET":
            PREV_URL = request.referrer
        else:
            if form.cancel.data:
                return redirect(PREV_URL)

        if form.validate_on_submit():
            delete_guest_by_id(guest_id)
            return redirect(url_for('welcome'))

        return render_template("delete_guest.html", form=form, guest=guest, basic_auth=basic_auth)

    return app


def start_app():
    app = create_app()
    app.run()


if __name__ == "__main__":
    start_app()
