from mongoengine import *



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


