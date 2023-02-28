from flask import Flask, render_template, request, redirect
from redminelib import


app = Flask(__name__)


@app.route('/')
def hello_world():
    models = []
    models = query_model()
    #return model_list
    return render_template('index.html',models=models)

def query_model():
    redmine_version = '3.4.6-stable'
    key = '9e162fa25b0267706cd589c99817b66403a8edfe'
    server = 'http://172.20.0.37'
    redmine_server = Redmine(server, key=key, version=redmine_version)


    name_list = []
    select_model = ["VMG", "DX", "AX", "EX", "WX", "PX", "PE", "EE"]
    # issues = redmine.issue.filter(project_id='Telefonica', tracker_id=1, status_id='*')
    # ticket = redmine.issue.get(126600)
    model_field = redmine_server.custom_field.get(14)
    service_profile = redmine_server.custom_field.get(15)
    service_type = redmine_server.custom_field.get(16)
    model_field = redmine_server.custom_field.get()
    new_project = redmine_server.custom_field.get(14)
    service = []
    


    for service in service_profile:
        service.append(service.name)

    for model in model_field.possible_values:
        for selective in select_model:
            if selective in model["value"]:
                name_list.append(model["value"])
    return name_list

if __name__ == '__main__':
    app.run()
