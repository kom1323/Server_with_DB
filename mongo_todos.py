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
    def get_number_of_entries(cls, session):
        return cls.objects.count()
    



connect('todos', host='localhost', port=27017)
# If the connection is successful, print a success message
print(f"Connected to MongoDB database: todos")

# Query the collection to get all documents
documents = mongoTodos.objects()

# Print the content of each document
for doc in documents:
    print(f"Field Name: {doc.rawid}")