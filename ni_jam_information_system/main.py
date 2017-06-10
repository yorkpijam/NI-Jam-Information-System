from flask import Flask, render_template, request, make_response, redirect

app = Flask(__name__)
#app.run(host='0.0.0.0', port=5000)
from datetime import datetime, timedelta
from ni_jam_information_system.logins import *
import ni_jam_information_system.database as database
import ni_jam_information_system.forms as forms
import ni_jam_information_system.eventbrite_interactions as eventbrite

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.before_request
def check_permission():
    permission_granted, user = check_allowed(db_session, request)
    print(request.url_root)
    if not permission_granted:
        return("")
    else:
        request.logged_in_user = user

@app.route("/test")
def test():
    database.get_attendees_in_workshop(5)


@app.route("/admin/import_attendees_from_eventbrite")
def import_from_eventbrite():
    print("Importing...")
    update_attendees_from_eventbrite(34595287436)
    return("Import finished.")

@app.route('/', methods=['POST', 'GET'])
def index():
    cookie = request.cookies.get('jam_order_id')
    if cookie and len(cookie) == 9 and database.verify_attendee_id(cookie):
        return redirect("workshops")
    form = forms.get_order_ID_form(request.form)
    if request.method == 'POST' and form.validate():
        if database.verify_attendee_id(form.order_id.data):
            resp = make_response(redirect("workshops"))
            resp.set_cookie('jam_order_id', str(form.order_id.data), expires=(datetime.datetime.now() + timedelta(hours=6)))
            resp.set_cookie('jam_id', "34595287436")
            return resp
        else:
            return render_template('index.html', form=form, status="Error, no order with that ID found. Please try again")
    return render_template('index.html', form=form)



@app.route("/admin/add_jam")
def add_jam():
    return render_template("admin/add_jam.html", jams=eventbrite.get_eventbrite_events_name_id(), jams_in_db=database.get_jams_dict())

@app.route("/admin/add_jam/<eventbrite_id>")
def add_jam_id(eventbrite_id):
    eventbrite_jam = eventbrite.get_eventbrite_event_by_id(eventbrite_id)
    database.add_jam(eventbrite_id, eventbrite_jam["name"]["text"], eventbrite_jam["start"]["local"].replace("T", " "))
    return redirect("/admin/add_jam", code=302)

@app.route("/login")
def login():
    return(render_template("login.html"))

@app.route("/check_login", methods=['POST', 'GET'])
def check_login():
    resp = make_response("Added")
    resp.set_cookie("jam_login", "12345")
    return resp

@app.route('/admin/add_workshop_to_catalog', methods=['GET', 'POST'])
def add_workshop_to_catalog():
    form = forms.CreateWorkshopForm(request.form)
    if request.method == 'POST' and form.validate():
        database.add_workshop(form.workshop_title.data, form.workshop_description.data, form.workshop_limit.data, form.workshop_level.data)
        print("Thanks for adding")
        return redirect(('admin/add_workshop'))
    return render_template('admin/new_workshop_form.html', form=form)

@app.route('/admin/add_workshop_to_jam', methods=['GET', 'POST'])
def add_workshop_to_jam():
    form = forms.add_workshop_to_jam(request.form)
    if request.method == 'POST' and form.validate():

        print("Thanks for adding")
    return render_template('admin/add_workshop_to_jam_form.html', form=form, workshop_slots=database.get_time_slots_to_select(34595287436, 0))


@app.route("/workshops")
def display_workshops():
    if database.verify_attendee_id(request.cookies.get('jam_order_id')):
        workshop_attendees = get_attendees_in_order(request.cookies.get("jam_order_id"))
        attendees = []
        if workshop_attendees:
            for attendee in workshop_attendees:
                attendees.append({"name":"{} {} - {}".format(attendee.first_name, attendee.surname, attendee.ticket_type), "id":attendee.attendee_id})
            return render_template("workshops.html", workshop_slots=database.get_time_slots_to_select(34595287436, request.cookies.get('jam_order_id')), jam_attendees=attendees)
        return render_template("workshops.html", workshop_slots=database.get_time_slots_to_select(34595287436, request.cookies.get('jam_order_id')))
    else:
        return redirect("/")


@app.route("/clear_tokens")
def clear_tokens():
    resp = make_response(redirect("/"))
    resp.set_cookie('jam_order_id', "", expires=0)
    resp.set_cookie('jam_login', "", expires=0)
    resp.set_cookie('jam_month', "", expires=0)
    return resp

@app.route("/show_tokens")
def show_tokens():
    order_id = request.cookies.get('jam_order_id')
    jam_login = request.cookies.get('jam_login')
    return("<p> Order ID - {} </p>"
           "<p> Jam Login ID - {} </p>".format(order_id, jam_login))

@app.route("/background_process", methods=['GET', 'POST'])
def background_test():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.add_attendee_to_workshop(34595287436, attendee_id, workshop_id):
        return("")