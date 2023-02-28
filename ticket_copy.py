from redminelib import Redmine
import redminelib
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as msgbox
from tkinter import ttk
import logging
import datetime
import sys, os
import copy

output_logging = 20

class Redmine_Copy(tk.Tk):
    def __init__(self, top=None):
        super().__init__()

        redmine = ""
        model_list = []
        x_loc = 0.01
        y_loc = 0.01
        x_gap = 0.2
        y_gap = 0.03

        self.start_logging()
        self.geometry("600x800+250+50")
        self.title("Redmine Ticket Copy Utility v1.0 (2023/2/2)")

        self.redmine = self.redmine_connect()
        self.LoopLabel = tk.Label(self, text='Redmine Ticket List:', anchor='w', justify='left')
        self.LoopLabel.place(relx=x_loc + 0.05, rely=y_loc, height=20, width=200)
        y_loc += y_gap
        self.TicketList = tk.Text(self)
        self.TicketList.place(relx=x_loc + 0.05, rely=y_loc, height=250, width=500)
        y_loc += y_gap * 11
        self.LoopLabel = tk.Label(self, text='Model List:', anchor='w', justify='left')
        self.LoopLabel.place(relx=x_loc + 0.05, rely=y_loc, height=20, width=200)
        y_loc += y_gap
        self.ModelList = tk.Listbox(self, selectmode=tk.EXTENDED)
        self.ModelList.place(relx=x_loc + 0.05, rely=y_loc, height=250, width=500)

        model_list = self.query_model()
        for model in model_list:
            self.ModelList.insert(tk.END, model)

        y_loc += y_gap * 11

        self.version_list = []
        self.version_dict = []
        self.version_dict = self.query_version()
        for version in self.version_dict:
            self.version_list.append(version["name"])

        self.TargetVersion_Label = tk.Label(self, text='Target:')
        self.TargetVersion_Label.place(relx=x_loc-0.1, rely=y_loc, height=32, width=250)
        self.TargetVersion = ttk.Combobox(self, width=600, values=self.version_list)
        self.TargetVersion.current(0)
        self.TargetVersion.place(relx=x_loc + x_gap, rely=y_loc, height=32, width=400)
        #self.TestType.bind("<<ComboboxSelected>>", self.test_profile_change)

        x_loc = 0.05
        y_loc += y_gap * 2
        self.StartButton = tk.Button(self, pady="0", text='Copy', command=self.start_copy)
        self.StartButton.place(relx=x_loc, rely=y_loc, height=31, width=150)

        # Configure the scrollbars
        #self.ResponseText = tk.Text(self, font=("Helvetica", 8))
        #self.ResponseText.place(relx=x_loc + 0.05, rely=y_loc, height=250, width=800)
        #self.ScrollBar = tk.Scrollbar(self.ResponseText)
        #self.ScrollBar.pack(side=tk.RIGHT, fill=tk.Y)
        #self.ScrollBar.config(command=self.ResponseText.yview)

    def query_version(self):
        version_list = []
        versions = self.redmine.version.filter(project_id="emea-bu-bug-report")
        #for testing
        #versions = self.redmine.version.filter(project_id="redmine-evaluatoin")
        for version_id in versions:
            if "OPAL" in version_id.name or "opal" in version_id.name:
                version_list.append({"name": version_id.name, "id": version_id.id})
        return version_list

    def redmine_connect(self):
        # Redmine setting
        redmine_version = '3.4.6-stable'
        key = '9e162fa25b0267706cd589c99817b66403a8edfe'
        server = 'http://172.20.0.37'
        redmine = Redmine(server, key=key, version=redmine_version)
        return redmine

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
            if target_version_name==version["name"]:
                version_id = version["id"]
                break

        #print (tickets)
        for ticket in ticket_list:
            if ticket !="":
                ticket_content = self.redmine.issue.get(int(ticket))
                file_list = []

                for item in ticket_content.attachments:
                    filepath = item.download(savepath=os. getcwd(), filename=item.filename)
                    file_list.append({'path': filepath, 'filename': item.filename})

                for model in model_list:
                    #print(ticket_content.custom_fields.get(14)['value'][0])
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
                        #report_date = datetime.datetime.strptime(datetime, "%Y/%m/%d").date()
                        #issue.start_date = report_date

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
                                         ticket_content.id, model ,issue.id, target_version_name)
                        except Exception as e:
                            #print(e)
                            logging.info("Copy ticket from ID#%s on model#%s is failed on new ID#%s, target:%s, reason:%s", \
                                         ticket_content.id, model ,issue.id, target_version_name , e)
                            continue

            #path = os. getcwd()
            for file in file_list:
                os.remove( os. getcwd() + "\\" + file['filename'])

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

if __name__ == '__main__':
    app = Redmine_Copy()
    app.mainloop()
    sys.exit(0)


