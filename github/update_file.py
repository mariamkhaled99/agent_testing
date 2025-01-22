from .execute_github_graphql_query import execute_github_graphql_query
from .get_repository_id import get_repository_id
from .get_branch_oid import get_branch_oid


async def update_files_on_github(token, repo_owner, repo_name, user_branch_name, file_paths_and_contents, latest_commit_oid):
    try:
        # Create a new commit with the updated files
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
        additions = []
        for file_path, file_content in file_paths_and_contents:
            additions.append({
                "path": file_path,
                "contents": file_content
            })
        variables = {
            "input": {
                "branch": {
                    "repositoryNameWithOwner": f"{repo_owner}/{repo_name}",
                    "branchName": user_branch_name
                },
                "message": {
                    "headline": "Update files"
                },
                "fileChanges": {
                    "additions": additions
                },
                "expectedHeadOid": latest_commit_oid
            }
        }
        print(f"Updating files on GitHub: {repo_owner}/{repo_name} - {user_branch_name}")
        response = await execute_github_graphql_query(query, variables, token)
        print(f"GitHub response: {response}")
        if "errors" in response:
            print(f"Error updating files on GitHub: {response['errors']}")
            raise Exception(f"Mutation returned errors: {response['errors']}")

        print(f"Files updated successfully on GitHub: {response['data']['createCommitOnBranch']['commit']['oid']}")
        return response["data"]["createCommitOnBranch"]["commit"]["oid"]

    except Exception as e:
        print(f"An error occurred: {e}")
        return None