def app():
    """ Run application tasks """
    with cd(VARS['root_dir']):
        # Create venv and install requirements
        run('pyvenv-{{ pyenv_version }} {venv_path}'.format(**VARS))
        # Install required python packages with pip from wheels archive
        run('make wheel_install')
        # run app tasks for devserver start
        # Copy settings local
        run('cd {project_name} && cp settings_local.py.example settings_local.py'.format(**VARS))


def localserver():
    with cd(VARS['root_dir']):
        # collect static files
        for command in ('migrate --noinput', 'collectstatic --noinput', ):  # 'compilemessages', ):
            run('{venv_path}/bin/python manage.py {command}'.format(command=command, **VARS))
        # make root dir available to read
        # sudo('chmod 755 {base_dir}/static -R'.format(**VARS))
        # Create user
        create_user_py = dedent('''\
            from django.contrib.auth import get_user_model
            User = get_user_model()
            User.objects.create_superuser(**{user_data})
        ''').format(**VARS)

        run('echo "{create_user_py}" | {venv_path}/bin/python manage.py shell'.format(
            create_user_py=create_user_py, **VARS))
        run('mkdir var -p')

        # Start{% if CELERY %} celery and{% endif %} runserver
        run('make start', pty=False){% if CELERY %}
        run('make runcelery_multi', pty=False){% endif %}
