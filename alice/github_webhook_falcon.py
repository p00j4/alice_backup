from flask import Flask, request, jsonify, abort
import logging
import traceback
from time import strftime
from logging.handlers import RotatingFileHandler
from alice.helper.constants  import *
import requests
#from flask import app as application
import simplejson as json
application = Flask(__name__)

@application.route("/",methods=['GET','POST'])
def hello():
    return "Hello World!"


class PushPayload():
    API_START_PR = "https://api.github.com/repos/moengage/MoEngage/pulls/"
    API_START_ISSUES = "https://api.github.com/repos/moengage/MoEngage/issues/"
    EP_REVIEWS = "reviews"
    EP_COMMENTS = "comments"
    STATE_OPEN = "open"
    STATE_CLOSED = "closed"
    PROTECTED_BRANCH_LIST = ["dev", "qa", "master"]

    #sensitiv

    def __init__(self, request, payload):
        self.request = request
        self.payload = payload
        self.data  = payload["pull_request"]

    
    @property
    def pr_link_pretty(self):
        return self.data["html_url"]

    @property
    def pr_link(self):
        return self.data["url"]

    @property
    def pr_by(self):
        return self.data["user"]["login"]

    @property
    def is_merged(self):
        return self.data["merged"]

    @property
    def action(self):
        return self.payload["action"]

    @property
    def repo(self):
        return self.payload["repository"]["name"]#self.data["head"]["repo"]["name"]

    @property
    def base_branch(self):
        return self.data["base"]["ref"]

    @property
    def head_branch(self):
        return self.data["head"]["ref"]



    def was_elligible_to_merge(self):
        if self.is_merged and self.head_branch in PushPayload.PROTECTED_BRANCH_LIST:
            self.getReviewes()
            return "repo:{repo} commits came from {pr}".format(repo=self.repo, pr=self.pr_link)

    def getReviewes(self):
        reviews = requests.get(self.pr_link+"/"+PushPayload.EP_REVIEWS,  headers={
            "Authorization": "token "+GITHUB_TOKEN, "Accept":GITHUB_REVIEW_ACCEPT_KEY})
        print "********** My REVIEWS ***********", reviews.content
        for item in json.loads(reviews.content):
            print item["body"]
            print item["state"] 


@application.route("/merge", methods=['POST'])
def merge():

    if request.method != 'POST':
        abort(501)

    payload = request.get_data()
    data = json.loads(unicode(payload, errors='replace'), strict=False)
    obj = PushPayload(request, payload=data)
    merge_correctness = obj.was_elligible_to_merge()

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
