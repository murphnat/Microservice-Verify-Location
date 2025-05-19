
# REQUIRED (NOTE: Necessary for microservice communication.)
import zmq
import pickle
import requests

from dotenv import load_dotenv  # Used to access API securely.

# OPTIONAL (NOTE: Requires modifying codebase.)
# -------- (NOTE: Removal will require manual download of API location cache.)
import platform
import os


def clear_terminal():
    """
    Clears user terminal/CMD window.
    Works for PC/MAC systems.
    """

    # Get user OS.
    user_os = platform.system()

    # Use os-specific command.
    if user_os == 'Darwin':
        os.system('clear')
    else:
        os.system('cls')


def terminate_zmq(socket, context):
    """
    Terminates the communication pipe b/t location
    verification microservice & main program.
    """

    socket.close()
    context.term()


def header_msg():
    """
    Prints header message
    on the CMD interface.
    """

    # Header Message:
    print("//////////////////")
    print("Weather App (Test)")
    print("//////////////////")
    print("")


def download_wapi_cache():
    """
    Downloads and unzips a copy of the Weather API
    for microservice location verification feature.

    General SRC: https://bulk.openweathermap.org/sample/
    """

    # Get user permission:
    print("NOTE: To function - the WeatherPy CLI requires")
    print("a local copy of the Weather API Location Cache.")
    print("")
    print("Download [Y/N]?")
    print("")
    inp = input("Input: ")

    # Case 1: DL Permitted.
    if inp in ['Yes', 'yes', 'Y', 'y']:

        # Establish ZMQ PUSH pipe:
        push_context = zmq.Context()
        push_socket = push_context.socket(zmq.PUSH)
        push_socket.bind("tcp://*:5555")

        # Establish ZMQ PULL pipe:
        pull_context = zmq.Context()
        pull_socket = pull_context.socket(zmq.PULL)
        pull_socket.connect("tcp://localhost:5556")

        push_socket.send(pickle.dumps(['cache_dl']))

        msg = pickle.loads(pull_socket.recv())

        terminate_zmq(push_socket, push_context)
        terminate_zmq(pull_socket, pull_context)

        if msg == 'success':
            print("")
            print("! - Download Successful - !")
            print("")
            input("Press enter to continue...")
            main_test()

        elif msg == 'error':
            print("")
            print("! - Error: Local cache file already exists - !")
            print("")
            input("Press enter to continue...")
            main_test()

    # Case 2: DL Denied.
    elif inp in ['No', 'no', 'N', 'n']:
        print("")
        print("! - User selected 'No' - !")
        print("Search feature unavailable...")
        print("")
        input("Press enter to continue...")
        main_test()

    # Case 3: Error / Invalid Input.
    else:
        print("")
        print("! - Invalid input - !")
        print("")
        input("Press enter to continue...")
        main_test()


