from alice.helper.constants  import *

class CommonUtils(object):
    @staticmethod
    def getSlackNicksFromGitNicks(key):
        if key in CommonUtils.git_mappings:
            return CommonUtils.git_mappings[key]
        return key
    
    @staticmethod
    def getGithubUsers():
        users = []
        for page in range(1,4):
            users += json.loads(requests.get(GITHUB_USER_LIST+str(page), headers = {"Authorization": "token "+GITHUB_TOKEN}).content)
        u={}
        for item in users:
            u[item["login"]] = item["login"]
        return u
    
    @staticmethod
    def getSlackUsers():
        users = json.loads(requests.get(SLACK_USER_LIST+SLACK_TOKEN).content)
        u={}
        for item in users["members"]:
            u[item["name"]] = item["name"]
        print json.dumps(u)
