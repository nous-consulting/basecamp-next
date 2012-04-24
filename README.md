Python Wrapper for Basecamp Next
================================

First, you need to ask user's permission to access her data:

    from basceampx.auth import Auth
    auth = Auth('clientid', 'clientsecret', 'http://redirecturl')
    auth.authorize_url()

After user grants you access, get the access token:

    token = auth.access_token(code)['access_token']

Find the accounts that this user has:

    from basecampx import Client
    client = Client(token, 'YourAppName')
    accounts = client.accounts()

Use a user's Basecamp Next account to access data in projects:

    bcx_accounts = filter(lambda a: a['product'] == 'bcx', accounts['accounts'])
    client = Client(token, 'YourAppName', bcx_accounts[0]['id'])

    from basecampx import Projects
    projects = Projects(client)
    project_list = projects.list()
    project_names = [project['name'] for project in project_list]