def main_test():
    """
    Mock simulation of Weather Application.
    """

    # Setup CMD environment:
    clear_terminal()
    header_msg()

    # Check if user has local copy of Weather API location cache:
    if not os.path.isfile("weatherapi_cache/city.list.json"):

        # Prompt download.
        download_wapi_cache()

    # Draw user options:
    print("[1] Get Weather")
    print("[2] Exit")
    print("")
    nav_inp = input("Input [#]: ")

    # Get weather for loc of interest.
    if nav_inp in ['1', '[1]']:

        # Get API info:
        load_dotenv()
        _api_key = os.getenv("WEATHER_API_KEY")
        _base_url = "http://api.openweathermap.org/data/2.5/weather?"
        u = 'imperial'

        # Get loc info via microservice.
        loc = get_location()

        # Clear interface.
        clear_terminal()
        header_msg()

        # Case 1: User input ZIP of location:
        if isinstance(loc, int):

            # Build URL from ZIP.
            url = f"{_base_url}appid={_api_key}&zip={loc},us&units={u}"
            res = requests.get(url)
            wd = res.json()

            # Check 'good' API response:
            if wd['cod'] == 200:
                print(f"Weather for area code {loc}:")
                print("")
                print(wd['main'])

            # API Error / Invalid Zip:
            else:
                print("")
                print("! - Invalid Zip / API Response Error - !")
                print("")
                input("Press enter to continue...")
                main_test()

        # Case 2: User filtered down location:
        else:

            # Build URL from lat/lon:
            lat = loc['coord']['lat']
            lon = loc['coord']['lon']
            url = f"{_base_url}appid={_api_key}&lat={lat}&lon={lon}&units={u}"

            res = requests.get(url)
            wd = res.json()

            # Check if 'good' API response:
            if wd['cod'] == 200:
                n = loc['name']
                c = loc['country']

                if loc['state']:
                    s = loc['state']
                    print(f"Weather for {n}, {s}, ({c}):")
                else:
                    print(f"Weather for {n}, ({c})")

                print(wd['main'])

            # API Error:
            else:
                print("")
                print("! - API Response Error - !")
                print("")
                input("Press enter to continue...")
                main_test()

        print("")
        input("Press enter to continue...")
        main_test()

    # Terminate microservice & exit.
    elif nav_inp in ['2', '[2]']:

        # Send "Quit" request to microservice.
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.bind("tcp://*:5555")
        socket.send(pickle.dumps("Q"))

        # Close ZMQ connection pipe.
        terminate_zmq(socket, context)

        # Clear CMD interface.
        clear_terminal()
        exit()

    # Handle user input err:
    else:

        print("")
        print("! - Invalid input - !")
        print("")
        input("Press enter to continue...")
        main_test()


def handle_single_match(msg, push_socket, pull_socket,
                        push_context, pull_context):
    """
    Handles logic for displaying
    single match location to user.
    """

    # Tidy CMD interface.
    clear_terminal()
    header_msg()

    # Print match count.
    print("! - 1 match found - !")
    print("")

    # Print valid loc.
    print(msg[1][0])

    # Check if correct loc w/ user.
    print("")
    print("Is this location correct? [Y/N]")
    print("")
    inp = input("Input: ")

    while True:

        clear_terminal()
        header_msg()
        print("")

        # Case 1: Correct location of interest.
        if inp in ['Yes', 'yes', 'Y', 'y']:
            return msg[3]

        # Case 2: Incorrect location.
        elif inp in ['No', 'no', 'N', 'n']:

            clear_terminal()
            header_msg()
            print("")

            # Prompt for zip code as no other alternative
            # filtering option is available to narrow results.
            zip_code = input("Zip Code: ")

            # Push zip to microservice.
            # NOTE: This bit is kind of redundant and should
            # really be done within the main program as the
            # API handles US-based zipcodes natively.
            # That information isn't present in the JSON
            # cache file that this microservice is based around.
            push_socket.send(pickle.dumps(['zip', zip_code]))
            zip_msg = pickle.loads(pull_socket.recv())

            # Handle user input err.
            if zip_msg == 'error':
                print("")
                print("! - Invalid Input - !")
                print("")
                input("Press enter to continue...")

                terminate_zmq(push_socket, push_context)
                terminate_zmq(pull_socket, pull_context)

                main_test()

            # Return valid ZIP to main program.
            else:
                return zip_msg

        # Handle user input err.
        else:
            print("")
            print("! - Invalid input - !")
            print("")
            input("Press enter to continue...")

            terminate_zmq(push_socket, push_context)
            terminate_zmq(pull_socket, pull_context)

            main_test()


def get_filter_input(city_town_name):
    """
    Gets user filter input to pare down
    potential locations of interest.
    """

    # Tidy CMD.
    clear_terminal()
    header_msg()

    filters = [city_town_name]

    # Prompt user for additional filter data.
    print("Follow prompt /OR/ Press 'enter' to skip.")
    print("")
    filters.append(input("Country Code: ").upper())
    filters.append(input("State (abbr.): ").upper())

    return filters


