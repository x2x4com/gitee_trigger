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

log.set_logger(filename="/tmp/Dingding.log", level='INFO', console=True)

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

    def __init__(self, robot_url):
        self.__is_url(robot_url)
        self.__robot_url = robot_url

    def __get_msgtype_struct(self, msgtype:str):
        if msgtype not in self.__get_all_msgtype():
            raise TypeError("msgtype:%s not in %s" %(msgtype, [x for x in self.__get_all_msgtype()]))
        return self.__robot_api_struct[msgtype].copy()

    def __get_all_msgtype(self):
        return self.__robot_api_struct.keys()

    def __post_data(self, data):
        try:
            ret = requests.post(self.__robot_url, json=data, timeout=30)
        except Exception as e:
            log.error("send data failed, err: %s" % e)
            return None
        log.info(ret.text)
        if ret.status_code == requests.codes.ok:
            log.info('%s 发送成功' % data)
            return True
        log.info('%s 发送失败' % data)
        return False

    @staticmethod
    def __str_not_empty(tester:tuple):
        for a in tester:
            if type(a) == str:
                if len(a) == 0:
                    raise ValueError("Empty not allow")

    @staticmethod
    def __is_url(url:str):
        if url[0:7] == "http://": return
        if url[0:8] == "https://": return
        raise ValueError("Url must start with http:// or https://")

    def add_action_card_btns(self, btns:list, title:str, url:str):
        self.__str_not_empty((title,))
        self.__is_url(url)
        btns.append({"title": title, "actionURL": url})
        return btns

    def send_text(self, msg:str, at_mobiles:list=list(), at_all=False):
        """
        发送text类型的信息

        :param msg: str, 发送的信息主体
        :param at_mobiles: list, 如果主体中包含@手机号码，需要在此列表中给出对应号码(此号码必须是钉钉注册账号，并在群内)
        :param at_all: bool, 是否全体通知
        :return:
        """
        self.__str_not_empty((msg,))
        ds = self.__get_msgtype_struct("text")
        ds["text"]["content"] = msg
        ds["at"]["atMobiles"] = at_mobiles
        ds["at"]["isAtAll"] = at_all
        return self.__post_data(ds)

    def send_link(self, msg:str, title:str, msg_url:str, pic_url:str=""):
        self.__str_not_empty((msg, title))
        self.__is_url(msg_url)
        if pic_url: self.__is_url(pic_url)
        ds = self.__get_msgtype_struct("link")
        ds["link"]["text"] = msg
        ds["link"]["title"] = title
        ds["link"]["messageUrl"] = msg_url
        ds["link"]["picUrl"] = pic_url
        return self.__post_data(ds)

    def send_markdown(self, msg:str, title:str, at_mobiles:list=list(), at_all=False):
        self.__str_not_empty((msg, title))
        ds = self.__get_msgtype_struct("markdown")
        ds["markdown"]["title"] = title
        ds["markdown"]["text"] = msg
        ds["at"]["atMobiles"] = at_mobiles
        ds["at"]["isAtAll"] = at_all
        return self.__post_data(ds)

    def send_action_card_single(self, msg:str, title:str, single_title:str, single_url:str, hide_avatar=False):
        self.__str_not_empty((msg, title, single_title))
        self.__is_url(single_url)
        ds = self.__get_msgtype_struct("actionCardSingle")
        ds["actionCard"]["title"] = title
        ds["actionCard"]["text"] = msg
        ds["actionCard"]["singleTitle"] = single_title
        ds["actionCard"]["singleURL"] = single_url
        if hide_avatar: ds["actionCard"]["hideAvatar"] = "1"
        return self.__post_data(ds)

    def send_action_card_btns(self, msg:str, title:str, btns:list, btn_orientation=False, hide_avatar=False):
        self.__str_not_empty((msg, title))
        ds = self.__get_msgtype_struct("actionCardBtns")
        ds["actionCard"]["title"] = title
        ds["actionCard"]["text"] = msg
        ds["actionCard"]["btns"] = btns
        if hide_avatar: ds["actionCard"]["hideAvatar"] = "1"
        if btn_orientation: ds["actionCard"]["btnOrientation"] = "1"
        return self.__post_data(ds)