import os

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

LINKED_PR_QUERY_STR = """
query getLinkedPrs($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      timelineItems(itemTypes: [CONNECTED_EVENT, DISCONNECTED_EVENT], first: 100) {
        nodes {
          ... on ConnectedEvent {
            __typename
            id
            subject {
              ... on PullRequest {
                id
                number
              }
            }
          }
          ... on DisconnectedEvent {
            __typename
            id
            subject {
              ... on PullRequest {
                id
                number
              }
            }
          }
        }
      }
    }
  }
}
"""

LINKED_PR_QUERY = gql(LINKED_PR_QUERY_STR)


def make_params(owner, repo, number):
    return({"owner": owner, "name": repo, "number": number})


def execute_query(client, query, params):
    result = client.execute(query, variable_values=params)
    return(result)


def parse_results(results):
    """Return a list of issue numbers connected to the PR.

    Only include those that haven't been disconnected.

    """

    timelineItems = results['repository']['issue']['timelineItems']
    nodes = timelineItems['nodes']

    # issue numbers of connected events
    conn_pr_ids = set([node['subject']['number'] for node in nodes if node['__typename'] == 'ConnectedEvent'])

    # issue numbers of disconnected events
    disconn_pr_ids = set([node['subject']['number'] for node in nodes if node['__typename'] == 'DisconnectedEvent'])

    return list(conn_pr_ids.difference(disconn_pr_ids))


def main():

    my_input_token = os.environ["INPUT_GITHUB_TOKEN"]
    my_input_owner = os.environ["INPUT_OWNER"]
    my_input_repo = os.environ["INPUT_OWNER"]
    my_input_number = os.environ["INPUT_NUMBER"]

    headers={'Authorization': f'bearer {os.environ["INPUT_GITHUB_TOKEN"]}',
             "Content-Type": "application/json"}

    # Select your transport with a defined url endpoint
    transport = AIOHTTPTransport(url="https://api.github.com/graphql", 
                                 headers=headers)

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)

    params = make_params(owner=my_input_owner, repo=my_input_repo, number=my_input_number)
    results = execute_query(client=client, query=LINKED_PR_QUERY, params=params)

    linked_prs = parse_results(results)

    print(f"::set-output name=linkedPrs::{linked_prs}")

if __name__ == "__main__":
    main()