def get_location():
    """
    Uses PyZMQ to communicate with
    location verification microservice.

    Microservice parses API location cache
    for user's town/city of interest.
    """

    # Tidy CMD.
    clear_terminal()
    header_msg()

    # Establish ZMQ PUSH pipe:
    push_context = zmq.Context()
    push_socket = push_context.socket(zmq.PUSH)
    push_socket.bind("tcp://*:5555")

    # Establish ZMQ PULL pipe:
    pull_context = zmq.Context()
    pull_socket = pull_context.socket(zmq.PULL)
    pull_socket.connect("tcp://localhost:5556")

    # Get init location query:
    city_town_name = input("City/Town: ").lower()

    # Send query to microservice:
    push_socket.send(pickle.dumps(['query', city_town_name]))
    msg = pickle.loads(pull_socket.recv())

    # Handle user input err...
    if msg == 'error':
        print("")
        print(f"Error: No location matching {city_town_name} identified.")
        print("")
        input("Press enter to continue...")

        terminate_zmq(push_socket, push_context)
        terminate_zmq(pull_socket, pull_context)

        main_test()

    else:

        # Case 1: Exact Match w/ (optional) Zip Code filtering:
        if msg[0] == 'single_match':
            res = handle_single_match(msg, push_socket, pull_socket,
                                      push_context, pull_context)

            terminate_zmq(push_socket, push_context)
            terminate_zmq(pull_socket, pull_context)

            return res

        # Case 2: Multiple Matches:
        # NOTE: Could be refactored into its own function.
        elif msg[0] == "multiple_matches":

            while True:

                # Tidy CMD.
                clear_terminal()
                header_msg()

                # Draw found match count msg to terminal.
                print(f"! - {msg[2]} matches found - !")
                print("")

                # Print valid locations options:
                for i in msg[1]:
                    print(i)

                # Prompt user to filter or select options (1-3):
                print("")
                print("Select a matching location [#]")
                print("/OR/ Type 'filter' to narrow search.")
                print("")
                inp = input("Input: ")

                # Filter using 'Country Code' or 'State' info:
                if inp in ['Filter', 'filter', 'Filters', 'filters', 'F', 'f']:

                    # Get additional filter information from user:
                    fd = ['filter_query', get_filter_input(city_town_name)]

                    # Send info to microservice to parse through
                    # the Weather API local cache.
                    push_socket.send(pickle.dumps(fd))
                    msg = pickle.loads(pull_socket.recv())

                    # Handle user err or no match case:
                    if msg == "error":
                        print("")
                        print("! - Invalid filter /OR/ No match - !")
                        print("")
                        input("Press enter to continue...")

                        terminate_zmq(push_socket, push_context)
                        terminate_zmq(pull_socket, pull_context)

                        main_test()

                    # Handle single match case:
                    if msg[0] == 'single_match':
                        res = handle_single_match(msg,
                                                  push_socket,
                                                  pull_socket,
                                                  push_context,
                                                  pull_context)

                        terminate_zmq(push_socket, push_context)
                        terminate_zmq(pull_socket, pull_context)

                        return res

                    continue

                # Prompt user to select from top 3 loc options:
                elif inp in ['1', '2', '3']:
                    i = int(inp) - 1
                    if 0 <= i < 3:
                        res = msg[3][i]

                        terminate_zmq(push_socket, push_context)
                        terminate_zmq(pull_socket, pull_context)

                        return res

                    # Handle user err:
                    else:
                        print("")
                        print("! - Invalid Input - !")
                        print("")
                        input("Press enter to continue...")

                    terminate_zmq(push_socket, push_context)
                    terminate_zmq(pull_socket, pull_context)

                    continue

                # Handle user err:
                else:
                    print("")
                    print("! - Invalid Input - !")
                    print("")
                    input("Press enter to continue...")

                    terminate_zmq(push_socket, push_context)
                    terminate_zmq(pull_socket, pull_context)

                    main_test()


if __name__ == "__main__":
    main_test()
