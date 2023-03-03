from flask import Flask, render_template, request, redirect
from redminelib import Redmine
import logging
import datetime
import sys, os
import copy

redmine = ""
model_list = []
version_list = []
version_dict = []
output_logging = 10
app = Flask(__name__)


def start_logging():
    # Enable the logging to console and file
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=output_logging,
                        format='%(asctime)s: [%(levelname)s] %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='redmine_copy.log',
                        filemode='a')

    console = logging.StreamHandler()
    console.setLevel(output_logging)
    formatter = logging.Formatter('%(levelname)-4s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def connect_redmine():
    global redmine
    redmine_version = '3.4.6-stable'
    key = '9e162fa25b0267706cd589c99817b66403a8edfe'
    server = 'http://172.20.0.37'
    redmine = Redmine(server, key=key, version=redmine_version)


def get_model_list():
    global redmine, model_list
    select_model = ["VMG", "DX", "AX", "EX", "WX", "PX", "PE", "EE"]
    # issues = redmine.issue.filter(project_id='Telefonica', tracker_id=1, status_id='*')
    # ticket = redmine.issue.get(126600)
    model_field = redmine.custom_field.get(14)
    for model in model_field.possible_values:
        for selective in select_model:
            if selective in model["value"]:
                model_list.append(model["value"])


def get_version_list():
    global redmine, version_list, version_dict
    # versions = redmine.version.filter(project_id="emea-bu-bug-report")
    # for testing
    versions = redmine.version.filter(project_id="redmine-evaluatoin")
    for version_id in versions:
        if "OPAL" in version_id.name or "opal" in version_id.name:
            version_dict.append({"name": version_id.name, "id": version_id.id})
            version_list.append(version_id.name)


def query_model_test():
    redmine_version = '3.4.6-stable'
    key = '9e162fa25b0267706cd589c99817b66403a8edfe'
    server = 'http://172.20.0.37'
    redmine_server = Redmine(server, key=key, version=redmine_version)

    name_list = []
    select_model = ["VMG", "DX", "AX", "EX", "WX", "PX", "PE", "EE"]
    # issues = redmine.issue.filter(project_id='Telefonica', tracker_id=1, status_id='*')
    # ticket = redmine.issue.get(126600)
    model_field = redmine_server.custom_field.get(14)

    for service in service_profile:
        service.append(service.name)

    for model in model_field.possible_values:
        for selective in select_model:
            if selective in model["value"]:
                name_list.append(model["value"])
    return name_list


def priority_convert(level):
    if level == 6:
        val = 19
    elif level == 5:
        val = 20
    elif level == 4:
        val = 21
    else:
        val = level
    return int(val)


@app.route('/', methods=['GET', 'POST'])
def index_page():
    global redmine, model_list, version_list, version_dict

    redmine = ""
    model_list = []
    version_list = []
    version_dict = []
    start_logging()
    connect_redmine()
    get_model_list()
    get_version_list()
    redmine = ""

    return render_template('index.html', models=model_list, versions=version_list)


@app.route('/submit', methods=['GET','POST'])
def submit():
    result_list = []
    global redmine, model_list, version_list, version_dict
    # if redmine==None or redmine=="":
    # redmine = ""
    # model_list = []
    # version_list = []
    # version_dict = []

    # start_logging()
    connect_redmine()
    # get_model_list()
    # get_version_list()
    # return redirect('/')

    selected_ticket_list = request.form['ticket_list'].replace("\r", "").split("\n")
    selected_model_list = request.form.getlist('model_list')
    selected_target_version = request.form['target_version']
    file_list = []

    selected_version_id = 0
    for version in version_dict:
        if selected_target_version == version["name"]:
            selected_version_id = version["id"]
            break

    for ticket in selected_ticket_list:
        if ticket != "":
            try:
                ticket_content = redmine.issue.get(int(ticket))
            except Exception as e:
                result_list.append("Copy ticket from ID#" + str(ticket_content.id) + "  on model#" + model + "  is failed on new ID#"
                                   + str(issue.id) + " , target:" + selected_target_version + " , reason:" + e)
                continue

            for item in ticket_content.attachments:
                filepath = item.download(savepath=os.getcwd(), filename=item.filename)
                file_list.append({'path': filepath, 'filename': item.filename})

            for model in selected_model_list:
                # print(ticket_content.custom_fields.get(14)['value'][0])
                try:
                    ticket_model_name = ticket_content.custom_fields.get(14)['value'][0]
                except Exception as e:
                    ticket_model_name = ""
                    continue

                if ticket_model_name == model:
                    logging.info("Copy ticket from ID#%s on model#%s is failed, target:%s, reason: exist model", \
                                 ticket_content.id, model, selected_target_version)
                    result_list.append("Copy ticket from ID#" + str(ticket_content.id) + "  on model#" + model + "  is failed, target:" +
                                       selected_target_version + " , reason: exist model")
                    continue
                else:
                    issue = redmine.issue.new()
                    issue.project_id = ticket_content['project']['id']
                    issue.subject = ticket_content['subject']
                    issue.tracker_id = ticket_content['tracker']['id']
                    issue.description = ticket_content['description']
                    issue.status_id = 1
                    issue.fixed_version_id = selected_version_id
                    issue.start_date = ""
                    issue.due_date = ""

                    try:
                        issue.custom_fields = [{'id': 14, 'value': model},
                                               {'id': 19, 'value': "CPE"},
                                               {'id': 6, 'value': ticket_content.custom_fields.get(6)['value']},
                                               {'id': 18, 'value': ticket_content.custom_fields.get(18)['value']},
                                               {'id': 38, 'value': ticket_content.custom_fields.get(38)['value']}]
                    except Exception as e:
                        logging.info(
                            "Copy ticket from ID#%s on model#%s is failed on new ID#%s, target:%s, reason:%s", \
                            ticket_content.id, model, issue.id, selected_target_version, e)
                        result_list.append("Copy ticket from ID#" + str(ticket_content.id) + "  on model#" + model +
                                           "  is failed on new ID#" + str(issue.id) + " , target:" + selected_target_version + " , reason:" + e)
                        continue

                    issue.priority_id = priority_convert(ticket_content['priority']['id'])
                    # report_date = datetime.datetime.strptime(datetime, "%Y/%m/%d").date()
                    # issue.start_date = report_date

                    copy_file_list = copy.deepcopy(file_list)
                    if ticket_content['attachments'] != "N/A":
                        issue.uploads = copy_file_list
                    try:
                        issue.save()

                        relation = redmine.issue_relation.new()
                        relation.issue_id = issue.id
                        relation.issue_to_id = ticket_content.id
                        relation.relation_type = 'copied_from'
                        relation.save()

                        logging.info("Copy ticket from ID#%s on model#%s is created on new ID#%s, target:%s", \
                                     ticket_content.id, model, issue.id, selected_target_version)
                        result_list.append("Copy ticket from ID#" + str(ticket_content.id) + "  on model#" + model + "  is created on new ID#" +
                                           str(issue.id) + " , target:" + selected_target_version)
                    except Exception as e:
                        # print(e)
                        logging.info(
                            "Copy ticket from ID#%s on model#%s is failed on new ID#%s, target:%s, reason:%s", \
                            ticket_content.id, model, issue.id, selected_target_version, e)
                        result_list.append("Copy ticket from ID#" + str(ticket_content.id) + "  on model#" + model +
                                           "  is failed on new ID#" + str(issue.id) + " , target:" + selected_target_version + " , reason:" + e)
                        continue
        # path = os. getcwd()
        for file in file_list:
            os.remove(os.getcwd() + "/" + file['filename'])
    # redmine = ""
    # model_list = []
    # version_list = []
    # version_dict = []
    return render_template("success.html", results=result_list)


if __name__ == '__main__':
    app.run()
