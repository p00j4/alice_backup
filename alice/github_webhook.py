from flask import Flask, request, jsonify, abort
import logging
from logging.handlers import RotatingFileHandler
from alice.helper.constants  import *
import requests
#from flask import app as application
import simplejson as json
from alice.helper.common_utils import CommonUtils

application = Flask(__name__)

@application.route("/", methods=['GET','POST'])
def hello():
    return "Welcome to the world of Alice"


class PushPayload():
    API_START_PR = "https://api.github.com/repos/moengage/MoEngage/pulls/"
    API_START_ISSUES = "https://api.github.com/repos/moengage/MoEngage/issues/"
    EP_REVIEWS = "reviews"
    EP_COMMENTS = "comments"
    STATE_OPEN = "open"
    STATE_CLOSED = "closed"
    PROTECTED_BRANCH_LIST = ["dev", "qa", "master"]

    def __init__(self, request, payload):
        self.request = request
        self.payload = payload
        self.pr = payload["pull_request"]

    @property
    def merged_by(self):
        return self.pr["merged_by"]["login"]
    
    @property
    def pr_link_pretty(self):
        return self.pr["html_url"]

    @property
    def pr_link(self):
        return self.pr["url"]

    @property
    def pr_by(self):
        return self.pr["user"]["login"]

    @property
    def is_merged(self):
        return self.pr["merged"]

    @property
    def action(self):
        return self.payload["action"]

    @property
    def repo(self):
        return self.payload["repository"]["name"]#self.data["head"]["repo"]["name"]

    @property
    def base_branch(self):
        return self.pr["base"]["ref"]

    @property
    def head_branch(self):
        return self.pr["head"]["ref"]

    def was_eligible_to_merge(self):
        merged_by_slack_nick = CommonUtils.getSlackNicksFromGitNicks(self.merged_by)
        pr_by_slack_nick = CommonUtils.getSlackNicksFromGitNicks(self.pr_by)

        if self.is_merged: #and self.head_branch in PushPayload.PROTECTED_BRANCH_LIST:  TO ENABLE
            is_bad_pr = self.getReviewes(pr_by_slack_nick)
            return "{msg} repo:{repo}".format(repo=self.repo, msg=is_bad_pr)

    def getReviewes(self, pr_by_slack_nick):
        reviews = requests.get(self.pr_link+"/"+PushPayload.EP_REVIEWS,  headers={
            "Authorization": "token "+GITHUB_TOKEN, "Accept":GITHUB_REVIEW_ACCEPT_KEY})
        print "********** My REVIEWS ***********", reviews.content
        bad_pr = True
        for item in json.loads(reviews.content):
            comment = item["body"]
            print "review body=", item["body"]
            print item["state"]
            thumbsUpIcon = "\ud83d\udc4d" in json.dumps(comment)
            print "thumbsUpIcon present=", thumbsUpIcon

            if self.pr_by in VALID_CONTRIBUTORS:  # FEW FOLKS TO ALLOW TO HAVE SUPER POWER
                print 'pr_by is super user of repo',self.repo,' so NO alert'
                bad_pr = False
                break

            if item["user"]["login"] != self.pr_by and (comment.find("+1") != -1 or thumbsUpIcon):
                print "No Alert because +1 found from commenter=" + item["user"]["login"] + " breaking further comments checks"
                bad_pr = False
                break

        bad_name_str = "Very Bad @" + pr_by_slack_nick
        if bad_pr:
            msg = "{name}:rage4: {pr} is merged into `{branch}` without a \"Tech +1\", soon these kind of requests will" \
                  " be automatically reverted CC: {team}".format(name=bad_name_str, pr=self.pr_link_pretty,
                                                           branch= self.base_branch, team=ALICE_NOTIFY_TEAM["repo1"])
            print msg
            #postToSlack(channel_name, msg, data={"username": bot_name})
        return bad_pr



@application.route("/merge", methods=['POST'])
def merge():

    if request.method != 'POST':
        abort(501)

    payload = request.get_data()
    data = json.loads(unicode(payload, errors='replace'), strict=False)
    obj = PushPayload(request, payload=data)
    merge_correctness = obj.was_eligible_to_merge()

    return jsonify(merge_correctness)



# @application.after_request
# def after_request(response):
#     timestamp = strftime('[%Y-%b-%d %H:%M]')
#     application.logger.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
#     return response

# @application.errorhandler(Exception)
# def exceptions(e):
#     tb = traceback.format_exc()
#     timestamp = strftime('[%Y-%b-%d %H:%M]')
#     application.logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, tb)
#     return e.status_code

if __name__ == "__main__":
    #application.run()
    handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
    logger = logging.getLogger('tdm')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    application.run(debug=True,
        host="0.0.0.0",
        port=int("5005")
    )

