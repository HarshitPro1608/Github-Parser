from flask import Flask, render_template, url_for, redirect
from authlib.integrations.flask_client import OAuth
from github import Github
from xml.etree import ElementTree as ET


app = Flask(__name__)

oauth = OAuth(app)

app.config['SECRET_KEY'] = "THIS SHOULD BE SECRET"
app.config['GITHUB_CLIENT_ID'] = "01a4e1bb9ae4a9ed2907"
app.config['GITHUB_CLIENT_SECRET'] = "90ec1c66fc46045b94b342a2687192ce9b105f10"


github = oauth.register (
  name = 'github',
    client_id = app.config["GITHUB_CLIENT_ID"],
    client_secret = app.config["GITHUB_CLIENT_SECRET"],
    access_token_url = 'https://github.com/login/oauth/access_token',
    access_token_params = None,
    authorize_url = 'https://github.com/login/oauth/authorize',
    authorize_params = None,
    api_base_url = 'https://api.github.com/',
    client_kwargs = {'scope': 'user:email'},
)


# Default route
@app.route('/')
def index():
  return render_template('index.html')


# Github login route
@app.route('/login/github')
def github_login():
    github = oauth.create_client('github')
    redirect_uri = url_for('github_authorize', _external=True)
    return github.authorize_redirect(redirect_uri)


# Github authorize route
@app.route('/login/github/authorize')
def github_authorize():
    github = oauth.create_client('github')
    token = github.authorize_access_token()
    res = github.get('user').json()
    user = res.get('login')
    resp = github.get('user/repos').json()
    repos = [repo['full_name'] for repo in resp]
    # print(f"\n{repos}\n")
    return render_template('repos.html', repos=repos, user=user)

@app.route('/parse_pom_xml_files/<path:repo_name>')
def parse_pom_xml_files(repo_name):
    g = Github()
    repo = g.get_repo(repo_name)
    pom_files = find_pom_xml_files(repo)
    dependencies = []
    for pom_file in pom_files:
        dependencies.extend(parse_pom_xml(pom_file))
    return render_template('dependencies.html', repo_name=repo_name, dependencies=dependencies)

def find_pom_xml_files(repo):
    pom_files = []
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        elif file_content.name.lower() == "pom.xml":
            pom_files.append(file_content)
    return pom_files

def parse_pom_xml(file_content):
    dependencies = []
    response = file_content.decoded_content.decode("utf-8")
    root = ET.fromstring(response)
    namespaces = {"maven": "http://maven.apache.org/POM/4.0.0"}
    for dependency in root.findall(".//maven:dependency", namespaces):
        group_id = dependency.find("maven:groupId", namespaces).text.strip()
        artifact_id = dependency.find("maven:artifactId", namespaces).text.strip()
        version = dependency.find("maven:version", namespaces).text.strip()
        dependencies.append(f"{group_id}: Version {version}")
    return dependencies

if __name__ == '__main__':
  app.run(debug=True)