from fasthtml.common import *

app, rt = fast_app(live=True)

# check this for adv database: https://github.com/AnswerDotAI/fasthtml/blob/main/examples/adv_app.py
# https://github.com/langchain-ai/langgraph-fullstack-python/blob/main/src/react_agent/app.py


# This represents the data we are rendering
# The data could original from a database, or any other datastore
@dataclass
class Contact:
    # Data points
    id: int
    name: str
    email: str
    status: str


def ContactTr(contact: Contact):
    return Tr(
        *map(Td, (contact.name, contact.email, contact.status)),
        Td(
            Button(
                "Delete",
                hx_delete=delete.to(id=contact.id).lstrip("/"),
                # Give a confirmation prompt before deleting
                # hx_confirm="Are you sure?",
                # Target the closest row (The one you clicked on)
                hx_target="closest tr",
                # Removes the row with htmx
                hx_swap="delete",
            )
        ),
    )


# Sample data
# Often this would come from a database

contacts_initial = [
    {"id": 1, "name": "Bob Deer", "email": "bob@deer.org", "status": "Active"},
    {"id": 2, "name": "Jon Doe", "email": "Jon@doe.com", "status": "Inactive"},
    {"id": 3, "name": "Jane Smith", "email": "jane@smith.com", "status": "Active"},
]


contacts: dict[int, Contact] = {x["id"]: Contact(**x) for x in contacts_initial}


def InputForm():
    return Form(
        Input(name="name", label="Name"),
        Input(name="email", label="Email"),
        Input(name="status", label="Status"),
        Button("Add", type="submit", cls="primary"),
        hx_post="/add",
        hx_target="#contacts-table-body",
        hx_swap="beforeend",
    )


@app.post
def add(name: str, email: str, status: str, sess):
    # Add a new contact
    id = max(contacts.keys()) + 1
    contact = Contact(id=id, name=name, email=email, status=status)
    contacts[id] = contact
    # Add the new contact to the session
    sess["contact_ids"].append(id)
    # Return the updated table
    return ContactTr(contact)


@rt
def index(sess):
    # Save a copy of contacts in your session
    # This is the demo doesn't conflict with other users
    print(sess)
    print(type(sess))
    sess["contact_ids"] = list(contacts.keys())
    # Create initial table

    return Main(
        InputForm(),
        make_table(sess),
    )

    # return make_table(sess)


def make_table(sess):
    return Table(
        Thead(Tr(*map(Th, ["Name", "Email", "Status", ""]))),
        # A `Contact` object is rendered as a row automatically using the `__ft__` method
        Tbody(*(ContactTr(contacts[id]) for id in sess["contact_ids"]), id="contacts-table-body"),
    )


@app.delete
def delete(id: int, sess):
    sess["contact_ids"] = [c for c in sess["contact_ids"] if c != id]


serve()
