import json
import requests
from mimetypes import guess_type


class BasecampError(Exception):
    pass


class Client(object):

    LAUNCHPAD_URL = 'https://launchpad.37signals.com'
    BASE_URL = 'https://basecamp.com/%s/api/v1'

    def __init__(self, access_token, user_agent, account_id=None):
        """Initialize client for making requests.

        user_agent -- string identifying the app, and an url or email related
        to the app; e.g. "BusyFlow (http://busyflow.com)".
        """
        self.account_id = account_id
        self.session = requests.session(
                headers={'User-Agent': user_agent,
                         'Authorization': 'Bearer %s' % access_token,
                         'Content-Type': 'application/json; charset=utf-8'})

    def accounts(self):
        url = '%s/authorization.json' % self.LAUNCHPAD_URL
        return self.session.get(url).content


class Endpoint(object):

    def __init__(self, client):
        self.client = client

    def qualified_url(self, url):
        assert self.client.account_id is not None, \
                "Pass an account id to the Client to make this request!"
        return '%s/%s.json' % (self.client.BASE_URL % self.client.account_id, url)

    def _get(self, url, params={}):
        resp = self.client.session.get(self.qualified_url(url),
                params=params)
        if resp.status_code != 200:
            raise BasecampError(resp.status_code)
        return json.loads(resp.content)

    def _post(self, url, data={}, expect=201, mimetype=None):
        if type(data) is not dict:
            resp = self.client.session.post(self.qualified_url(url),
                    data, headers={'Content-Type': mimetype})
        else:
            resp = self.client.session.post(self.qualified_url(url),
                    json.dumps(data))
        if resp.status_code != expect:
            raise BasecampError(resp.status_code)
        if resp.content:
            return json.loads(resp.content)

    def _put(self, url, data={}, expect=200):
        resp = self.client.session.put(self.qualified_url(url),
                json.dumps(data))
        if resp.status_code != expect:
            raise BasecampError(resp.status_code)
        if resp.content:
            return json.loads(resp.content)

    def _delete(self, url):
        resp = self.client.session.delete(self.qualified_url(url))
        if resp.status_code != 204:
            raise BasecampError(resp.status_code)


class ProjectEndpoint(Endpoint):
    """A thing that can only be inside a project.
    E.g. messages, todos, comments etc.
    """

    SECTION_URL = 'projects'

    def __init__(self, client, project_id):
        super(ProjectEndpoint, self).__init__(client)
        self.project_id = project_id

    def qualified_url(self, url):
        return super(ProjectEndpoint, self).qualified_url('%s/%s/%s' % (
            Projects.SECTION_URL, self.project_id, url))

    def delete(self, item_id):
        return self._delete('%s/%s' % (self.SECTION_URL, item_id))


class Projects(Endpoint):

    SECTION_URL = 'projects'

    def list(self, archived=False):
        if archived:
            return self._get('%s/archived' % self.SECTION_URL)
        return self._get(self.SECTION_URL)

    def get(self, project_id):
        return self._get('%s/%s' % (self.SECTION_URL, project_id))

    def post(self, name, description=None):
        return self._post(self.SECTION_URL,
                {'name': name,
                 'description': description})

    def update(self, project_id, name, description=None):
        return self._put('%s/%s' % (self.SECTION_URL, project_id),
                {'name': name,
                 'description': description})

    def archive(self, project_id, archived=True):
        return self._put('%s/%s' % (self.SECTION_URL, project_id),
                {'archived': archived})

    def activate(self, project_id):
        return self.archive(project_id, False)

    def delete(self, project_id):
        return self._delete('%s/%s' % (self.SECTION_URL, project_id))

    def accesses(self, project_id):
        return self._get('%s/%s/accesses' % (self.SECTION_URL, project_id))

    def grant_access(self, project_id, ids=[], emails=[]):
        if not ids and not emails:
            return
        return self._post('%s/%s/accesses' % (self.SECTION_URL, project_id),
                {'ids': ids, 'email_addresses': emails}, expect=204)

    def revoke_access(self, project_id, person_id):
        return self._delete('%s/%s/accesses/%s' %
                (self.SECTION_URL, project_id, person_id))


