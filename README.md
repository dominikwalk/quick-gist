[![tests](https://github.com/dominikwalk/quick-gist/actions/workflows/tests.yaml/badge.svg)](https://github.com/dominikwalk/quick-gist/actions/workflows/tests.yaml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/dominikwalk/quick_gist/master.svg)](https://results.pre-commit.ci/latest/github/dominikwalk/quick_gist/master)
[![codecov](https://codecov.io/github/dominikwalk/quick-gist/branch/master/graph/badge.svg?token=ZXWA8HO7I4)](https://codecov.io/github/dominikwalk/quick-gist)
# quick-gist
A tool that allows to quickly create Github Gists from your files.


## Installation
```console
pip install quick-gist
```
## Usage
### First time configuration
If you use quick-gist for the first time you have to create a new user configuration first:
```console
quick-gist add-user
```
At first start quick-gist will automatically create a configuration file under ``~/.config/quick_gist/quick-gist-config.yaml``.  This is the place where your Github username and Github-API token are stored. Just follow the instructions on the screen and type in your Github username.

Now your are having two options to store your Github API token:

- from an **environment variable**
- from the **configuration file**

**Environment variable:** If this option is selected, quick-gist is configured to look for your API token in an environment variable named ``QUICK_GIST_"YOUR-USERNAME"_AUTH`` every time you want to create a new gist. But you have to set this variable yourself in your environment variables.

**From the configuration file:** Using this option, your API token will be stored in the configuration file you just created.

**In both cases**, you have the **option** to encrypt your API token with a password. The tool will ask you for your password every time you want to create a new Github Gist.
#### Creating a Github API token
Now, and in order to use the tool, you neet to create a new Github API token. Just go to [Github Token Settings](https://github.com/settings/tokens) and log in to your Github account. There you will find the option to create a new token.

Type in a note. For example: "Access token for quick-gist" and select the checkbox **gist** for the scopes.

You can also specify an expiration time. This is the time after which your token becomes invalid and you have to recreate it. However, you can also choose the option without expiration date so that your token will be valid forever.
Click **Generate Token** to complete the process.
**Copy** your token and paste it into your terminal when quick-gist asks you for it.
Decide whether you want to encrypt your token with a password or not.
**The configuration is now complete.** If you have chosen the option to store the token in an environment variable, it will now tell you under which name and with which value it should be stored. If you have chosen the option to encrypt the token with a password, it will show you the value of the encrypted token.

### Once it is configured
#### New Github Gist
Creating a new Github Gist works with the following command:
```console
quick-gist new -f file1.txt file2.txt
```
##### Command line options
``-f/--files`` files from which you want to create your new Github Gist

``-d/--description`` (optional)  the Github Gist description

``-p/--public`` (optional)  make the Github Gist public, **default is secret**

``-sf/--softfail`` (optional) issue a warning instead of aborting if the program cannot read a file, **default disabled**

``-u/--user`` (optional) specify Github username if you have more then one user configured


##### Specify line numbers
You can specify from which exact line numbers in your files you want to create a new Github Gist by passing it to the ``-f/--files`` argument.
**Example:** ``quick-gist new -f file1.txt[1-5] file2.txt[2] file3.txt[1-5,10-15]``

In this case a new Github Gist will be created which includes
- line 1 to 5 from file1.txt
- only line 2 from file2.txt
- lines 1-5 and line 10-15 from file3.txt

If no lines are specified, the entire file is included.

#### List configured Github users
```console
quick-gist list-user
```
This command will print out information about which Github users are configured and how the API token is stored.

#### Remove configured Github users
```console
quick-gist remove-user
```
This command will allow you to remove a configured Github user from your configuration

#### Add Github user to your configuration
```console
quick-gist add-user
```
This command will allow you to add a new Github user to your configuration

## TODOs
- Allow passing a directory as file argument and add all files from this directory
- Allow piping content directly into the tool to create a new gist (instead of files)
- Issue warning when Github API token is about to expire
- Add command to renew Gihub API token
- Unittest (and refactor some functions to make them easier to test)

---
Any pull requests are welcome 🍰
