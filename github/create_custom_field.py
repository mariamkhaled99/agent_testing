from .execute_github_graphql_query import execute_github_graphql_query

async def create_custom_field(project_id, field_name, data_type, token, options=None):
    """Creates a custom field in a GitHub project."""
    query = """
    mutation($input: CreateProjectV2FieldInput!) {
      createProjectV2Field(input: $input) {
        clientMutationId
        projectV2Field {
          __typename
          ... on ProjectV2FieldCommon {
            id
            name
            dataType
          }
        }
      }
    }
    """
    variables = {
        "input": {
            "projectId": project_id,
            "name": field_name,
            "dataType": data_type,
            "singleSelectOptions": options
        }
    }
    print(f"create_custom_field query: {query}")
    print(f"create_custom_field variables: {variables}")
    result = await execute_github_graphql_query(query, variables, token)
    print(f"create_custom_field result: {result}")
    if 'data' in result and 'createProjectV2Field' in result['data']:
        return result['data']['createProjectV2Field']['projectV2Field']
    elif 'errors' in result:
        raise Exception(result['errors'])
    else:
        raise Exception("Unexpected response format")