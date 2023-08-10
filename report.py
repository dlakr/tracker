import datetime
import os
import socket
from PRINT_LINK import write_log
import sqlite3

sleep = 3
period = 14
p_loc = "next_period"
c_name = socket.gethostname()
log_file = f"ttracker-{c_name}.log"
lock_file_path = "script.lock"
database_path = r'timeTracker-{}.sqlite'.format(c_name)
conn = sqlite3.connect(database_path)



def get_period():
    with open(p_loc) as f:
        p = f.read()
    return p
    # return "2023-07-24"

c_name = socket.gethostname()
log_file = f"ttracker-{c_name}.log"
date =  get_period()
format = "%Y-%m-%d"
dest = r"TRACKER"
if not os.path.exists(dest):
    os.mkdir(dest)
p_length = datetime.timedelta(days=period)
start = datetime.datetime.strptime(date, format)
end = start + p_length
counter = period
report_title = ""
log_msg = ''

# def write_log(info):
#     with open(log_file, "a") as f:
#         f.write(str(f"\n{info}"))


def write(f_name, data):
    with open(f_name, "w") as f:
        f.write(str(data))


def retrieve_data(start, end):
    cursor = conn.cursor()
    st = start - datetime.timedelta(days=1)
    out = []
    query = """
    SELECT project_id, date, time 
    FROM Time WHERE date 
    BETWEEN ? AND ? 
    """
    d2 = {}
    cursor.execute(query, (st, end))
    rows = cursor.fetchall()
    for row in rows:
        project_id, date, time = row
        p = f"""date:{date},\nproject: {project_id}\ntime: {time}\n"""
        d = {'date': date, 'project': project_id, 'time': time}
        d2[date] = d2.get(date, {})
        d2[date][project_id] = d2[date].get(project_id, time)

    return d2


def convert_integer_to_time(integer):
    duration = datetime.timedelta(seconds=integer)
    return duration


def generate_html(data, title):
    html_content = f"""
    <html>

    <head>
        <link rel="stylesheet" href="report_style.css">
        <title>{title}</title>

    </head>
    <body>
        <h1>{title}</h1>


    """
    for v in data:
        day = datetime.datetime.strptime(v, '%Y-%m-%d').strftime("%A")
        print(f"item:{day} - {v}")
        day_date = f"{day} - {v}"
        html_content += f"""
        <div class="table-container">
            <table class="table">
                <th colspan='2'>{day_date}</th>
                <tr class="column-headers">
                    <td>PROJECT</td>
                    <td>TIME</td>
                </tr>
"""


        for inner_v in data[v]:
            time = convert_integer_to_time(int(data[v][inner_v]))
            html_content += f"""
                    <tr>
                        <td>{inner_v}</td>
                        <td>{time}</td>
                    </tr>
        """

    html_content += """
            </table>
        </div>
    </body>
    </html>
    """

    return html_content
def create_report(entries, title):

    output = os.path.join(dest, f"{title}.html")
    html = generate_html(entries, title)
    write(output, html)


def report():

    start = datetime.datetime.strptime(get_period(), format)
    end = start + p_length
    rt = f"Report_{start.date()}_to_{end.date()}"

    now = datetime.date.today()
    now_dt = datetime.datetime.strftime(now, format)
    start_dt = datetime.datetime.strftime(start, format)

    if now_dt >= start_dt:
        write_log(f'{now} - publishing {rt}')
        data = retrieve_data(start, end)
        create_report(data, rt)
        write(p_loc, end.date())


# report()