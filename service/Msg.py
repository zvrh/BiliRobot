import time
import json
import requests
from service.Service import Service
from util.Config import Config
from util.Log import Log
from util.Msg import Msg
from util.Robot import Robot


class MsgService(Service):

    def __init__(self):
        # 初始化变量
        self.config = Config()
        self.cookies = self.config.getCookies()

        self.log = Log('service/Msg')
        self.msg = Msg(self.cookies)
        self.robot = Robot(self.config.get('api_keys'))

        self.uid = int(self.cookies['DedeUserID'])
        self.admin_ids = self.config.get('admin_ids')
        self.receiver_ids = self.config.get('receiver_ids')
        self.cookies_str = self.config.get('cookies')
        self.userList = {}
        self.groupList = {}

        self.is_private = self.config.get('is_private')
        # self.msg.send('start')

    def run(self):
        # self.parseMsg()
        # time.sleep(2)
        try:
            self.parseMsg()
            time.sleep(2)
        except Exception as e:
            self.log.error(e)

    # 解析消息
    def parseMsg(self):
        msgList = self.msg.get()
        for msg in msgList:
            self.log.debug(msg)
            # 私信
            if msg['receiver_type'] == 1:
                if msg['msg_type'] == 1:
                    text = json.loads(msg['content'])['content'].lstrip()
                    self.handler(text, msg['sender_uid'], 0)
                pass
            # 应援团
            elif msg['receiver_type'] == 2:
                if (0 in self.receiver_ids or int(msg['receiver_id'] in self.receiver_ids)) \
                        and msg['msg_type'] == 1:
                        # 检测并处理@
                        text = json.loads(msg['content'])['content'].lstrip()
                        if text.find('@' + self.getUserName(self.uid)) != -1:
                            text = text.replace('\u0011', '')  # IOS客户端的@前后有这两个控制字符
                            text = text.replace('\u0012', '')
                            text = text.replace('@' + self.getUserName(self.uid), '').lstrip()
                            if 'at_uids' in msg and self.uid in msg['at_uids']:
                                self.handler(text, msg['sender_uid'], msg['receiver_id'])
                            else:
                                self.handler('#冒泡', 0, msg['receiver_id'])
                pass
        pass

    # 消息处理函数
    def handler(self, text, user_id, group_id):
        if group_id not in self.groupList:
            self.getGroupDetail(group_id)
        ot = ''
        # 命令
        if text.find('#') == 0 and \
                (user_id == self.groupList[group_id]['admin'] or user_id in self.admin_ids or user_id == 0):
                text = text[1:]
                if user_id == 0:
                    if text == '冒泡':
                        ot = '敢不敢长按我的头像试试？'
                elif user_id in self.admin_ids:
                    if text == '切换':
                        old = self.robot.swiRobot()
                        ot = '已从%d号切换到%d号（我比前一位聪明哦~）' % (old, self.robot.apiKeyNo)
                #
                if text == '睡觉':
                    self.groupList[group_id]['off'] = 1
                    ot = '已准备睡觉，各位晚安~'
                elif text == '醒醒':
                    self.groupList[group_id]['off'] = 0
                    ot = '又是全新的一天，早安！'
                if ot == '':
                    ot = '对方不想理你，并抛出了个未知的异常(◔◡◔)'
        # 聊天
        else:
            # 私信关闭状态
            if group_id == 0 and self.is_private == 0:
                return
            # 睡觉
            if self.groupList[group_id]['off'] == 1:
                return
            if text == '':
                text = '?'
            # 转发消息给机器人
            self.log.success('[in][%s][%s] %s' % (self.groupList[group_id]['name'], self.getUserName(user_id), text))
            ot = self.robot.send(text, user_id, group_id)
            self.log.success('[out][%s][%s] %s' % (self.groupList[group_id]['name'], self.getUserName(user_id), ot))
        # 回复
        # 私信
        if group_id == 0:
            self.msg.send(ot, user_id, receiver_type=1)
        # 群聊
        else:
            if user_id == 0:
                self.msg.send(ot, group_id, receiver_type=2)
            else:
                self.msg.send('@%s %s' % (self.getUserName(user_id), ot), group_id, receiver_type=2, at_uid=user_id)

    # 获取用户名 uid -> 昵称
    def getUserName(self, user_id):
        # 每300s（5min）更新一次昵称
        if user_id not in self.userList or self.userList[user_id][1] - int(time.time()) > 300:
            url = 'http://api.live.bilibili.com/user/v2/User/getMultiple'
            postData = {
                'uids[0]': user_id,
                'attributes[0]': 'info',
                'csrf_token': self.msg.cookies['bili_jct']
            }
            response = requests.post(url, data=postData, cookies=self.cookies).json()
            self.log.debug('[查询用户]'+str(response))
            self.userList[user_id] = [response['data'][str(user_id)]['info']['uname'], int(time.time())]
        return self.userList[user_id][0]

    # 获取群信息 群主&勋章名(替代群名)
    def getGroupDetail(self, group_id):
        if group_id not in self.groupList:
            if group_id == 0:
                self.groupList[group_id] = {
                    'admin': 0,
                    'name': '私信',
                    'off': 0
                }
            else:
                url = 'https://api.vc.bilibili.com/link_group/v1/group/detail?group_id=%s' % str(group_id)
                response = requests.get(url).json()
                self.log.debug('[查询群]'+str(response))
                self.groupList[group_id] = {
                    'admin': response['data']['owner_uid'],
                    'name': response['data']['fans_medal_name'],
                    'off': 0
                }
