import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# In production, load from env vars
app = App(token=os.environ.get("SLACK_BOT_TOKEN", "xoxb-mock"))

@app.command("/jira")
def handle_jira_command(ack, respond, command):
    ack()
    user_query = command['text']
    respond(f"Nexus received Jira command: {user_query}. Forwarding to Orchestrator...")
    # TODO: Call Orchestrator API here

@app.command("/search-rm")
def handle_search(ack, respond, command):
    ack()
    respond("Searching Nexus knowledge base... 🧠")

if __name__ == "__main__":
    # Start Socket Mode
    if os.environ.get("SLACK_APP_TOKEN"):
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
    else:
        print("Slack Token not found. Starting in HTTP mode for Dev.")
