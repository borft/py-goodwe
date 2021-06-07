import psycopg2
import psycopg2.extras

class db:

    def __init__(self, config):

        ## setup db connection
        database = config['database']
        username = database['username']
        password = database['password']
        hostname = database['hostname']
        dbname = database['database']

        dsn = f"dbname='{dbname}' user='{username}' host='{hostname}' password='{password}'"
        try:
            self._conn = psycopg2.connect(dsn)
        except:
            print('db is b0rken')
        self._cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def get_cursor(self):
        return self._cur

