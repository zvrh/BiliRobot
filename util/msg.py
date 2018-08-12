import requests
import json
import time


class Msg(object):
    def __init__(self, cookies):
        # 初始化变量
        self.cookies = cookies
        self.client_seq_no = 0
        self.httpConfig = {
            'getUrl': 'http://api.vc.bilibili.com/web_im/v1/web_im/fetch_msg',
            'sendUrl': 'http://api.vc.bilibili.com/web_im/v1/web_im/send_msg',
            'unreadUrl': 'http://api.vc.bilibili.com/web_im/v1/web_im/unread_msgs'
        }
        self.sendLock = False

    # 获取消息
    def get(self):
        # 获取最新消息编号
        if self.client_seq_no == 0:
            r = requests.get(self.httpConfig['unreadUrl'], cookies=self.cookies).json()
            self.client_seq_no = r['data']['latest_seqno']

        # 读取消息
        postData = {
            'client_seqno': self.client_seq_no,
            'msg_count': 100,
            'uid': self.cookies['DedeUserID'],
            'csrf_token': self.cookies['bili_jct']
        }
        response = requests.post(self.httpConfig['getUrl'], data=postData,
                                 cookies=self.cookies).json()
        msgList = []
        if 'messages' in response['data']:
            self.client_seq_no = response['data']['max_seqno']
            for msg in response['data']['messages']:
                msgList.append(msg)
        return msgList

    # 发送消息
    def send(self, text, receiver_id, receiver_type=1, at_uid=None):
        elapsedTime = 0
        while self.sendLock:
            time.sleep(1)
            # 判断等待超时
            elapsedTime += 1
            if elapsedTime > 30:
                return None

        self.sendLock = True
        try:
            # 准备数据
            content = json.dumps({'content': text}, ensure_ascii=False)
            postData = {
                'msg[receiver_type]': receiver_type,            # 聊天类型 1:私信 2:群聊
                'msg[receiver_id]': receiver_id,                # 接收者id
                'msg[msg_type]': 1,                             # 消息类型 1:文本
                'msg[content]': content,                        # 正文
                'msg[timestamp]': int(time.time()),             # 时间戳
                'msg[sender_uid]': self.cookies['DedeUserID'],  # 发送者id
                'csrf_token': self.cookies['bili_jct']          # csrf_token
            }
            if at_uid:
                postData['msg[at_uids][0]'] = at_uid
            # 发送请求
            response = requests.post(self.httpConfig['sendUrl'], data=postData,
                                     cookies=self.cookies).json()
            return 'code' in response and response['code'] == 0
        except Exception as e:
            raise e
        finally:
            self.sendLock = False
