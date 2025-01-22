from .execute_github_graphql_query import execute_github_graphql_query

async def link_project_to_repository(project_id, repo_id, token):
    """Links a GitHub project to a repository."""
    query = """
    mutation($input: LinkProjectV2ToRepositoryInput!) {
      linkProjectV2ToRepository(input: $input) {
        clientMutationId
        repository {
          id
        }
      }
    }
    """
    variables = {
        "input": {
            "projectId": project_id,
            "repositoryId": repo_id
        }
    }
    print(f"link_project_to_repository query: {query}")
    print(f"link_project_to_repository variables: {variables}")
    result = await execute_github_graphql_query(query, variables, token)
    print(f"link_project_to_repository result: {result}")
    if 'data' in result and 'linkProjectV2ToRepository' in result['data']:
        return result['data']['linkProjectV2ToRepository']['repository']['id']
    elif 'errors' in result:
        raise Exception(result['errors'])
    else:
        raise Exception("Unexpected response format")