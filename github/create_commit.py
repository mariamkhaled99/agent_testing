import httpx

GITHUB_API_URL = "https://api.github.com/graphql"

async def create_commit(token, repo_owner, repo_name, branch_name, file_additions, commit_message, expected_head_oid):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    query = """
    mutation($input: CreateCommitOnBranchInput!) {
        createCommitOnBranch(input: $input) {
            commit {
                oid
                url
            }
        }
    }
    """

    variables = {
        "input": {
            "branch": {
                "repositoryNameWithOwner": f"{repo_owner}/{repo_name}",
                "branchName": branch_name
            },
            "message": {
                "headline": commit_message
            },
            "fileChanges": {
                "additions": file_additions
            },
            "expectedHeadOid": expected_head_oid
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GITHUB_API_URL, headers=headers, json={"query": query, "variables": variables}, timeout=None)
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise Exception(f"Mutation returned errors: {data['errors']}")
        return data["data"]["createCommitOnBranch"]["commit"]["oid"]