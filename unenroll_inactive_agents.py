# This script will find agents that haven't been seen for > 1 day and force unenroll / revoke them
# Careful with this - if you had an agent offline, or the elastic server itself was offline for > 24 hours, this will unenroll active/live servers.
# You can also use the whitelist to protect fleet machines and similar

import requests
from requests.auth import HTTPBasicAuth
import json

# Configuration
elastic_host = 'http://localhost:9200'
kibana_host = 'http://localhost:5601'
username = 'elastic'
password = 'changeme'

# Whitelist of agent IDs to exclude from unenrollment
whitelist_agent_ids = [
    'your_fleet_machine_agent_id_1',
    'your_fleet_machine_agent_id_2'
]

# Step 1: Query Elasticsearch to find inactive agents
def get_inactive_agents():
    size = 1000  # Set a high limit for the number of results to retrieve
    query = {
        "size": size,
        "query": {
            "range": {
                "last_checkin": {
                    "lt": "now-1d/d"
                }
            }
        }
    }

    response = requests.post(
        f'{elastic_host}/.fleet-agents/_search',
        auth=HTTPBasicAuth(username, password),
        headers={'Content-Type': 'application/json'},
        data=json.dumps(query)
    )

    if response.status_code != 200:
        print(f"Error querying Elasticsearch: {response.text}")
        return []

    return response.json()['hits']['hits']

inactive_agents = get_inactive_agents()

# Step 2: Prepare the list of agent IDs for bulk unenrollment, excluding those in the whitelist
agent_ids = [agent['_id'] for agent in inactive_agents if agent['_id'] not in whitelist_agent_ids]

# Step 3: Bulk unenroll inactive agents
if agent_ids:
    bulk_unenroll_payload = {
        "agents": agent_ids,
        "force": True,
        "revoke": True
    }

    bulk_unenroll_response = requests.post(
        f'{kibana_host}/api/fleet/agents/bulk_unenroll',
        auth=HTTPBasicAuth(username, password),
        headers={'kbn-xsrf': 'true', 'Content-Type': 'application/json'},
        data=json.dumps(bulk_unenroll_payload)
    )

    if bulk_unenroll_response.status_code == 200:
        print("Successfully unenrolled inactive agents in bulk.")
    else:
        print(f"Error unenrolling agents in bulk: {bulk_unenroll_response.text}")
else:
    print("No inactive agents to unenroll.")

print("Done.")
