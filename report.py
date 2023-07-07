import datetime

import os
import socket
from PRINT_LINK import write_log
sleep = 3
period = 14

p_loc = "next_period"


def get_period():
    with open(p_loc) as f:
        p = f.read()
    return p

c_name = socket.gethostname()
log_file = f"ttracker-{c_name}.log"
date =  get_period()
format = "%Y-%m-%d"
dest = r"F:\Dropbox\_Admin_office\LEGAL_&_FINANCE\TIMESHEETS_PLICO\TRACKER"
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


def retrieve_data(conn, start, end):
    cursor = conn.cursor()
    out = []
    query = """
    SELECT project_id, date, time 
    FROM Time WHERE date 
    BETWEEN ? AND ? 
    GROUP BY date"""

    cursor.execute(query, (start, end))
    rows = cursor.fetchall()
    for row in rows:
        project_id, date, time = row

        p = f"""date:{date},\nproject: {project_id}\ntime: {time}\n"""
        d = {'date': date, 'project': project_id, 'time': time}
        out.append(d)
        print(p)

    return out

def convert_integer_to_time(integer):
    duration = datetime.timedelta(seconds=integer)
    return duration

print(convert_integer_to_time(15330))
def generate_html(data, title):
    html_content = f"""
    <html>
        
    <head>
        <link rel="stylesheet" href="report_style.css">
        <title>{title}</title>
        
    </head>
    <body>
        <h1>{title}</h1>
        <div class="table-container">
            <table class="table">
                <tr>
                    <th>DATE</th>
                    <th>PROJECT</th>
                    <th>TIME</th>
                </tr>
    """

    for item in data:
        time = convert_integer_to_time(item['time'])
        html_content += f"""
                <tr>
                    <td>{item['date']}</td>
                    <td>{item['project']}</td>
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


def report(conn):
    start = datetime.datetime.strptime(get_period(), format)
    end = start + p_length
    rt = f"Report_{start.date()}_to_{end.date()}"

    now = datetime.date.today()
    now_dt = datetime.datetime.strftime(now, format)
    start_dt = datetime.datetime.strftime(start, format)

    if now_dt >= start_dt:
        write_log(f'{now} - publishing {rt}')
        data = retrieve_data(conn, start, end)
        create_report(data, rt)
        write(p_loc, end.date())


