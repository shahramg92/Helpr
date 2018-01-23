import os
import tornado.log
import tornado.ioloop
import tornado.web
import requests


from jinja2 import Environment, PackageLoader, select_autoescape
from models import *

PORT = int(os.environ.get('PORT', '8888'))
# Retrieve path where HTML lives
ENV = Environment(
    loader=PackageLoader('project', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


# Retrieve all details for a specific request
def get_status_info(req_id):
    # get details for the request
    requestdata = []
    for requestinfo in Request.select().where(Request.id == req_id).dicts():
        people_needed = requestinfo['people_needed']

    # get details for all of the volunteeers
    volunteerdata = []
    for assignmentinfo in Assignment.select().where(Assignment.request_id == req_id).dicts():
        vol_id = assignmentinfo['volunteer']
        volunteers_assigned = 0
        for volunteerinfo in Volunteer.select().where(Volunteer.id == vol_id).order_by(Volunteer.id).dicts():
            volunteers_assigned = volunteerinfo['volunteers']
            people_needed = people_needed - volunteers_assigned
            volunteerdata.append(volunteerinfo)

    # update request info with number of people needed after processing all of the volunteers
    if people_needed < 0:
        people_needed = 0
    else:
        pass
    requestinfo['people_needed'] = people_needed
    requestdata.append(requestinfo)
    return requestdata, volunteerdata


class TemplateHandler(tornado.web.RequestHandler):
  def render_template (self, tpl, context):
    template = ENV.get_template(tpl)
    self.write(template.render(**context))


# Home Page Handler
class MainHandler(TemplateHandler):
    def get (self):
        mapdata = []
        for helprequest in Request.select().where(Request.open_request == True).dicts():
            # get the request id for use in querying the number of volunteers assigned to a request
            helprequest_id = helprequest['id']

            # query the database to get the number of volunteers assigned to a request
            sum_volunteers = DB.execute_sql('SELECT SUM(volunteers) FROM  Assignment JOIN Volunteer ON Assignment.volunteer_id = volunteer.id WHERE request_id = %s', (helprequest_id,)).fetchone()

            # set the number of volunteers assigned based on the query results
            if sum_volunteers[0] is not None:
                volunteers_assigned = sum_volunteers[0]
            else:
                volunteers_assigned = 0

            # calculate the number of people needed based on the request and the number of volunteers assigned
            people_needed = helprequest['people_needed']
            people_needed = people_needed - volunteers_assigned

            # If the number of people needed is less than or equal to zero then we're at full capacity
            if people_needed <= 0:
                people_needed = 0
                helprequest['full_capacity'] = True
            else:
                helprequest['full_capacity'] = False

            # update the dictionary with number of people needed
            helprequest['people_needed'] = people_needed

            # load the array with data from each row in the Request table for use in the UI
            mapdata.append(helprequest)

        self.set_header('Cache-Control',
        'no-store, no-cache, must-revalidate, max-age=0')
        template = ENV.get_template('index.html')
        self.write(template.render({'mapdata':mapdata}))


class RequestFormHandler(TemplateHandler):
    def get(self):
        self.set_header('Cache-Control',
         'no-store, no-cache, must-revalidate, max-age=0')
        self.render_template("request_form.html", {})

    def post(self):
        # Process form data

        first_name = self.get_body_argument('first_name')
        last_name = self.get_body_argument('last_name')
        address = self.get_body_argument('address1')
        city = self.get_body_argument('city')
        state = self.get_body_argument('state')
        postalcode = self.get_body_argument('postalcode')
        phone = self.get_body_argument('phone')
        email = self.get_body_argument('email')
        description = self.get_body_argument('description')
        people = self.get_body_argument('people_needed')
        truck = self.get_body_argument('truck_needed')

        address1 = (address + ', ' + city + ', ' + state)

        GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'

        params = {
            'address': address1,
            'key': 'AIzaSyDICJB-ecPiyM2GtrlleYblXt318jz71So'
        }

        # Do the request and get the response data
        req = requests.get(GOOGLE_MAPS_API_URL, params=params)
        res = req.json()

        # Use the first result
        result = res['results'][0]

        geodata = dict()
        geodata['lat'] = result['geometry']['location']['lat']
        geodata['lng'] = result['geometry']['location']['lng']
        geodata['address'] = result['formatted_address']
        lat = result['geometry']['location']['lat']
        lng = result['geometry']['location']['lng']

        row = Request.create(
            first_name = first_name,
            last_name = last_name,
            address1 = address,
            city = city,
            state = state,
            postalcode = postalcode,
            latitude = lat,
            longitude = lng,
            phone = phone,
            email = email,
            description = description,
            people_needed = people,
            truck_needed = truck
        )

        # Get details for the request so it can be displayed on the status page
        req_id = row
        requestdata, volunteerdata = get_status_info(req_id)

        self.set_header('Cache-Control',
         'no-store, no-cache, must-revalidate, max-age=0')

        template = ENV.get_template('status.html')
        self.write(template.render({'requestdata': requestdata, 'volunteerdata': volunteerdata}))


class VolunteerFormHandler(TemplateHandler):
    def get(self):
        self.set_header('Cache-Control',
         'no-store, no-cache, must-revalidate, max-age=0')
        self.render_template("volunteer_form.html", {})

    def post(self):
        # Process form data
        form_request_id = self.get_body_argument('id')
        form_first_name = self.get_body_argument('first_name')
        form_last_name = self.get_body_argument('last_name')
        form_phone = self.get_body_argument('phone')
        form_email = self.get_body_argument('email')
        form_volunteers = self.get_body_argument('volunteers')
        form_has_truck = self.get_body_argument('has_truck')
        v = Volunteer.create(
            first_name = form_first_name,
            last_name = form_last_name,
            phone = form_phone,
            email = form_email,
            volunteers = form_volunteers,
            has_truck = form_has_truck
        )
        a = Assignment.create(
            # Developer note - regarding the line of code below:  When referencing an object that was used to insert a row into a table (in this case 'v' was used to insert a row into the Volunteer table) it automatically knows to use the id field from that object when assigning it to another variable (in this case variable 'volunteer' will contain the value of the id field for the row that was written to the Volunteer table).  Actually, the object 'v' will contain ALL fields and their corresponding value.  An equivalent to the code below would have been 'volunteer = v.id' - this would have worked just as well.  Also, you can reference all fields this way (e.g. v.first_name, v.last_name, etc.)
            volunteer = v,
            request = form_request_id
        )

        # Get details for the request so it can be displayed on the status page
        req_id = form_request_id
        requestdata, volunteerdata = get_status_info(req_id)

        self.set_header('Cache-Control',
         'no-store, no-cache, must-revalidate, max-age=0')

        template = ENV.get_template('status.html')
        self.write(template.render({'requestdata': requestdata, 'volunteerdata': volunteerdata}))


class StatusFormHandler(TemplateHandler):
    def post(self):

        # Get details for the request so it can be displayed on the status page
        req_id = self.get_body_argument('id')
        requestdata, volunteerdata = get_status_info(req_id)

        self.set_header('Cache-Control',
         'no-store, no-cache, must-revalidate, max-age=0')

        template = ENV.get_template('status.html')
        self.write(template.render({'requestdata': requestdata, 'volunteerdata': volunteerdata}))


# Make the Web Applicaton using Tornado
def make_app():
  return tornado.web.Application([
    (r"/", MainHandler),
    (r"/request_form", RequestFormHandler),
    (r"/volunteer_form", VolunteerFormHandler),
    (r"/status", StatusFormHandler),
    (r"/rstatus", RequestFormHandler),
    (r"/vstatus", VolunteerFormHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': 'static'}),
    ], autoreload=True)

# Main
if __name__ == "__main__":
    tornado.log.enable_pretty_logging()
    app = make_app()
    app.listen(PORT, print('Hosting at 8888'))
    tornado.ioloop.IOLoop.current().start()
