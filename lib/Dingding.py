#!/usr/bin/env python3
# encoding: utf-8
# ===============================================================================
#
#         FILE:  Dingding
#
#        USAGE:  ./Dingding
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
#      CREATED:  2018/10/14 20:43
#     REVISION:  ---
# ===============================================================================

import requests
import MyLog as log
import time
import hmac
import hashlib
import base64
import urllib.parse
from .DB import StorageSQLite
import json

log.set_logger(filename="/tmp/Dingding.log", level='INFO', console=True)


class NoStorage(object):
    def save(self, msg_from, msg_type, payload, ret):
        pass


class Storage(StorageSQLite):
    def __init__(self, db_file, check_same_thread=False):
        super().__init__(db_file, check_same_thread)
        if self.is_empty("dingding"):
            sql = 'create table dingding (' \
                  'id integer primary key, ' \
                  'create_time INTEGER, ' \
                  'msg_from TEXT, ' \
                  'msg_type TEXT, ' \
                  'is_success INTEGER, ' \
                  'payload TEXT, ' \
                  'ret TEXT)'
            self._save_data(sql)

    def save(self, msg_from, msg_type, payload, ret):
        now = int(time.time())
        try:
            decode_ret = json.loads(ret)
            if 'errcode' in decode_ret and decode_ret['errcode'] == 0:
                is_success = 1
            else:
                is_success = 0
        except json.JSONDecodeError:
            is_success = 0
        sql = 'insert into dingding ' \
              '(create_time, msg_from, msg_type, is_success, payload, ret) values ' \
              '("%s", "%s", "%s", "%s", \'%s\', \'%s\')' % (
               now, msg_from, msg_type, is_success, json.dumps(payload), ret
              )
        # log.info(sql)
        self._save_data(sql)


