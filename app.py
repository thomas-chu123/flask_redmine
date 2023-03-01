from flask import Flask, render_template, request, redirect
from redminelib import Redmine
import logging
import datetime
import sys, os
import copy

output_logging = 20
app = Flask(__name__)

class Redmine_Copy():
    def __init__(self, top=None):
        super().__init__()

        self.redmine = ""
        self.model_list = []
        self.start_logging()
        self.redmine = self.redmine_connect()

    def query_version(self):
        version_list = []
        versions = self.redmine.version.filter(project_id="emea-bu-bug-report")
        # for testing
        # versions = self.redmine.version.filter(project_id="redmine-evaluatoin")
        for version_id in versions:
            if "OPAL" in version_id.name or "opal" in version_id.name:
                version_list.append({"name": version_id.name, "id": version_id.id})
        return version_list

    def redmine_connect(self):
        # Redmine setting
        redmine_version = '3.4.6-stable'
        key = '9e162fa25b0267706cd589c99817b66403a8edfe'
        server = 'http://172.20.0.37'
        self.redmine = Redmine(server, key=key, version=redmine_version)
        return

    def query_model(self):
        name_list = []
        select_model = ["VMG", "DX", "AX", "EX", "WX", "PX", "PE", "EE"]
        # issues = redmine.issue.filter(project_id='Telefonica', tracker_id=1, status_id='*')
        # ticket = redmine.issue.get(126600)
        model_field = self.redmine.custom_field.get(14)
        for model in model_field.possible_values:
            for selective in select_model:
                if selective in model["value"]:
                    name_list.append(model["value"])
        return name_list

    def query_model_test(self):
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

    def start_copy(self):
        model_list = []

        tickets = self.TicketList.get("1.0", tk.END)
        ticket_list = tickets.split("\n")
        ticket_list = list(filter(None, ticket_list))

        for i in self.ModelList.curselection():
            model_list.append(self.ModelList.get(i))

        target_version_name = self.TargetVersion.get()
        version_id = 0
        for version in self.version_dict:
            if target_version_name == version["name"]:
                version_id = version["id"]
                break

        # print (tickets)
        for ticket in ticket_list:
            if ticket != "":
                ticket_content = self.redmine.issue.get(int(ticket))
                file_list = []

                for item in ticket_content.attachments:
                    filepath = item.download(savepath=os.getcwd(), filename=item.filename)
                    file_list.append({'path': filepath, 'filename': item.filename})

                for model in model_list:
                    # print(ticket_content.custom_fields.get(14)['value'][0])
                    if ticket_content.custom_fields.get(14)['value'][0] == model:
                        logging.info("Copy ticket from ID#%s on model#%s is failed, target:%s, reason: exist model", \
                                     ticket_content.id, model, target_version_name)
                        continue
                    else:
                        issue = self.redmine.issue.new()
                        issue.project_id = ticket_content['project']['id']
                        issue.subject = ticket_content['subject']
                        issue.tracker_id = ticket_content['tracker_id']
                        issue.description = ticket_content['description']
                        issue.status_id = 1
                        issue.fixed_version_id = version_id

                        try:
                            issue.custom_fields = [{'id': 14, 'value': model},
                                                   {'id': 5, 'value': ticket_content.custom_fields.get(5)['value']},
                                                   {'id': 36, 'value': ticket_content.custom_fields.get(36)['value']},
                                                   {'id': 21, 'value': ticket_content.custom_fields.get(21)['value']},
                                                   {'id': 19, 'value': "CPE"},
                                                   {'id': 6, 'value': ticket_content.custom_fields.get(6)['value']},
                                                   {'id': 34, 'value': ticket_content.custom_fields.get(34)['value']},
                                                   {'id': 18, 'value': ticket_content.custom_fields.get(18)['value']},
                                                   {'id': 38, 'value': ticket_content.custom_fields.get(38)['value']}]
                        except Exception as e:
                            logging.info(
                                "Copy ticket from ID#%s on model#%s is failed on new ID#%s, target:%s, reason:%s", \
                                ticket_content.id, model, issue.id, target_version_name, e)
                            continue

                        issue.priority_id = self.priority_convert(ticket_content['priority']['id'])
                        # report_date = datetime.datetime.strptime(datetime, "%Y/%m/%d").date()
                        # issue.start_date = report_date

                        copy_file_list = copy.deepcopy(file_list)
                        if ticket_content['attachments'] != "N/A":
                            issue.uploads = copy_file_list
                        try:
                            issue.save()

                            relation = self.redmine.issue_relation.new()
                            relation.issue_id = issue.id
                            relation.issue_to_id = ticket_content.id
                            relation.relation_type = 'copied_from'
                            relation.save()

                            logging.info("Copy ticket from ID#%s on model#%s is created on new ID#%s, target:%s", \
                                         ticket_content.id, model, issue.id, target_version_name)
                        except Exception as e:
                            # print(e)
                            logging.info(
                                "Copy ticket from ID#%s on model#%s is failed on new ID#%s, target:%s, reason:%s", \
                                ticket_content.id, model, issue.id, target_version_name, e)
                            continue

            # path = os. getcwd()
            for file in file_list:
                os.remove(os.getcwd() + "\\" + file['filename'])

        tk.messagebox.showinfo("INFO", "Copy Ticket Is Finished")
        return

    def start_logging(self):
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

    def priority_convert(self, level):
        if level == 6:
            val = 19
        elif level == 5:
            val = 20
        elif level == 4:
            val = 21
        else:
            val = level
        return int(val)

@app.route('/')
def index_page():
    model_list = []
    version_list = []
    version_dict = []

    Redmine_Copy()
    model_list = Redmine_Copy.query_models()

    for model in model_list:
        self.ModelList.insert(tk.END, model)

    version_dict = self.query_version()
    for version in self.version_dict:
        self.version_list.append(version["name"])

    return render_template('index.html', models=model_list, versions=version_list)


if __name__ == '__main__':
    app.run()
