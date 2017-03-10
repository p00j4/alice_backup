import falcon
import logging
from logging.handlers import RotatingFileHandler
from alice.helper.constants  import *
import requests
#from flask import app as application
import simplejson as json
from alice.helper.common_utils import CommonUtils
#from alice.helper.base import JSONBodyParser
from alice.helper.message_template import *
from alice.helper.slack_helper import SlackHelper

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
        if self.is_merged:
            self.MERGED_BY_SLACK_NICK = CommonUtils.getSlackNicksFromGitNicks(self.merged_by)
            self.PR_BY_SLACK_NICK = CommonUtils.getSlackNicksFromGitNicks(self.pr_by)
            self.bad_name_str = MSG_BAD_START + self.PR_BY_SLACK_NICK

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

    MERGED_BY_SLACK_NICK = ""
    PR_BY_SLACK_NICK = ""

    def was_eligible_to_merge(self):
        if self.is_merged:   #and self.head_branch in PushPayload.PROTECTED_BRANCH_LIST:  TO ENABLE
            is_bad_pr = self.is_reviewed()
            if is_bad_pr:
                msg = MSG_NO_REVIEW.format(name=self.bad_name_str, pr=self.pr_link_pretty,
                                           branch= self.base_branch, team=ALICE_NOTIFY_TEAM["repo1"])
            slack = SlackHelper()
            slack.postToSlack("general", msg)
            slack.postToSlack("general", msg=msg, attachments=[{"pretext": "pre-hello", "text": msg, "fields": [], "color": "#764FA5"}])
            return "{msg} repo:{repo}".format(repo=self.repo, msg=msg)

    def is_reviewed(self):
        reviews = requests.get(self.pr_link+"/"+PushPayload.EP_REVIEWS,  headers={
            "Authorization": "token "+GITHUB_TOKEN, "Accept":GITHUB_REVIEW_ACCEPT_KEY})
        print "********** My REVIEWS ***********", reviews.content
        bad_pr = True
        for item in json.loads(reviews.content):
            comment = item["body"]
            print "review body=", item["body"]; print item["state"]
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

        #postToSlack(channel_name, msg, data={"username": bot_name})
        return bad_pr



class MergePullRequest:
    def on_post(self, request, response):
        body = request.stream.read()                    #data = request.context['request_body']
        data = json.loads(body.decode('utf-8'))
        obj = PushPayload(request, payload=data)
        merge_correctness = obj.was_eligible_to_merge()
        response.body = json.dumps(merge_correctness)    #response.context['response'] = merge_correctness   #if used middleware JSONBodyParser

#middleware = [JSONBodyParser()]
#app = falcon.API(middleware=middleware)
app = falcon.API()
app.add_route('/merge', MergePullRequest())


