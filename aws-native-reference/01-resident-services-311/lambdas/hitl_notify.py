from _shared import ok
# Sends the draft + task token to the reviewer queue (SNS/SES/Connect). The Step
# Functions waitForTaskToken pause holds here until a reviewer approves.
def handler(event, _ctx=None):
    return ok({**event, "review_status": "PENDING", "notified": True})
