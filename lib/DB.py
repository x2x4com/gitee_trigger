#!/usr/bin/env python3
# encoding: utf-8
# ===============================================================================
#
#         FILE:  DB
#
#        USAGE:  ./DB
#
#  DESCRIPTION:  UpdateHook
#
#      OPTIONS:  ---
# REQUIREMENTS:  ---
#         BUGS:  ---
#        NOTES:  ---
#       AUTHOR:  x2x4(x2x4@qq.com)
#      COMPANY:  x2x4
#      VERSION:  1.0
#      CREATED:  2018/10/16 14:49
#     REVISION:  ---
# ===============================================================================
import sqlite3
import MyLog as log
import json
import time

log.set_logger(filename="/tmp/DB.log", level='INFO', console=True)


class StorageSQLite():
    db_file = None
    handle = None

    def __init__(self, db_file):
        self.db_file = db_file
        self.connect()

    def connect(self):
        try:
            self.handle = sqlite3.connect(self.db_file)
        except sqlite3.OperationalError as e:
            RuntimeError("db error: %s" % e)

    def is_empty(self, table):
        try:
            cursor = self.handle.cursor()
            sql = 'select count(*) from sqlite_master where type="table" and name="' + table + '"'
            count = cursor.execute(sql).fetchall()[0][0]
            if count > 0:
                return False
            else:
                return True
        except sqlite3.OperationalError as e:
            RuntimeError("db error: %s" % e)

    def _load_data(self, sql):
        try:
            log.debug("load sql: %s" % sql)
            cursor = self.handle.cursor()
            log.debug("cursor: %s" % cursor)
            data = cursor.execute(sql).fetchall()
            return data
        except sqlite3.OperationalError as e:
            RuntimeError("sqlite error: %s\nsql: %s" % (e, sql))

    def _save_data(self, sql):
        try:
            log.debug("save sql: %s" % sql)
            cursor = self.handle.cursor()
            log.debug("cursor: %s" % cursor)
            data = cursor.execute(sql)
            log.debug("exec: %s" % data)
            self.handle.commit()
        except sqlite3.OperationalError as e:
            RuntimeError("sqlite error: %s\nsql: %s" % (e, sql))


class Storage(StorageSQLite):
    def __init__(self, db_file):
        super().__init__(db_file)
        if self.is_empty("data"):
            sql = 'create table data (id integer primary key, create_time INTEGER, project_id TEXT, commit_hash TEXT, build_tag TEXT, is_success INTEGER, val TEXT)'
            self._save_data(sql)

    def get(self, project_id:str, commit_hash:str):
        sql = 'select build_tag, is_success, val from data where project_id = "%s" and commit_hash = "%s" ' % (project_id, commit_hash)
        data = self._load_data(sql)
        build_tag = is_success = val = None
        if data: build_tag, is_success, val = data[0]
        try:
            val = json.loads(val)
        except Exception as e:
            # log.error("JSON decode error, %s" % e)
            val = None
        return (build_tag, is_success, val)

    def set(self, project_id:str, commit_hash:str, val, build_tag:str=None, is_success:bool=None):
        now = int(time.time())
        build_tag, _is_success, data = self.get(project_id, commit_hash)
        if is_success is not None:
            _is_success = int(is_success)
        else:
            if _is_success:
                _is_success = int(_is_success)
                if _is_success not in [0, 1]:
                    _is_success = 0
            else:
                _is_success = 0
        try:
            val = json.dumps(val)
        except Exception as e:
            log.error("JSON encode error, %s" % e)
            return False
        if data:
            data.update(val)
            sql = 'update data set val = "%s", is_success = "%s"  where project_id = "%s" and commit_hash = "%s"' % (data, _is_success, project_id, commit_hash)
        else:
            if build_tag:
                sql = 'insert into data (create_time, commit_hash, val, build_tag, project_id, is_success) values ("%s", "%s", \'%s\', "%s" , "%s", "%s")' % (now, commit_hash, val, build_tag, project_id, is_success)
            else:
                sql = 'insert into data (create_time, commit_hash, val, project_id, is_success) values ("%s", "%s", \'%s\', "%s", "%s")' % (now, commit_hash, val, project_id, is_success)
        self._save_data(sql)
        return True


