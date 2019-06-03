import os

from fabric.api import run, sudo
from fabric.api import prefix, warn, abort
from fabric.api import task, env
from fabric.contrib.files import exists
from fabric.context_managers import cd

git_project = 'nimodipine-web'
django_app = 'nimodipine'
env.hosts = ['web2.openprescribing.net']
env.forward_agent = True
env.colorize_errors = True
env.user = 'hello'


environments = {
    'live': 'nimodipine',
    'staging': 'nimodipine-staging',
}

def make_directory():
    if not exists(env.path):
        sudo("mkdir -p %s" % env.path)
        sudo("chown -R www-data:www-data %s" % env.path)
        sudo("chmod  g+w %s" % env.path)

def venv_init():
    run('[ -e venv ] || python3 -m venv venv --without-pip')

def pip_install():
    with prefix('source /var/www/%s/venv/bin/activate' % env.app):
        sudo("chmod  g+w %s" % env.path)
        # We have to bootstrap pip this way because of issues in the Debian-provided python3.4
        # In python 3.6 we could remove the --without-pip above.
        run('wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py')
        run('rm get-pip.py*')
        run('pip install -q -r %s/%s/requirements.txt' % (git_project, django_app))

def update_from_git(branch):
    # clone or update code
    if not exists('%s/.git' % git_project):
        run("git clone -q git@github.com:ebmdatalab/%s.git" % git_project)
    with cd(git_project):
        run("git fetch --all")
        run("git reset --hard origin/{}".format(branch))
        run("chmod 775 */*.log")

def setup_nginx():
    sudo('%s/%s/deploy/setup_nginx.sh %s %s' % (git_project, django_app, env.path, env.environment))
    # https://stackoverflow.com/a/33881057/559140
    sudo('/etc/init.d/supervisor force-stop && '
         '/etc/init.d/supervisor stop && '
         '/etc/init.d/supervisor start')

def setup_django():
    with prefix('source /var/www/%s/venv/bin/activate' % env.app):
        run('cd %s/%s/ && python manage.py collectstatic --noinput ' % (git_project, django_app))
        run('cd %s/%s/ && python manage.py migrate' % (git_project, django_app))

def restart_gunicorn():
    sudo("%s/%s/deploy/restart.sh %s" % (git_project, django_app, env.app))

def reload_nginx():
    sudo("%s/%s/deploy/reload_nginx.sh" % (git_project, django_app))

def setup(environment, branch='master'):
    if environment not in environments:
        abort("Specified environment must be one of %s" %
              ",".join(environments.keys()))
    env.app = environments[environment]
    env.environment = environment
    env.path = "/var/www/%s" % env.app
    env.branch = branch
    return env


@task
def deploy(environment, branch='master', git_only=False):
    env = setup(environment, branch)
    make_directory()
    with cd(env.path):
        print(env.path)
        # We can use all the same connection details as the main app
        with prefix("source /etc/profile.d/nimodipine_%s.sh" % env.environment):
            venv_init()
            update_from_git(branch)
            if not git_only:
                pip_install()
                setup_django()
                setup_nginx()
                restart_gunicorn()
                reload_nginx()
