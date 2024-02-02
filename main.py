from http.server import HTTPServer, CGIHTTPRequestHandler
import time
import json
from urllib.parse import parse_qs
from Loggin_etc import *
from datetime import datetime
import logging
import sqlalchemy
from mongoengine import connect
from mongo_todos import mongoTodos
from postgres_todos import PostgresTodos
from sqlalchemy.orm import Session
import sqlalchemy


"""
1. Only do MONGO db side with mongoengine
2. Remove TODO CLASS

"""

todos = []
request_number = 1
postgres_engine = sqlalchemy.create_engine('postgresql://postgres:docker@localhost:5432/todos', echo=False)
with Session(postgres_engine) as session, session.begin():
    idGenerator = PostgresTodos.get_number_of_entries(session)
connect('todos', host='localhost', port=27017)




class TODO:
    def __init__(self, id, title, content, dueDate, status):
        global idGenerator
        self.id = id
        self.title = title
        self.content = content
        self.dueDate = dueDate
        self.status = status
        idGenerator += 1


class MyHTTP(CGIHTTPRequestHandler):

    global idGenerator, todos, request_number
    log_formatter = LogFormatter()
    request_logger = RequestLogger(log_formatter)
    todo_logger = TodoLogger(log_formatter)


    def do_PUT(self):
        global request_number
        start_time = time.time()
        my_path = self.path.split('?', 1)[0]
        self.request_logger.request_info("INFO", "PUT", my_path, request_number)

        if my_path == '/logs/level':
            params = self.path.split('?', 1)[-1]
            params = parse_qs(params)
            logger_name = params['logger-name'][0]
            logger_level = params['logger-level'][0]

            if logger_name == "request-logger":
                self.request_logger.set_level(logger_level)
                res = logger_level
                self.send_response(200)
            elif logger_name == "todo-logger":
                self.todo_logger.set_level(logger_level)
                res = logger_level
                self.send_response(200)
            else:
                self.send_response(400)
                res = ":("

            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(f"{res}", "utf-8"))



        if my_path == '/todo':
            statusname = ""
            didfind = invalid = False

            query_string = self.path.split('?', 1)[-1]
            query_params = parse_qs(query_string)
            identity = int(query_params['id'][0])
            status = query_params['status'][0]

            self.todo_logger.todo_info(f"Update TODO id [{identity}] state to {status}", request_number)


            if status in ['PENDING', 'LATE', 'DONE']:
                with Session(postgres_engine) as session, session.begin():
                        old_status = PostgresTodos.update_state_by_rawid(session, identity, status)
                        mongoTodos.update_state_by_rawid(identity, status)
            else:
                res = {
                    "errorMessage": f"Error: no such TODO with id {identity}"
                }
                self.send_response(400)
                
            if old_status is not None:
                self.todo_logger.todo_debug(f"Todo id [{identity}] state change: {old_status} --> {status}", request_number)
                res = {
                    "result": old_status
                }
                self.send_response(200)
            else:
                self.todo_logger.todo_error(f"Error: no such TODO with id {identity}", request_number)
                res = {
                    "errorMessage": f"Error: no such TODO with id {identity}"
                }
                self.send_response(404)

            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        self.request_logger.request_debug("DEBUG", (time.time() - start_time) * 1000, request_number)
        request_number += 1

    def do_DELETE(self):
        global request_number, idGenerator
        start_time = time.time()
        my_path = self.path.split('?', 1)[0]
        self.request_logger.request_info("INFO", "DELETE", my_path, request_number)

        if my_path == '/todo':
            query_string = self.path.split('?', 1)[-1]
            query_params = parse_qs(query_string)
            identity = int(query_params['id'][0])
            didremove = False


            with Session(postgres_engine) as session, session.begin():
                    didremove = PostgresTodos.delete_by_rawid(session, identity)

            if didremove:
                idGenerator -= 1
                self.todo_logger.todo_info(f"Removing todo id {identity}", request_number)
                self.todo_logger.todo_debug(f"After removing todo id [{identity}]"
                                            f" there are {len(todos)} TODOs in the system", request_number)

                self.send_response(200)
                res = {
                    "result": PostgresTodos.get_number_of_entries(session)
                }
            else:
                self.todo_logger.todo_error(f"Error: no such TODO with id {identity}", request_number)
                self.send_response(404)
                res = {
                    "errorMessage": f"Error: no such TODO with id {identity}"
                }

            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        self.request_logger.request_debug("DEBUG", (time.time() - start_time) * 1000, request_number)
        request_number += 1


    def do_GET(self):
        global request_number
        my_path = self.path.split('?', 1)[0]
        start_time = time.time()
        self.request_logger.request_info("INFO", "GET", my_path, request_number)

        if my_path == '/logs/level':
            logger_name = self.path.split('?', 1)[-1]
            logger_params = parse_qs(logger_name)
            logger_name = logger_params['logger-name'][0]

            if logger_name == "request-logger":
                level = self.request_logger.get_level()
                res = logging.getLevelName(level)
                self.send_response(200)
            elif logger_name == "todo-logger":
                level = self.request_logger.get_level()
                res = logging.getLevelName(level)
                self.send_response(200)
            else:
                res = "Wrong input mr checker try again"
                self.send_response(400)

            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(f"{res}", "utf-8"))

        if my_path == '/todo/health':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("OK", "utf-8"))

        elif my_path == '/todo/size':
            is_invalid = False
            query_string = self.path.split('?', 1)[-1]
            query_params = parse_qs(query_string)
            status = query_params.get('status', ['ALL'])[0]
            persistence_method = query_params.get('persistenceMethod', [None])[0]

            if status in ['ALL', 'PENDING', 'LATE', 'DONE']:
                if persistence_method == 'POSTGRES':
                    with Session(postgres_engine) as session, session.begin():
                        numoftodos = PostgresTodos.get_number_of_entries(session, status)
                elif persistence_method == 'MONGO':
                    numoftodos = mongoTodos.get_number_of_entries(status)

            else:
                is_invalid = True

            if not is_invalid:
                res = {
                    "result": numoftodos
                }
                self.send_response(200)
            else:
                res = {
                    "errorMessage": f"Invalid status: {status}"
                }
                self.send_response(400)

            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            self.todo_logger.todo_info(f"Total TODOs count for state {status} is {numoftodos}", request_number)

        elif my_path == '/todo/content':
            is_invalid = False
            query_string = self.path.split('?', 1)[-1]
            query_params = parse_qs(query_string)

            persistence_method = query_params.get('persistenceMethod', [None])[0]
            status = query_params.get('status', ['ALL'])[0]
            sortby = query_params.get('sortBy', ['ID'])[0]


            self.todo_logger.todo_info(f"Extracting todos content. Filter: {status} | Sorting by: {sortby}", request_number)
   
            if status in ['ALL', 'PENDING', 'LATE', 'DONE']:
                if persistence_method == 'POSTGRES':
                    with Session(postgres_engine) as session, session.begin():
                        sortedjson, counter = PostgresTodos.get_entries_as_json(session, status, sortby)
                elif persistence_method == 'MONGO':
                    sortedjson, counter = mongoTodos.get_entries_as_json(status, sortby)

         
            if sortedjson == None:  #Added if for invalid ~ check later
                is_invalid = False
            
            if not is_invalid:
                self.todo_logger.todo_debug(f"There are a total of {len(todos)}"
                                            f" todos in the system. The result holds {counter} todos", request_number)
                res = {
                    "result": sortedjson
                }
                self.send_response(200)
            else:
                res = {
                    "errorMessage": 'Invalid query parameter(s)'
                }
                self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        self.request_logger.request_debug("DEBUG", (time.time() - start_time) * 1000, request_number)
        request_number += 1


    def do_POST(self):
        global request_number, idGenerator
        my_path = self.path.split('?', 1)[0]
        start_time = time.time()
        self.request_logger.request_info("INFO", "POST", my_path, request_number)
        if my_path == '/todo':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode('utf-8'))

            content = payload.get('content', '')
            due = payload.get('dueDate', 0)
            title = payload.get('title', '')

            curtime = time.time() * 1000
            taken = late = False
            if due < curtime:
               late = True
            else:  
                with Session(postgres_engine) as session, session.begin():
                    try:
                        idGenerator += 1
                        PostgresTodos.create_entry(session, idGenerator, due, title, content)
                    except ValueError as e:
                        taken = e
           
            if late:
                res = {
                    "errorMessage": "Error: Can’t create new TODO that its due date is in the past"
                }
            elif taken:
                res = {
                    "errorMessage": f"Error: TODO with the title [{title}] already exists in the system"
                }
            else:
                res = {
                    "result": idGenerator
                }
            if taken:
                self.todo_logger.todo_error(f"Error: TODO with the title [{title}] already exists in the system", request_number)
            elif late:
                self.todo_logger.todo_error("Error: Can’t create new TODO that its due date is in the past", request_number)

            if taken or late:
                self.send_response(409)
            else:
                self.send_response(200)
                self.todo_logger.todo_info(f"Creating new TODO with Title [{title}]", request_number)
                self.todo_logger.todo_debug(f"Currently there are {idGenerator - 1} TODOs"
                                            f" in the system. New TODO will be assigned with id {idGenerator}", request_number)

            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        self.request_logger.request_debug("DEBUG", (time.time() - start_time) * 1000, request_number)
        request_number += 1



if __name__ == "__main__":
    server = HTTPServer(server_address=("", 9285), RequestHandlerClass=MyHTTP)
    print("Starting server...")
    server.serve_forever()
    server.server_close()
