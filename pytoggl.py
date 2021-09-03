import base64
import datetime
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

print("--pytoggl--")
# Get timezone difference to UTC
TZ_DIFF = "%02d:00" % int(
    datetime.datetime.now()
    .astimezone()
    .tzinfo.utcoffset(datetime.datetime.now())
    .seconds
    / 3600
)
if TZ_DIFF[0] != "-":
    TZ_DIFF = "+" + TZ_DIFF
print("Detected timezone UTC difference: %s hrs" % TZ_DIFF)
TOGGL_DIR = Path.home().joinpath(".local/share/toggl")
Path(TOGGL_DIR).mkdir(parents=True, exist_ok=True)
API_KEY_FILE = Path(TOGGL_DIR).joinpath("api_key")
FAV_PROJECTS_FILE = Path(TOGGL_DIR).joinpath("fav_projects")
API_URL = "https://api.track.toggl.com/api/v8"

if API_KEY_FILE.is_file():
    with open(API_KEY_FILE, "r") as api_key_file:
        API_KEY = api_key_file.read().strip()
        auth = base64.b64encode(bytes("%s:%s" % (API_KEY, "api_token"), "ascii"))
else:
    print(
        "No API key file found. Make sure you have your API key stored in a text file in '%s'"
        % str(API_KEY_FILE)
    )
    exit(1)

headers = {
    "Content-Type": "application/json",
    "Authorization": "Basic %s" % auth.decode("utf-8"),
}
USED_FAVORITE = False
chosen_fav = "-1"
if FAV_PROJECTS_FILE.is_file():
    print("Favorites:\n")
    print(30 * "-")
    with open(FAV_PROJECTS_FILE, "r") as fav_projects_file:
        fav_projects = sorted(fav_projects_file.readlines())
        for idx, fav in enumerate(fav_projects):
            print("[%s] %s" % (idx, fav.strip().split("\t")[1]))
        while chosen_fav not in [str(i) for i in range(len(fav_projects))] + [""]:
            chosen_fav = input(
                "Choose favorite project (leave empty for manual setup): "
            )
            if chosen_fav != "":
                USED_FAVORITE = True
                sel_project = fav_projects[int(chosen_fav)]
                sel_project_id = sel_project.split("\t")[0]
                sel_project_name = sel_project.split("\t")[1]
# MANUAL SETUP
if chosen_fav in ["", "-1"]:
    request_workspaces = Request(API_URL + "/workspaces", headers=headers)
    workspaces_json = json.loads(urlopen(request_workspaces).read().decode())
    chosen_workspace = -1
    while chosen_workspace not in [str(i) for i in range(0, len(workspaces_json))]:
        print("Available workspaces:\n")
        print(30 * "-")
        for idx, workspace in enumerate(workspaces_json):
            print("[%s] %s\n" % (idx, workspace["name"].strip()))
        chosen_workspace = input(
            "Choose a workspace (default: '%s'): " % workspaces_json[0]["name"]
        )
        if chosen_workspace == "":
            chosen_workspace = str(0)
    sel_workspace_id = workspaces_json[int(chosen_workspace)]["id"]

    request_clients = Request(
        API_URL + "/workspaces/%s/clients" % sel_workspace_id, headers=headers
    )
    clients_json = json.loads(urlopen(request_clients).read().decode())

    clients = {client["id"]: client["name"] for client in clients_json}

    request_projects = Request(
        API_URL + "/workspaces/%s/projects" % sel_workspace_id, headers=headers
    )
    projects_json = json.loads(urlopen(request_projects).read().decode())
    chosen_project = -1
    while chosen_project not in [str(i) for i in range(0, len(projects_json))]:
        print("Available projects:\n")
        print(30 * "-")
        for idx, project in enumerate(projects_json):
            print(
                "[%s] %s - %s" % (idx, clients[project["cid"]], project["name"].strip())
            )
        chosen_project = input("Choose a project: ")

    sel_project = projects_json[int(chosen_project)]
    sel_project_id = sel_project["id"]
    sel_project_name = "%s - %s" % (
        clients[sel_project["cid"]],
        sel_project["name"].strip(),
    )

# QUICK SETUP
description = ""
while description == "":
    description = input("Add description: ")
today_iso = datetime.date.today().isoformat()
day = ""
while len(day) != 10:
    day = input("Set day (default '%s'): " % today_iso)
    if day == "":
        day = today_iso
start_time = ""
while len(start_time) != 4:
    start_time = input("Set start time [hhmm]: ")
start_time = start_time[0:2] + ":" + start_time[2:4]
end_time = ""
while len(end_time) != 4:
    end_time = input("Set end time [hhmm]: ")
end_time = end_time[0:2] + ":" + end_time[2:4]

duration = (
    datetime.datetime.strptime(end_time, "%H:%M")
    - datetime.datetime.strptime(start_time, "%H:%M")
).seconds

print(duration)

print("\n--NEW TIME ENTRY--")
print(30 * "-")
print("Project: %s" % sel_project_name)
print("Start time: %s" % start_time)
print("End time: %s" % end_time)
print("Description: %s" % description)
print(30 * "-")
submit_confirmation = ""
while submit_confirmation.lower() not in ("y", "n"):
    submit_confirmation = input("Submit time entry? [y/n]: ")

if submit_confirmation.lower() == "y":
    post_fields = {
        "time_entry": {
            "description": description,
            "duration": duration,
            "start": "%sT%s:00%s" % (day, start_time, TZ_DIFF),
            "pid": sel_project_id,
            "created_with": "pytoggl",
        }
    }
    request_time_entry = Request(
        API_URL + "/time_entries",
        data=bytes(json.dumps(post_fields), encoding="utf-8"),
        headers=headers,
    )
    time_entry_response = json.loads(urlopen(request_time_entry).read().decode())
    if "data" in time_entry_response.keys():
        print("Time entry submitted succesfully.")

    if not USED_FAVORITE:
        project_confirmation = ""
        while project_confirmation.lower() not in ("y", "n"):
            project_confirmation = input("Save project to favorites? [y/n]: ")

        if project_confirmation.lower() == "y":
            if FAV_PROJECTS_FILE.is_file():
                with open(FAV_PROJECTS_FILE, "r") as fav_projects_file:
                    fav_projects = set(fav_projects_file.readlines())
                    fav_projects.add("%s\t%s" % (sel_project_id, sel_project_name))
            else:
                fav_projects = {"%s\t%s" % (sel_project_id, sel_project_name)}
            with open(FAV_PROJECTS_FILE, "w+") as fav_projects_file:
                for fav in list(fav_projects)[:-1]:
                    fav_projects_file.write("%s\n" % fav.strip())
                fav_projects_file.write("%s" % list(fav_projects)[-1].strip())
            print("Project saved to favorites.")


else:
    print("Time entry not submitted.")
