# Communication Contract
NOTE: Please reach out on Discord before Friday, May 30th, if you have any questions, comments, or concerns.

 

## 'Verify Location' Microservice Overview
The 'verify location' microservice provides a service for querying and filtering a local cache of cities and towns from OpenWeather to use in conjunction with their Weather API.

### Prerequisites
The microservice can run locally on PC within Windows Command Prompt or Powershell using Python 3. Mac and Linux compatibility remains untested at this time. The microservice communication pipeline relies on Python ZeroMQ. It utilizes (by default) PORT `5555` and PORT `5556`. Required python packages: `pyzmq, os, json, gzip, pickle, shutil, and urlib.request`.

### Install
1. Install third party packages:
  - `pip install pyzmq`

3. Run in CMD/Powershell.
  - `py verify_location.py`

## Requesting Data
1. Run in CMD/Powershell
  - `py verify_location.py`

2. Setup ZMQ Connections
```
# Example with ZMQ PUSH/PULL pattern:

# PUSH socket for sending requests
push_context = zmq.Context()
push_socket = push_context.socket(zmq.PUSH)
push_socket.bind("tcp://*:5555")
```

3. Send Query

#### Location Query:
```
# Example Location Query
city_name = "portland"
push_socket.send(pickle.dumps(['query', city_name]))
```

#### Filtered Location Query:
```
# Example Filtered Location Query
filters = ['portland', 'US', 'OR']
push_socket.send(pickle.dumps(['filter_query', filters]))
```

#### Zip Code Query:
```
# Example Zip Code Query
zip_code = "97331"
push_socket.send(pickle.dumps(['zip', zip_code]))
```

#### Cache DL Query:
```
# Example Cache DL Query:
push_socket.send(pickle.dumps(['cache_dl']))
```

#### Quit Microservice:
```
# Example Quit request:
push_socket.send(pickle.dumps('Q'))
```

## Receiving Data

1. Setup ZMQ Connections
```
# Example with ZMQ PUSH/PULL pattern:

# PULL socket for receiving responses
pull_context = zmq.Context()
pull_socket = pull_context.socket(zmq.PULL)
pull_socket.connect("tcp://localhost:5556")
```

2. Receive 'pickled' Python Obj.
```
`response = pickle.loads(pull_socket.recv())`
```

#### Error Response Format:
```
response = 'error'  
```

#### Single Match Response Format:
```
# Response = [Match Type, [plausible location display strings], num of matches, {location data}]

response = ['single_match',
           ['[1]: Portland, OR, (US)'],
           1,
           {'id': 5746545,'name': 'Portland', ... ,}]

# OR 'error'
```

#### Multiple Matches Response Format:
```
# Response = [Match Type, [plausible location display strings], num of matches, [{location data}]]

response = ['multiple_matches',
           ['[1] Portland, OR, (US)','[2] Portland, ME, (US)','[3] Portland, (AU)','...'],
           15,
           [{'id': 5746545, 'name': 'Portland', ..., }, {...}, {...}]]

# OR 'error'
```

#### Zip Code Response Format:
```
# Integer:
response = 97201

# OR 'error'
```

#### Cache DL Response Format
```
# String
response = 'success'

# OR 'error'
```

#### Quit Response Format
```
None -> no response sent to main program.
```

## UML Sequence Diagram:
TODO