class People(Endpoint):

    SECTION_URL = 'people'

    def list(self):
        return self._get(self.SECTION_URL)

    def get(self, person_id=None):
        if not person_id:
            return self._get('%s/me' % self.SECTION_URL)
        return self._get('%s/%s' % (self.SECTION_URL, person_id))

    def assigned_todos(self, person_id=None):
        return self._get('%s/%s/assigned_todos' % \
                (self.SECTION_URL, person_id))

    def delete(self, person_id):
        return self._delete('%s/%s' % (self.SECTION_URL, person_id))


class Events(Endpoint):

    SECTION_URL = 'events'
    PAGE_SIZE = 50

    def list(self, project_id=None, since=None):
        """List either all events available to the user, or events
        from a specific project only. If the 'since' parameter is
        given, only list newer events.
        """
        if since is not None:
            since = since.isoformat()

        url = self.SECTION_URL
        if project_id is not None:
            url = '%s/%s/%s' % (Projects.SECTION_URL, project_id, self.SECTION_URL)

        page = 1
        while True:
            events = self._get(url, params={'page': page, 'since': since})
            for event in events:
                yield event
            if len(events) < self.PAGE_SIZE:
                break
            page += 1


class Attachments(Endpoint):

    SECTION_URL = 'attachments'
    PAGE_SIZE = 50

    def list(self, project_id):
        page = 1
        while True:
            attachments = self._get('%s/%s/%s' %
                    (Projects.SECTION_URL, project_id, self.SECTION_URL),
                    params={'page': page})
            for attachment in attachments:
                yield attachment
            if len(attachments) < self.PAGE_SIZE:
                break
            page += 1

    def upload(self, f, mimetype=None):
        """Upload a file to Basecamp.
        """
        guessed_type = (guess_type(f.name)[0]
                if mimetype is None else mimetype)
        return self._post(self.SECTION_URL,
                f.read(),
                mimetype=guessed_type if guessed_type else 'text/plain',
                expect=200)


class Topics(ProjectEndpoint):

    SECTION_URL = 'topics'
    PAGE_SIZE = 50

    def list(self):
        """List all topics available in a given project.
        """
        page = 1
        while True:
            topics = self._get(self.SECTION_URL, params={'page': page})
            for topic in topics:
                yield topic
            if len(topics) < self.PAGE_SIZE:
                break
            page += 1


class Messages(ProjectEndpoint):

    SECTION_URL = 'messages'

    def get(self, message_id):
        return self._get('%s/%s' % (self.SECTION_URL, message_id))

    def post(self, subject, content=None, attachments=None):
        """Post a new message.
        Attachments must be a list with one or more dicts.
        """
        return self._post(self.SECTION_URL,
                {'subject': subject,
                 'content': content,
                 'attachments': attachments})

    def update(self, message_id, subject=None, content=None, attachments=None):
        return self._put('%s/%s' % (self.SECTION_URL, message_id),
                {'subject': subject,
                 'content': content,
                 'attachments': attachments})


class Comments(ProjectEndpoint):

    SECTION_URL = 'comments'

    def post(self, section, topic_id, content, attachments=None):
        return self._post('%s/%s/%s' % (section, topic_id, self.SECTION_URL),
                {'content': content,
                 'attachments': attachments})


class TodoLists(ProjectEndpoint):

    SECTION_URL = 'todolists'

    def list(self, completed=False):
        if completed:
            return self._get('%s/completed' % self.SECTION_URL)
        return self._get(self.SECTION_URL)

    def get(self, todolist_id):
        return self._get('%s/%s' % (self.SECTION_URL, todolist_id))

    def post(self, name, description=None):
        return self._post(self.SECTION_URL,
                {'name': name,
                 'description': description})

    def update(self, todolist_id, name, description=None, position=None):
        return self._put('%s/%s' % (self.SECTION_URL, todolist_id),
                {'name': name,
                 'description': description,
                 'position': position})