class DRobot(object):
    """
    简单的钉钉机器人客户端，主要用于消息通知

    目前只支持 text, link, markdown, actionCard(singleTitle)

    """
    __robot_api_struct = {
        "text": {
            "msgtype": "text",
            "text": {
                "content": ""
            },
            "at": {
                "atMobiles": [],
                "isAtAll": False
            }
        },
        "link": {
            "msgtype": "link",
            "link": {
                "text": "",
                "title": "",
                "picUrl": "",
                "messageUrl": ""
            }
        },
        "markdown": {
            "msgtype": "markdown",
            "markdown": {
                "title": "",
                "text": ""
            },
            "at": {
                "atMobiles": [],
                "isAtAll": False
            }
        },
        "actionCardSingle": {
            "msgtype": "actionCard",
            "actionCard": {
                "title": "",
                "text": "",
                "singleTitle": "",
                "singleURL": "",
                "btnOrientation": "0",
                "hideAvatar": "0"
            }
        },
        "actionCardBtns": {
            "msgtype": "actionCard",
            "actionCard": {
                "title": "",
                "text": "",
                "btns": [],
                "btnOrientation": "0",
                "hideAvatar": "0"
            }
        }
    }

    def __init__(self, robot_url, is_sign=False, token=None, secret=None, db_file=None, check_same_thread=False):
        self.__is_url(robot_url)
        self.__robot_url = robot_url
        if is_sign:
            if token is None or secret is None:
                raise RuntimeError("Sign mode is enable, please define token and secret")
            self.__robot_url = 'https://oapi.dingtalk.com/robot/send'
        self.__token = token
        self.__secret = secret
        self.__is_sign = is_sign
        if db_file is not None:
            self.__db = Storage(db_file, check_same_thread=check_same_thread)
        else:
            self.__db = NoStorage()

    def __get_msgtype_struct(self, msgtype:str):
        if msgtype not in self.__get_all_msgtype():
            raise TypeError("msgtype:%s not in %s" %(msgtype, [x for x in self.__get_all_msgtype()]))
        return self.__robot_api_struct[msgtype].copy()

    def __get_all_msgtype(self):
        return self.__robot_api_struct.keys()

    def __sign(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.__secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.__secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        # sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return timestamp, sign

    def __post_data(self, data):
        _url = self.__robot_url
        try:
            if self.__is_sign:
                _timestamp, _sign = self.__sign()
                _params = {
                    'access_token': self.__token,
                    'timestamp': _timestamp,
                    'sign': _sign
                }
                # log.info(_params)
                ret = requests.post(_url, params=_params, json=data, timeout=30)
            else:
                ret = requests.post(_url, json=data, timeout=30)
        except Exception as e:
            log.error("send data failed, err: %s" % e)
            return None
        # log.info(ret.text)
        # if ret.status_code == requests.codes.ok:
        #     log.info('%s 发送成功' % data)
        #     return True
        # log.info('%s 发送失败' % data)
        # return False
        return ret.text

    @staticmethod
    def __str_not_empty(tester: tuple):
        for a in tester:
            if type(a) == str:
                if len(a) == 0:
                    raise ValueError("Empty not allow")

    @staticmethod
    def __is_url(url: str):
        if url[0:7] == "http://":
            return
        if url[0:8] == "https://":
            return
        raise ValueError("Url must start with http:// or https://")

    def add_action_card_btns(self, btns: list, title: str, url: str):
        self.__str_not_empty((title,))
        self.__is_url(url)
        btns.append({"title": title, "actionURL": url})
        return btns

    def send_text(self, msg: str, at_mobiles: list=(), at_all=False, msg_from='default'):
        """
        发送text类型的信息

        :param msg: str, 发送的信息主体
        :param at_mobiles: list, 如果主体中包含@手机号码，需要在此列表中给出对应号码(此号码必须是钉钉注册账号，并在群内)
        :param at_all: bool, 是否全体通知
        :param msg_from: str, 消息来源
        :return:
        """
        self.__str_not_empty((msg,))
        ds = self.__get_msgtype_struct("text")
        ds["text"]["content"] = msg
        ds["at"]["atMobiles"] = at_mobiles
        ds["at"]["isAtAll"] = at_all
        rt = self.__post_data(ds)
        self.__db.save(msg_type='text', msg_from=msg_from, payload=ds, ret=rt)
        return rt

    def send_link(self, msg: str, title: str, msg_url: str, pic_url: str="", msg_from='default'):
        self.__str_not_empty((msg, title))
        self.__is_url(msg_url)
        if pic_url: self.__is_url(pic_url)
        ds = self.__get_msgtype_struct("link")
        ds["link"]["text"] = msg
        ds["link"]["title"] = title
        ds["link"]["messageUrl"] = msg_url
        ds["link"]["picUrl"] = pic_url
        rt = self.__post_data(ds)
        self.__db.save(msg_type='link', msg_from=msg_from, payload=ds, ret=rt)
        return rt

    def send_markdown(self, msg: str, title: str, at_mobiles: list=(), at_all=False, msg_from='default'):
        self.__str_not_empty((msg, title))
        ds = self.__get_msgtype_struct("markdown")
        ds["markdown"]["title"] = title
        ds["markdown"]["text"] = msg
        ds["at"]["atMobiles"] = at_mobiles
        ds["at"]["isAtAll"] = at_all
        rt = self.__post_data(ds)
        self.__db.save(msg_type='markdown', msg_from=msg_from, payload=ds, ret=rt)
        return rt

    def send_action_card_single(
            self,
            msg: str,
            title: str,
            single_title: str,
            single_url: str,
            hide_avatar=False,
            msg_from='default'
    ):
        self.__str_not_empty((msg, title, single_title))
        self.__is_url(single_url)
        ds = self.__get_msgtype_struct("actionCardSingle")
        ds["actionCard"]["title"] = title
        ds["actionCard"]["text"] = msg
        ds["actionCard"]["singleTitle"] = single_title
        ds["actionCard"]["singleURL"] = single_url
        if hide_avatar:
            ds["actionCard"]["hideAvatar"] = "1"
        rt = self.__post_data(ds)
        self.__db.save(msg_type='actionCardSingle', msg_from=msg_from, payload=ds, ret=rt)
        return rt

    def send_action_card_btns(
            self,
            msg: str,
            title: str,
            btns: list,
            btn_orientation=False,
            hide_avatar=False,
            msg_from='default'
    ):
        self.__str_not_empty((msg, title))
        ds = self.__get_msgtype_struct("actionCardBtns")
        ds["actionCard"]["title"] = title
        ds["actionCard"]["text"] = msg
        ds["actionCard"]["btns"] = btns
        if hide_avatar:
            ds["actionCard"]["hideAvatar"] = "1"
        if btn_orientation:
            ds["actionCard"]["btnOrientation"] = "1"
        rt = self.__post_data(ds)
        self.__db.save(msg_type='actionCardBtns', msg_from=msg_from, payload=ds, ret=rt)
        return rt
