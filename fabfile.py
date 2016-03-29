import os
import sys
import string
import random

import fabric
from fabric.api import run, sudo, cd, put


fabric.state.env.colorize_errors = True
# fabric.state.output['stdout'] = False

sys.path.insert(0, os.path.dirname(__file__))

VARS = dict(
    init_app=True,
    base_path=os.getcwd(),
    templates_dir=os.path.join(os.path.dirname(__file__), 'templates')
)


def str_random(size=9, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    """ Not a fabric task, it will generate random str for passw """
    return ''.join(random.choice(chars) for _ in range(size))


def render_template(template_name, remote_name):
    """ Render wrapper for simplify touch rendered template into target """
    if os.path.dirname(remote_name):
        run('mkdir -p {}'.format(os.path.dirname(remote_name)))
    fabric.contrib.files.upload_template(
        template_name, remote_name,
        context=VARS, use_jinja=True,
        backup=False, use_sudo=False, template_dir=VARS['templates_dir']
    )


def common(proj_name=None):
    """ Run all common tasks """
    if proj_name:
        VARS['proj_name'] = proj_name
    read_data()
    start_box()


def read_data():
    from settings import settings
    VARS.update(settings)

    if 'proj_ip' not in VARS:
        VARS['proj_ip'] = raw_input('project ip: ')

    while 'proj_name' not in VARS:
        proj_name = raw_input('project name: ')
        if proj_name.isalpha():
            VARS['proj_name'] = proj_name
        else:
            print ('incorect name')

    if 'db_user' not in VARS:
        VARS['db_user'] = VARS['proj_name'] + '_user'

    if 'box_name' not in VARS:
        VARS['box_name'] = raw_input('box name: ')

    if 'db_pass' not in VARS:
        VARS['db_pass'] = str_random()

    VARS['root_dir'] = os.path.join(VARS['base_path'], VARS['proj_name'])


def start_box():
    """ Create Vagrant file and up virtual machine """
    run('mkdir -p {root_dir}'.format(**VARS))
    with cd(VARS['root_dir']):
        render_template('Vagrantfile.j2', 'Vagrantfile')
        render_template('Makefile.j2', 'Makefile')
        run('chmod +x Makefile')
        # make provisioning folder
        run('mkdir -p provision')
        render_template('provision_fabfile.j2', 'provision/fabric_provisioner.py')
        render_template('requirements.j2', 'requirements.txt')
        render_template('requirements.j2', 'requirements-remote.txt')
        render_template('settings_local.j2', '{proj_name}/settings_local.py.example'.format(**VARS))
        # copy templates for vagrant fabric render
        path = os.path.join(VARS['templates_dir'], 'vagrant_templates')
        run('mkdir -p {}'.format('provision/templates'))
        put(path, 'provision')
        run('rm -rf provision/templates && mv -f provision/vagrant_templates provision/templates')
        # run vagrant up
        run('vagrant up')
        # replace template
        VARS['init_app'] = False
        render_template('provision_fabfile.j2', 'provision/fabric_provisioner.py')


def reprovision():
    read_data()
    with cd(VARS['root_dir']):
        run('vagrant provision')


def rmproj():
    """ Remove project """
    read_data()
    with cd(VARS['root_dir']):
        run('vagrant destroy')

    run('rm {root_dir} -rf'.format(**VARS))
