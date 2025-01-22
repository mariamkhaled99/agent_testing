import httpx
from .get_repository_id import get_repository_id
import uuid

async def merge_branch_via_graphql(repo_owner, repo_name, branch_name, github_token, github_email):
    
    repository_id = await get_repository_id(repo_owner, repo_name, github_token)
    
    
    
    """
    Calls GitHub's GraphQL API to merge a branch using httpx.
    """
    graphql_url = "https://api.github.com/graphql"
    
    merge_query = """
    mutation MergeBranch($input: MergeBranchInput!) {
        mergeBranch(input: $input) {
            clientMutationId
            mergeCommit {
                id
            }
        }
    }
    """
    
    variables = {
        "input": {
            "authorEmail": github_email,
            "base": "main",
            "clientMutationId": str(uuid.uuid4()),
            "commitMessage": f"Merging {branch_name} branch into main",
            "head": branch_name,
            "repositoryId": repository_id
        }
    }

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            graphql_url,
            json={"query": merge_query, "variables": variables},
            headers=headers
        )

    if response.status_code != 200:
        raise Exception(f"GitHub GraphQL API call failed with status {response.status_code}: {response.text}")

    response_data = response.json()
    if 'errors' in response_data:
        raise Exception(f"GitHub GraphQL API returned errors: {response_data['errors']}")

    return response_data['data']['mergeBranch']
