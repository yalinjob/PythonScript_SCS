import requests
import json
import os
import git
import xml.etree.ElementTree as ET

def clone_repository(github_url, destination_path):
    # Ensure the destination directory exists
    os.makedirs(destination_path, exist_ok=True)

    if not is_repository_cloned(destination_path):
        # Clone the repository into the destination path
        git.Repo.clone_from(github_url, destination_path)
        print("Repository cloned successfully.")
    else:
        print("Repository already cloned.")

def is_repository_cloned(destination_path):
    # Check if the destination directory exists
    if os.path.exists(destination_path):
        # Check if it contains the .git directory
        git_directory = os.path.join(destination_path, '.git')
        if os.path.exists(git_directory):
            return True
    return False

def invoke_api(api_token, dependencies):
    api_url = 'https://api.dusti.co/v1/packages'

    payload = []

    for dependency in dependencies:
        payload.append({
            "name": dependency['artifact_id'],
            "type": "mvn",
            "version": dependency['version']
        })

    # Convert the payload to a JSON formatted string
    json_payload = json.dumps(payload)
    
    # Print the JSON-formatted payload
    print("Payload:")
    print(json_payload)
     
    try:
        response = requests.post(api_url, headers={'Authorization': api_token, 'Content-Type': 'application/json'}, json=payload)
        if response.status_code == 200:
            print("API request successful")
            print("Response:")
            print(json.dumps(response.json(), indent=4))
        else:
            print(f"API request failed with status code: {response.status_code}")
            print("Response:")
            print(response.text)
    except Exception as e:
        print(f"Error occurred: {e}")

def clone_and_parse(github_url, destination_path):
    clone_repository(github_url, destination_path)
    pom_xml_path = os.path.join(destination_path, 'pom.xml')
    if os.path.exists(pom_xml_path):
        dependencies = parse_pom_xml(pom_xml_path)
        print("pom.xml file was found.")
        return dependencies
    else:
        print("pom.xml file not found.")
        return None

def parse_pom_xml(pom_xml_path):
    dependencies = []
    try:
        tree = ET.parse(pom_xml_path)
        root = tree.getroot()

        # Find dependencies
        dependency_elements = root.findall('.//{http://maven.apache.org/POM/4.0.0}dependency')
        print(f"Number of dependency elements found: {len(dependency_elements)}")

        if not dependency_elements:
            print("No dependency elements found.")

        for dependency in dependency_elements:
            group_id = dependency.find('{http://maven.apache.org/POM/4.0.0}groupId').text
            artifact_id = dependency.find('{http://maven.apache.org/POM/4.0.0}artifactId').text
            version = dependency.find('{http://maven.apache.org/POM/4.0.0}version').text
            
            # Check if the version is a placeholder
            if version and "${" not in version:
                dependencies.append({
                    'artifact_id': artifact_id,
                    'type': 'maven',
                    'version': version
                })
            else:
                print(f"Skipping dependency {artifact_id} due to placeholder version.")

        print("pom.xml file was found.")
        # Print each dependency in a readable format
        for dependency in dependencies:
            print(f"Artifact ID: {dependency['artifact_id']}, Version: {dependency['version']}")

    except Exception as e:
        print(f"Error occurred while parsing pom.xml file: {e}")

    return dependencies

if __name__ == "__main__":
    # Example GitHub repository URL and destination path
    github_url = 'https://github.com/WebGoat/WebGoat'
    destination_path = 'webgoat-master'

    # Retrieve API token from environment variable
    api_token = os.environ.get("API_TOKEN")
    if api_token is None:
        print("API token is not set.")
    else:
        print("API token:", api_token)

    # Clone repository and parse pom.xml to extract dependencies
    dependencies = clone_and_parse(github_url, destination_path)
    if dependencies:
        # Invoke API with extracted dependencies
        invoke_api(api_token, dependencies)