class Todos(ProjectEndpoint):

    SECTION_URL = 'todos'

    def get(self, todo_id):
        return self._get('%s/%s' % (self.SECTION_URL, todo_id))

    def post(self, todolist_id, todo_dict):
        """Fields accepted in the dict are:
        - content,
        - due_at,
        - assignee dict (with id and type fields).
        """
        return self._post('%s/%s/%s' %
                (TodoLists.SECTION_URL, todolist_id, self.SECTION_URL),
                todo_dict)

    def update(self, todo_id, todo_dict):
        """Fields accepted (apart from fields defined in post):
        - completed,
        - position.
        """
        return self._put('%s/%s' % (self.SECTION_URL, todo_id), todo_dict)


class Documents(ProjectEndpoint):

    SECTION_URL = 'documents'

    def list(self):
        return self._get(self.SECTION_URL)

    def get(self, document_id):
        return self._get('%s/%s' % (self.SECTION_URL, document_id))

    def post(self, title, content=None):
        return self._post(self.SECTION_URL,
                {'title': title,
                 'content': content})

    def update(self, document_id, title, content=None):
        return self._put('%s/%s' % (self.SECTION_URL, document_id),
                {'title': title,
                 'content': content})


class Uploads(ProjectEndpoint):

    SECTION_URL = 'uploads'

    def get(self, upload_id):
        return self._get('%s/%s' % (self.SECTION_URL, upload_id))

    def post(self, attachments, content=None):
        """Create a new file in the uploaded file section.

        attachments -- a list of dicts containing an attachment
        token and a file name.
        """
        return self._post(self.SECTION_URL,
                {'content': content,
                 'attachments': attachments})


class Calendars(Endpoint):

    SECTION_URL = 'calendars'

    def list(self):
        return self._get(self.SECTION_URL)

    def get(self, calendar_id):
        return self._get('%s/%s' % (self.SECTION_URL, calendar_id))

    def create(self, name):
        return self._post(self.SECTION_URL, {'name': name})

    def update(self, calendar_id, name):
        return self._put('%s/%s' % (self.SECTION_URL, calendar_id),
                {'name': name}, expect=204)

    def delete(self, calendar_id):
        return self._delete('%s/%s' % (self.SECTION_URL, calendar_id))


class CalendarEvents(Endpoint):

    SECTION_URL = 'calendar_events'

    def __init__(self, client, project_id=None, calendar_id=None):
        super(CalendarEvents, self).__init__(client)
        assert not project_id or not calendar_id, \
                "Only give project id or calendar id, not both!"
        if project_id:
            self.parent_section = Projects.SECTION_URL
            self.parent_id = project_id
        else:
            self.parent_section = Calendars.SECTION_URL
            self.parent_id = calendar_id

    def qualified_url(self, url):
        return super(CalendarEvents, self).qualified_url('%s/%s/%s' % (
            self.parent_section, self.parent_id, url))

    def list(self, past=False):
        if past:
            return self._get('%s/past' % self.SECTION_URL)
        return self._get(self.SECTION_URL)

    def get(self, event_id):
        return self._get('%s/%s' % (self.SECTION_URL, event_id))

    def create(self, event_dict):
        """Create an event on Basecamp.
        Event dictionary can contain:
        - summary,
        - description,
        - all_day (boolean),
        - starts_at,
        - ends_at.
        """
        return self._post(self.SECTION_URL, event_dict)

    def update(self, event_id, event_dict):
        return self._put('%s/%s' % (self.SECTION_URL, event_id),
                event_dict)

    def delete(self, event_id):
        return self._delete('%s/%s' % (self.SECTION_URL, event_id))
