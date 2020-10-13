from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import ProgrammingError
# from psycopg2 import ProgrammingError
from psycopg2.extensions import AsIs
from datetime import datetime, timedelta
from django.conf import settings


class Command(BaseCommand):
    '''
    CREATE [MAX_PARTITIONS] sequential from current date.

    '''
    MAX_PARTITIONS = 15

    def add_arguments(self, parser):
        # parser.add_argument(
        #     '--startdate',
        #     default=((datetime.now() + timedelta(days=LEAD_DAYS)).strftime(
        #         "%Y-%m-%d"),
        #     help="date for first partition, default today"
        # )
        parser.add_argument(
            '--num_partitions',
            default=self.MAX_PARTITIONS,
            help="number of sequential partitions to maintain"
        )

    def select_latest_partition(self):
        '''find the lastest partition and return table name as strings
        '''
        sql = '''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name like 'measurement_measurement_%'
            ORDER BY table_name
            LIMIT 1;'''
        with connection.cursor() as cursor:
            cursor.execute(sql)
            table = cursor.fetchone()
            if table is None:
                return table
            return table[0]

    def parse_partition_date(self, table_name):
        '''extract date from table name and return datetime object'''
        date_string = table_name.replace('measurement_measurement_', '')
        date = datetime.strptime(date_string, '%Y_%m_%d')
        return date

    def handle(self, *args, **options):
        '''method called by manager'''

        '''the TableMaker2500Max'''
        sql = '''CREATE TABLE measurement_measurement_%s_%s_%s
                PARTITION OF measurement_measurement
                FOR VALUES FROM (%s) TO (%s);'''

        latest_partition = self.select_latest_partition()
        if latest_partition is None:
            latest_partition_date = datetime.now()
            print("nope")
        else:
            latest_partition_date = self.parse_partition_date(latest_partition)
        partition_start_date = latest_partition_date
        print(latest_partition)
        # how many partitions beyond last_partition do we create????
        num_partitions = self.MAX_PARTITIONS - \
            (latest_partition_date - datetime.now()).days

        with connection.cursor() as cursor:
            sql = '''CREATE TABLE measurement_measurement_%s_%s_%s
                PARTITION OF measurement_measurement
                FOR VALUES FROM (%s) TO (%s);'''

            for i in range(num_partitions):
                partition_end_date = partition_start_date + timedelta(days=1)
                try:
                    # NOTE: AsIS required for formating table names

                    cursor.execute(sql, [
                        AsIs(partition_start_date.strftime("%Y")),
                        AsIs(partition_start_date.strftime("%m")),
                        AsIs(partition_start_date.strftime("%d")),
                        partition_start_date.strftime("%Y-%m-%d"),
                        partition_end_date.strftime("%Y-%m-%d")
                    ])
                except ProgrammingError as e:
                    print(e)
                finally:
                    # run grant in case where partition is created but not 
                    # ganted
                    sql_grant = '''GRANT ALL PRIVILEGES
                        ON TABLE measurement_measurement_%s_%s_%s
                        TO %s; '''

                    cursor.execute(sql_grant, [
                        AsIs(partition_start_date.strftime("%Y")),
                        AsIs(partition_start_date.strftime("%m")),
                        AsIs(partition_start_date.strftime("%d")),
                        AsIs(settings.DATABASES['default']['USER'])])
                    partition_start_date += timedelta(days=1)