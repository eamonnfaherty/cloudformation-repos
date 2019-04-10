import click
import logging
import requests
import yaml
import os
import json
import subprocess
from terminaltables import AsciiTable, SingleTable
from colorclass import Color


logger = logging.getLogger(__file__)

CONFIG_PATH = os.path.sep.join([os.environ.get('HOME'), '.cloudformation-repos'])
GLOBAL_CONFIG_LOCATION = os.path.sep.join([CONFIG_PATH, 'global.yaml'])


@click.group()
@click.option('--info/--no-info', default=False)
@click.option('--info-line-numbers/--no-info-line-numbers', default=False)
def cli(info, info_line_numbers):
    """cli for pipeline tools"""
    if info:
        logging.basicConfig(
            format='%(levelname)s %(threadName)s %(message)s', level=logging.INFO
        )
    if info_line_numbers:
        logging.basicConfig(
            format='%(levelname)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO
        )


def put_global_config(global_config):
    logger.info('putting global config')
    with open(GLOBAL_CONFIG_LOCATION, 'w') as f:
        f.write(yaml.safe_dump(global_config))


def get_global_config():
    logger.info('getting global config')
    if not os.path.exists(CONFIG_PATH):
        logger.info('creating config path: {}'.format(CONFIG_PATH))
        os.makedirs(CONFIG_PATH)
    if not os.path.exists(GLOBAL_CONFIG_LOCATION):
        logger.info('creating global config: {}'.format(GLOBAL_CONFIG_LOCATION))
        put_global_config({})

    return yaml.safe_load(open(GLOBAL_CONFIG_LOCATION))


@cli.command()
@click.argument('owner')
@click.argument('repo')
def add_github_repo(owner, repo):
    global_config = get_global_config()
    logger.info("Global config: {}".format(global_config))

    config = requests.get(
        "https://raw.githubusercontent.com/{}/{}/master/cloudformation-repos.yaml".format(owner, repo)
    )
    config = yaml.safe_load(config.text)

    if global_config.get('providers') is None:
        global_config['providers'] = {}
    if global_config.get('providers').get('github') is None:
        global_config['providers']['github'] = {}
    logger.info("Adding repo: {}".format(config))
    global_config['providers']['github']["{}/{}".format(owner, repo)] = config
    put_global_config(global_config)


@cli.command()
@click.argument('what')
def search(what):
    global_config = get_global_config()
    results = [
        ['Repo', 'Directory', 'Description']
    ]
    for uid, config in global_config.get('providers').get('github').items():
        check_provider_github(uid, config, what, results)
    table = SingleTable(results)
    table.title = "Results"

    click.echo(table.table.replace(what, Color("{green}"+what+"{/green}")))


def check_provider_github(uid, config, what, results):
    logger.info("looking at: {}".format(uid))

    headers = {}
    if os.environ.get('GITHUB_TOKEN'):
        logger.info("Adding token to the headers")
        headers["Authorization"] = "token {}".format(os.environ.get('GITHUB_TOKEN'))

    repo_config = config.get('repo').get('config')
    r = requests.get('https://api.github.com/repos/{owner}/{repo}/contents/'.format(**repo_config), headers=headers)
    if r.status_code == 200:
        for f in r.json():
            logger.info("Looking at: {} in: {}".format(f.get('name'), uid))
            if f.get('type') == 'dir':
                directory_name = f.get('name')
                r = requests.get(
                    "https://raw.githubusercontent.com/{owner}/{repo}/master/{directory_name}/README.md".format(
                        **repo_config, directory_name=directory_name
                    )
                )
                if r.status_code == 200:
                    logger.info("looking in README.md")
                    pos = r.text.lower().find(what.lower())
                    if pos > -1:
                        results.append([uid, directory_name, r.text])
                else:
                    raise Exception(r.text)

            if what.lower() in f.get('name').lower():
                click.echo("{} matches in filename: {}".format(uid, f.get('name')))
    else:
        raise Exception(r.json().get('message'))


@cli.command()
@click.argument('owner-and-repo')
@click.argument('directory')
@click.argument('path')
def grab_from_github(owner_and_repo, directory, path):
    subprocess.call([
        "svn",
        "export",
        "https://github.com/{}/trunk/{}".format(owner_and_repo, directory),
        path,
        '--force',
    ])


if __name__ == "__main__":
    cli()
