import os
import sys
# Mock imports for script safety
try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
except ImportError:
    class App:
        def __init__(self, token): pass
        def command(self, cmd): return lambda f: f
        def view(self, name): return lambda f: f

sys.path.append(os.path.abspath("../../../shared"))
from nexus_lib.utils import AsyncHttpClient

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
orchestrator_client = AsyncHttpClient(base_url=os.environ.get("ORCHESTRATOR_URL", "http://localhost:8080"))

@app.command("/nexus")
def handle_nexus_command(ack, body, client):
    ack()
    user_query = body['text']
    client.chat_postMessage(channel=body['channel_id'], text=f"🧠 Nexus is thinking about: '{user_query}'...")

@app.command("/jira-update")
def open_update_modal(ack, body, client):
    ack()
    client.views_open(trigger_id=body["trigger_id"], view={
        "type": "modal", "callback_id": "jira_update_view", "title": {"type": "plain_text", "text": "Update Jira Ticket"},
        "blocks": [{"type": "input", "block_id": "ticket_id", "label": {"type": "plain_text", "text": "Ticket Key"}}]
    })

if __name__ == "__main__":
    if os.environ.get("SLACK_APP_TOKEN"):
        SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
