# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START taskqueues_request_handler]
from flask import Flask, request
from google.cloud import datastore


app = Flask(__name__)


@app.route('/')
def main():
    counter = get_counter()
    count = counter['count']
    html = """
            Count: {}<br>
            <form method="post" action="/enqueue">
                <label>Increment amount</label>
                <input name="amount" value="1">
                <button>Enqueue task</button>
            </form>
            """.format(count)
    return html


@app.route('/enqueue', methods=['POST'])
def enqueue():
    from google.cloud import tasks_v2beta3

    # Create a client.
    client = tasks_v2beta3.CloudTasksClient()

    # Get increment amount from form
    payload = request.form["amount"]

    # TODO(developer): Replace with your values.
    project = 'my-project-id'
    queue = 'my-queue'
    location = 'us-central1'

    # Construct the fully qualified queue name.
    parent = client.queue_path(project, location, queue)

    # Construct the request body.
    task = {
            'app_engine_http_request': {  # Specify the type of request.
                'http_method': 'POST',
                'relative_uri': '/update_counter',
                'body': payload.encode()
            }
    }

    # Use the client to build and send the task.
    response = client.create_task(parent, task)

    return "Task enqueued"


@app.route('/update_counter', methods=['POST'])
def example_task_handler():
    # [START taskqueues_secure_handler]
    if request.headers.get('X-Appengine-Taskname') is None:
        # You may use the presence of the X-Appengine-Taskname header to validate
		# the request comes from Cloud Tasks.
        print('Invalid Task: No X-Appengine-Taskname request header found')
        return 'Bad Request - Invalid Task', 400
    # [END taskqueues_secure_handler]

    amount = int(request.get_data())
    uodate_counter(amount)
    return


def get_counter():
    # Instantiates a client
    client = datastore.Client()

    key = client.key('Counter', 'count')
    counter = client.get(key)
    return counter


def update_counter(amount):
    counter = get_counter()

    # Create entity if it doesn't exist
    if counter is None:
        counter = datastore.Entity(key)
        previous = 0
    else:
        previous = counter['count']

    counter.update({'count': amount + previous})
    # Send update request
    client.put(counter)

    print('Counter: {}'.format(amount + previous))
    return


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END taskqueues_request_handler]
