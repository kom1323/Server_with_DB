from mongoengine import *
import json


class mongoTodos(Document):
    title = StringField()
    state = StringField()
    content = StringField()
    rawid = IntField()  
    duedate = LongField()  
    meta = {
            'collection': 'todos' 
        }

    @classmethod
    def get_number_of_entries(cls, asked_status):
        if asked_status == 'ALL':
            return cls.objects.count()
        return cls.objects(state=asked_status).count()
    
    @classmethod
    def get_entries_as_json(cls, asked_status, asked_sortby):
        jsonarr = []
        sortedjson = []
        counter = 0

        if asked_status == "ALL":
            documents = cls.objects
        else:
            documents = cls.objects(state=asked_status)

        for doc in documents:    
            counter += 1
            jsonarr.append(json.loads(json.dumps({"id": doc.rawid, "title": f"{doc.title}", "content": f"{doc.content}", "status": f"{doc.state}", "dueDate": doc.duedate})))

        if asked_sortby == "ID":
            sortedjson = sorted(jsonarr, key=lambda y: y["id"])
        elif asked_sortby == "DUE_DATE":
            sortedjson = sorted(jsonarr, key=lambda y: y["dueDate"])
        elif asked_sortby == "TITLE":
            sortedjson = sorted(jsonarr, key=lambda y: y["title"])
        else:
            sortedjson = None

        return sortedjson, counter
    
    @classmethod
    def update_state_by_rawid(cls, rawid, new_state):
        doc = cls.objects(rawid=rawid).first()
        if doc:
            doc.state = new_state
            doc.save()