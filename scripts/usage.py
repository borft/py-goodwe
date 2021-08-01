import configparser, psycopg2, psycopg2.extras as extras
from prettytable import PrettyTable
import os

config = configparser.ConfigParser()
config.read(os.path.dirname(__file__) + '/../config.ini')

database = config['database']
username = database['username']
password = database['password']
hostname = database['hostname']
dbname = database['database']

dsn = f"dbname='{dbname}' user='{username}' host='{hostname}' password='{password}'"

try:
    conn = psycopg2.connect(dsn, cursor_factory=extras.DictCursor)
except Exception as e:
    print(f'db is b0rken {e}')
    exit(1)
cur = conn.cursor()

query = """
SELECT
        bar.start,
        bar.end,
        bar.in,
        bar.out,
        bar.in-bar.out as net_usage,
        bar.in - bar.out + s.generation   as consumption,
        s.generation,
        DATE_PART('day', bar.end - bar.start) +1 AS day_count,
        TRUNC(100 * (s.generation - bar.out)  / ( s.generation),2) as own_usage,
        TRUNC(100 * (s.generation - bar.out) / (bar.in - bar.out + s.generation), 2) as self_suff
FROM
        (SELECT
                foo.*,
                foo.in_1+foo.in_2 as in ,
                foo.out_1+foo.out_2 as out
        FROM
                (SELECT
                        MIN(sample) as start,
                        MAX(sample) as end,
                        MAX(kwh_in_1) - MIN(kwh_in_1) as in_1,
                        MAX(kwh_in_2) - MIN(kwh_in_2) as in_2,
                        MAX(kwh_out_1) - MIN(kwh_out_1) as out_1,
                        MAX(kwh_out_2) - MIN(kwh_out_2) as out_2
                FROM
                        electricity
                /* start date of Powerpeers subscription */
                WHERE
                        date(sample) > '2020-12-31'
                GROUP BY
                        to_char(sample, 'YYYY-MM')
                ORDER BY
                        MIN(sample)
                ) as foo
                LEFT JOIN (SELECT
                        MAX(sample) - INTERVAL '1 month' as end,
                        MAX(kwh_in_1) as in_1,
                        MAX(kwh_in_2) as in_2,
                        MAX(kwh_out_1) as out_1,
                        MAX(kwh_out_2) as out_2
                FROM electricity
                WHERE date(sample) > '2020-12-31'
                GROUP BY
                        to_char(sample, 'YYYY-MM')
                ORDER BY MIN(sample)) as prev ON prev.end=foo.end

        ) as bar
        LEFT JOIN (SELECT
                to_char(daily.sample, 'YYYY-MM') AS yearmonth,
                SUM(daily.yield) as generation
                FROM (SELECT
                        MAX(sd.sample) as sample,
                        MAX(sd.yield_today) as yield
                        FROM sems sd
                        WHERE date(sd.sample) > '2020-12-31'
                        GROUP BY DATE(sd.sample)
                ) as daily
                WHERE date(sample) > '2020-12-31'
                GROUP BY
                        to_char(daily.sample, 'YYYY-MM')

                ) as s ON s.yearmonth = to_char(bar.start, 'YYYY-MM')
        ORDER BY bar.start
"""

cur.execute(query)
rows = cur.fetchall()

class MikesPrettyTable (PrettyTable):
    _footer = False

    def add_row(self, row):
        return PrettyTable.add_row(self, [f'{r:.3f}' if type(r) == float else r for r in row])

    def add_footer(self, row):
        self._footer = True
        self.add_row(row)

    def get_string(self, **kwargs):
        lines =  PrettyTable.get_string(self, **kwargs).splitlines()

        if self._footer:
            # means the last line is the footer, so we need to add a separator
            separator = lines[0]
            lines = [*lines[0:-2], separator, *lines[-2:]]

        return '\n'.join(lines)


table = MikesPrettyTable()

footer = {
        'start': None,
        'end': None,
        'in': 0,
        'out': 0,
        'net_usage': 0,
        'consumption': 0,
        'generation': 0,
        'own_usage': 0,
        'self_suff': 0,
        'day_count': 0
        }
panel_power = 26 * .33 + 3 * .305

for r in rows:
    row = r.copy()

    # calculate aggregations
    row['r_prod'] = float(row['generation']) / row['day_count'] / panel_power
    row['r_usage'] = float(row['consumption']) / row['day_count']

    # update totals
    if footer['start'] == None:
        footer['start'] = row['start']
    footer['end'] = row['end']
    footer['in'] += row['in']
    footer['out'] += row['out']
    footer['net_usage'] += row['net_usage']
    footer['consumption'] += row['consumption']
    footer['generation'] += row['generation']
    footer['day_count'] += row['day_count']

    del row['day_count']

    if len(table.field_names) == 0:
        table.field_names = row.keys()

    table.add_row(row=row.values())

footer['own_usage'] = 100 * float(footer['generation'] - footer['out']) / float(footer['generation'])
footer['self_suff'] = 100 * float(footer['generation'] - footer['out']) / float(footer['consumption'])
footer['r_prod'] = float(footer['generation']) / footer['day_count'] / panel_power
footer['r_usage'] = float(footer['consumption']) / footer['day_count']
del footer['day_count']

table.add_footer(footer.values())

print(table)
