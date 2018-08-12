import json


class Config:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = None
        self.reload()

    # 获取格式化的Cookies
    def get_cookies(self):
        cookies = self.get('cookies')
        return dict([l.split("=", 1) for l in cookies.split("; ")])

    # 获取配置项
    def get(self, key, module=''):
        if module == '':
            return self.config.get(key)
        else:
            return self.config.get(module, {}).get(key)

    # 设置配置项
    def set(self, key, value, module=''):
        if module == '':
            self.config[key] = value
        else:
            if module in self.config:
                self.config[module][key] = value
            else:
                self.config[module] = {
                    key: value
                }
        with open(self.config_path, 'w') as f:
            json.dump(obj=self.config, fp=f, ensure_ascii=False, indent=4)

    # 从文件中读取配置对象
    def reload(self):
        with open(self.config_path, encoding='utf-8') as f:
            self.config = json.load(f)
