import json
from aiohttp import request


def handle_webhook_delivery(payload, event_type):
    """
    Handles GitHub webhook deliveries for push and pull_request events.
    """
    repository = payload.get('repository', {}).get('full_name')
    if repository != "mariamkhaled99/ABI-Backend-Assesment":  # Replace with your repo name
        print(f"Ignoring event for repository: {repository}")
        return

    if event_type == 'push':
        # Handle push event
        branch = payload.get('ref').split('/')[-1]  # Extract branch name
        commits = payload.get('commits', [])
        print(f"Push event received for branch: {branch}")
        print(f"Number of commits: {len(commits)}")
        for commit in commits:
            print(f"Commit ID: {commit['id']}, Message: {commit['message']}")

    elif event_type == 'pull_request':
        # Handle pull_request event (includes merge actions)
        action = payload.get('action')
        pr_number = payload.get('number')
        pr_title = payload.get('pull_request', {}).get('title')
        merged = payload.get('pull_request', {}).get('merged')

        if action == 'closed' and merged:
            print(f"Pull request #{pr_number} was merged: {pr_title}")
        elif action == 'closed' and not merged:
            print(f"Pull request #{pr_number} was closed without merging: {pr_title}")
        else:
            print(f"Unhandled action for pull_request event: {action}")

    else:
        print(f"Ignoring unhandled event type: {event_type}")


def webhook():
    # Respond to indicate that the delivery was successfully received
    
    response =json.dumps({'status': 'Accepted'})
    response.status_code = 202

    # Check the `x-github-event` header to learn what event type was sent
    github_event = request.headers.get('X-GitHub-Event')

    # Handle the webhook delivery
    handle_webhook_delivery(request.json, github_event)

    return response