import os
import zmq
import json
import gzip
import pickle
import shutil
import urllib.request


def init_listener():
    """
    Creates a listener communication pipe using
    PyZMQ to communicate with main program.
    """

    context = zmq.Context()
    socket = context.socket(zmq.PULL)

    socket.connect("tcp://localhost:5555")
    print("!...Initialized listener...!")
    return context, socket


def terminate_zmq(socket, context):
    """
    Terminates the communication pipe b/t location
    verification microservice & main program.
    """

    socket.close()
    context.term()
    print("!...Listener Terminated...!")


def download_wapi_cache():
    """
    Downloads and unzips a copy of the Weather API
    for microservice location verification feature.

    General SRC: https://bulk.openweathermap.org/sample/
    """

    url = 'https://bulk.openweathermap.org/sample/city.list.json.gz'

    # Checks if relative path exists.
    if not os.path.exists('weatherapi_cache'):
        os.makedirs('weatherapi_cache')
        urllib.request.urlretrieve(url, 'city.list.json.gz')

    # Error: Path already exists
    else:
        msg = 'error'
        return msg

    # Unzip file contents to cache repository.
    with gzip.open('city.list.json.gz', 'rb') as gz:
        path = 'weatherapi_cache/city.list.json'
        with open(path, 'wb') as gz_copy:
            shutil.copyfileobj(gz, gz_copy)

    # Remove the gzip file
    os.remove('city.list.json.gz')

    # DL was successful:
    msg = 'success'
    return msg


def receive_user_query(socket):
    """
    Receives user query information and returns
    it for use in location verification microservice.
    """

    print("!...Waiting for User Query...!")
    user_query = pickle.loads(socket.recv())

    print(f"Received {user_query}")
    return user_query


def package_results(filt_res):
    """
    Collates results into easily printable
    message format for main program to display.
    """

    # Handle empty filter list.
    if len(filt_res) == 0:
        msg = 'error'
        return msg

    # Case 1: Single Match:
    if len(filt_res) == 1:

        msg = ["single_match", []]

        # msg[2] -> length
        length = len(filt_res)
        msg.append(length)

        filt_res = filt_res[0]

        # msg[3] -> raw location data
        loc_data = filt_res
        msg.append(loc_data)

        # NOTE: Can remove these abbr.
        # Only using to match FLAKE8 style.

        n = filt_res['name']
        c = filt_res['country']

        if filt_res['state']:

            # Include state:
            s = filt_res['state']
            msg[1].append(f"[1]: {n}, {s}, ({c})")

        else:
            msg[1].append(f"[1]: {n}, ({c})")

    # Case 2: Multiple Matches:
    elif len(filt_res) > 1:

        # msg_type, organized_msg, length, loc_data
        msg = ["multiple_matches", []]

        # msg[2] -> length
        length = len(filt_res)
        msg.append(length)

        # msg[3] -> raw location data
        loc_data = filt_res
        msg.append(loc_data)

        # Present first 3 matches.
        for i, l in enumerate(filt_res[:3], 1):
            full_loc = f"{l['name']}, ({l['country']})"

            if l.get('state'):
                full_loc = f"{l['name']}, {l['state']}, ({l['country']})"
            msg[1].append(f"[{i}] {full_loc}")

        if len(filt_res) > 3:
            msg[1].append("...")

    return msg


def handle_API_cache_query(query_type, msg_contents=[]):
    """
    Handles location query requests.
    Parses local API cache and returns
    valid location options to user.
    """

    # Connect to ZMQ comms pipe:
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:5556")

    # Prompt cache download.
    if query_type == 'cache_dl':
        res = download_wapi_cache()

        # Error: Cache already exists.
        if res == 'error':
            socket.send(pickle.dumps('error'))
        else:
            socket.send(pickle.dumps('success'))

    # Read-in JSON file:
    fp = 'weatherapi_cache/city.list.json'
    with open(fp, 'r', encoding='utf-8') as cache:
        loc_data = json.load(cache)

    # Handle ZIP input:
    if query_type == 'zip':
        zip_code = msg_contents

        try:
            socket.send(pickle.dumps(int(zip_code)))
        except ValueError:
            socket.send(pickle.dumps('error'))

    filters_dict = {
        'name': None,
        'country_code': None,
        'state': None
    }

    # Handle additional filtering data:
    if query_type == 'filter_query':

        # Location Name:
        if msg_contents[0]:
            filters_dict['name'] = msg_contents[0].lower()

        # Country Code
        if msg_contents[1].strip():
            filters_dict['country_code'] = msg_contents[1].upper()

        # State Abbreviation
        if msg_contents[2].strip():
            filters_dict['state'] = msg_contents[2].upper()

        query_type = 'query'

    fd_country = filters_dict["country_code"]
    fd_state = filters_dict["state"]

    # Handle general loc query search:
    if query_type == "query":

        # Check if loc name exists in filters.
        if not filters_dict['name']:
            filters_dict['name'] = msg_contents.lower()

        # Store filtered results.
        filt_res = []

        # Parse Weather API Cache locations.
        for loc in loc_data:

            # Filter mismatching city/towns.
            if loc.get('name').lower() != filters_dict['name']:
                continue
            # Filter mismatching countries.
            if fd_country and loc.get('country') != fd_country:
                continue
            # Filter mismatching states.
            if fd_state and loc.get('state') != fd_state:
                continue

            # Add matching results.
            filt_res.append(loc)

        # Send err if no loc found:
        if not filt_res:
            socket.send(pickle.dumps('error'))

        # Send [msg_type, organized_msg, length, loc_data] as msg
        else:
            msg = package_results(filt_res)
            socket.send(pickle.dumps(msg))

    terminate_zmq(socket, context)
    return


if __name__ == "__main__":
    context, socket = init_listener()

    while True:

        # Receive user query.
        uq = receive_user_query(socket)

        # Quit
        if uq == "Q":
            terminate_zmq(socket, context)
            break

        # Prompt cache download (if needed).
        if uq and isinstance(uq, list) and uq[0] == 'cache_dl':
            handle_API_cache_query(uq[0])

        # Check if initial query.
        if uq and isinstance(uq, list) and uq[0] == "query":
            handle_API_cache_query(uq[0], uq[1])

        # Check if initial query.
        if uq and isinstance(uq, list) and uq[0] == "filter_query":
            handle_API_cache_query(uq[0], uq[1])

        # Check if zip query.
        if uq and isinstance(uq, list) and uq[0] == "zip":
            handle_API_cache_query(uq[0], uq[1])
