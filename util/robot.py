import requests
import time


class Robot(object):
    def __init__(self, api_keys):
        self.apiKeyNo = 0
        self.apiKeys = api_keys
        self.apiUrl = 'http://openapi.tuling123.com/openapi/api/v2'
        self.sendLock = False

    def send(self, text, user_id, group_id):
        elapsedTime = 0
        while self.sendLock:
            time.sleep(1)
            # 判断等待超时
            elapsedTime += 1
            if elapsedTime > 30:
                return None

        self.sendLock = True
        try:
            # 发送消息
            postData = {
                "reqType": 0,
                "perception": {
                    "inputText": {
                        "text": text
                    }
                },
                "userInfo": {
                    "apiKey": self.apiKeys[self.apiKeyNo],
                    "userId": str(user_id),
                    "groupId": str(group_id)
                }
            }
            response = requests.post(self.apiUrl, json=postData).json()

            # 机器人消息达到每日上限，切换机器人
            if response['intent']['code'] == 4003:
                old = self.swiRobot()
                return '%d号因说话过多已累死，现在切换到%d号机器人。' % (old, self.apiKeyNo)

            # 提取消息文本
            if response['intent']['code'] >= 10000:
                for msg in response['results']:
                    if msg['resultType'] == 'text':
                        return msg['values']['text']
            else:
                return '自毁程序已启动，请暂时不要打扰我！'

        except Exception as e:
            raise e
        finally:
            self.sendLock = False

    # 切换机器人
    def swiRobot(self):
        apiKeyNoOld = self.apiKeyNo
        if self.apiKeyNo + 1 >= len(self.apiKeys):
            self.apiKeyNo = 0
        else:
            self.apiKeyNo += 1
        return apiKeyNoOld
