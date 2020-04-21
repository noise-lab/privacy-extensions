#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
import datetime
import logging

import psycopg2
import psycopg2.extras

log = logging.getLogger('database')


class Database:
    def __init__(self, host, port, user, password, database, table):
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._table = table
        self._connect()

    def _connect(self):
        try:
            self.conn = psycopg2.connect(host=self._host,
                                         port=self._port,
                                         user=self._user,
                                         password=self._password,
                                         database=self._database)
            psycopg2.extras.register_uuid()
        except Exception as e:
            log.error(f"Error connecting to database: {e}")

        try:
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except Exception as e:
            log.error(f"Error getting cursor from database: {e}")

        self.create()

    def _table_exists(self):
        self._execute_command(f"SELECT to_regclass('{self._table}')")
        rv = self.cursor.fetchone()[0]
        return rv

    @staticmethod
    def init_from_config_file(config_filename, section='postgresql'):
        parser = configparser.ConfigParser()
        parser.read(config_filename)

        params = {}
        if parser.has_section(section):
            for param in parser.items(section):
                params[param[0]] = param[1]

        return Database(host=params['host'],
                        port=params['port'],
                        user=params['user'],
                        password=params['password'],
                        database=params['database'],
                        table=params['table'])

    def _execute_command(self, cmd, format_tuple=None):
        if self.conn.closed:
            self._connect()

        try:
            if format_tuple:
                self.cursor.execute(cmd, format_tuple)
            else:
                self.cursor.execute(cmd)
            self.conn.commit()
        except Exception as e:
            log.error(f"Unable to execute database command {e}")
            self.conn.commit()
            return e
        return None

    def create(self):
        if self._table_exists():
            log.warning(f"Table '{self._table}' already exists, not recreating")
            return

        cmd = \
            f"""CREATE TABLE {self._table} (experiment UUID,
                                            insertion_time TIMESTAMP WITH TIME ZONE,
                                            browser TEXT,
                                            extensions TEXT,
                                            domain TEXT,
                                            har_uuid UUID PRIMARY KEY,
                                            har JSONB,
                                            har_error TEXT DEFAULT NULL)
            """

        rv = self._execute_command(cmd)
        if rv:
            log.error(f"Error creating table '{self._table}': error: {rv}")
        return rv

    def drop(self):
        if not self._table_exists():
            log.error(f"Table '{self._table}' does not exist")
            return

        rv = self._execute_command(f"DROP TABLE {self._table}")
        if rv:
            pass
        return rv

    def insert(self, experiment, browser, extensions, domain,
               har_uuid, har, har_error):
        cmd = \
            f"""INSERT INTO {self._table} (experiment,
                                           insertion_time,
                                           browser,
                                           extensions,
                                           domain,
                                           har_uuid,
                                           har,
                                           har_error)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
        now = datetime.datetime.utcnow()
        har_uuid = psycopg2.extensions.adapt(har_uuid)

        if har:
            tup = (experiment, now, browser, extensions, domain,
                   har_uuid, psycopg2.extras.Json(har), None)
        else:
            tup = (experiment, now, browser, extensions, domain,
                   har_uuid, None, har_error)

        rv = self._execute_command(cmd, tup)
        if rv:
            log.error(f"Error inserting HAR into database: {rv}")
        return rv

    def get_hars(self, extensions, domains):
        domains = tuple(domains)
        cmd = \
            f"""SELECT *
                FROM {self._table}
                WHERE extensions = %s AND domain IN %s
            """

        rv = self._execute_command(cmd, (recursive, dns_type, domains))
        if rv:
            err = 'Error getting HARs from database, error: {}'
            print(err.format(rv))
            return rv
        rv = self.cursor.fetchall()
        return rv

    def get_resources(self, domains, experiments=None):
        cmd = \
            f"""SELECT experiment, extensions, domain, har_uuid
                        (jsonb_extract_path(
                            jsonb_array_elements(
                                jsonb_extract_path(har, 'entries')),
                            'request')->>'url') as url
                FROM {self._table}
                WHERE domain IN %s
            """

        domains = tuple(domains)
        if experiments:
            experiments = tuple(experiments)
            cmd = f"{cmd} AND experiments IN %s"
            rv = self._execute_command(cmd, (domains, experiments))
        else:
            rv = self._execute_command(cmd, (domains,))

        if rv:
            log.error(f"Error getting resources URLs: {rv}")
            return rv

        rv = self.cursor.fetchall()
        return rv

    def get_resource_counts(self, experiments=None):
        cmd = \
            f"""SELECT experiment, extensions, domain, har_uuid,
                    jsonb_array_length(jsonb_extract_path(har, 'entries')) as resources,
                    (jsonb_extract_path(har, 'pages', '0', 'pageTimings')->>'onLoad')::float
                        as pageload
            FROM {self._table}
            """

        if experiments:
            experiments = tuple(experiments)
            cmd = f"{cmd} WHERE experiments IN %s"
            rv = self._execute_command(cmd, (experiments, ))
        else:
            rv = self._execute_command(cmd)

        if rv:
            log.error(f"Error getting resource counts: {rv}")
            return rv

        rv = self.cursor.fetchall()
        return rv

    def get_pageloads(self, domains, experiments=None):
        cmd = \
            f"""SELECT experiment, extensions, domain, har_uuid,
                       jsonb_extract_path(har, 'pages', '0', 'pageTimings')->>'onLoad' as pageload
                FROM {self._table}
                WHERE domain IN %s
            """

        domains = tuple(domains)
        if experiments:
            experiments = tuple(experiments)
            cmd = f"{cmd} AND experiments IN %s"
            rv = self._execute_command(cmd, (domains, experiments))
        else:
            rv = self._execute_command(cmd, (domains,))

        if rv:
            log.error(f"Error getting pageloads: {rv}")
            return rv

        rv = self.cursor.fetchall()
        return rv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('database_config_file')
    parser.add_argument('-d', '--drop', action='store_true')
    parser.add_argument('-c', '--create', action='store_true')
    args = parser.parse_args()

    database = Database.init_from_config_file(args.database_config_file)

    if args.drop:
        database.drop()

    if args.create:
        database.create()

if __name__ == "__main__":
    main()
