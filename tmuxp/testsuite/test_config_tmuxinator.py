# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import os
import shutil
import unittest
import kaptan
from .. import config, exc
from ..util import tmux, basestring

from .. import log
import logging

logger = logging.getLogger(__name__)
TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')

# https://github.com/aziz/tmuxinator


def tmuxinator_to_tmuxp(sconf):
    '''

    :param sconf: python dict for session configuration
    :type sconf: dict
    '''

    tmuxp_config = {}

    if 'project_name' in sconf:
        tmuxp_config['session_name'] = sconf['project_name']
    else:
        tmuxp_config['session_name'] = None

    if 'cli_args' in sconf:
        tmuxp_config['config'] = sconf['cli_args']

        if '-f' in tmuxp_config['config']:
            tmuxp_config['config'] = tmuxp_config['config'].replace('-f', '').strip()

    if 'socket_name' in sconf:
        tmuxp_config['socket_name'] = sconf['socket_name']

    tmuxp_config['windows'] = []
    logger.error(sconf)
    if 'tabs' in sconf:
        sconf['windows'] = sconf.pop('tabs')

    if 'pre' in sconf:
        if isinstance(sconf['pre'], basestring):
            tmuxp_config['shell_command_before'] = [sconf['pre']]
        else:
            tmuxp_config['shell_command_before'] = sconf['pre']

    if 'rbenv' in sconf:
        if 'shell_command_before' not in tmuxp_config:
            tmuxp_config['shell_command_before'] = []
        tmuxp_config['shell_command_before'].append(
            'rbenv %s' % sconf['rbenv']
        )

    for w in sconf['windows']:
        for k, v in w.items():

            windowdict = {}

            windowdict['window_name'] = k

            logger.error('%s, %s' % (k, v))

            if isinstance(v, basestring) or v is None:
                windowdict['panes'] = [v]
                continue

            if 'pre' in v:
                logger.error(v['pre'])
                windowdict['shell_command_before'] = v['pre']
            if 'panes' in v:
                windowdict['panes'] = v['panes']

            if 'layout' in v:
                windowdict['layout'] = v['layout']
            tmuxp_config['windows'].append(windowdict)

    return tmuxp_config


class TmuxinatorTest(unittest.TestCase):

    tmuxinator_yaml = """\
    windows:
    - editor:
        layout: main-vertical
        panes:
            - vim
            - guard
    - server: bundle exec rails s
    - logs: tail -f logs/development.log
    """

    tmuxinator_dict = {
        'windows': [
            {
                'editor': {
                    'layout': 'main-vertical',
                    'panes': [
                        'vim',
                        'guard'
                    ]
                }
            },
            {
                'server': 'bundle exec rails s',
            },
            {
                'logs': 'tail -f logs/development.log'
            }
        ]
    }

    tmuxp_dict = {
        'session_name': None,
        'windows': [
            {
                'window_name': 'editor',
                'layout': 'main-vertical',
                'panes': [
                    'vim',
                    'guard'
                ]
            },
            {
                'window_name': 'server',
                'panes': [
                    'bundle exec rails s'
                ]
            },
            {
                'window_name': 'logs',
                'panes': [
                    'tail -f logs/development.log'
                ]
            }
        ]
    }

    def test_config_to_dict(self):
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.tmuxinator_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.tmuxinator_dict)

        self.assertDictEqual(tmuxinator_to_tmuxp(yaml_to_dict), self.tmuxp_dict)


class TmuxinatorDeprecationsTest(unittest.TestCase):

    ''' tmuxinator uses `tabs` instead of `windows` in older versions

    https://github.com/aziz/tmuxinator/blob/master/lib/tmuxinator/project.rb#L18

    https://github.com/aziz/tmuxinator/blob/master/spec/fixtures/sample.deprecations.yml

    LICENSE: https://github.com/aziz/tmuxinator/blob/master/LICENSE
    '''

    tmuxinator_yaml = """\
    project_name: sample
    project_root: ~/test
    socket_name: foo # Remove to use default socket
    pre: sudo /etc/rc.d/mysqld start # Runs before everything
    rbenv: 2.0.0-p247
    cli_args: -f ~/.tmux.mac.conf # Pass arguments to tmux
    tabs:
    - editor:
        pre:
            - echo "I get run in each pane, before each pane command!"
            -
        layout: main-vertical
        panes:
            - vim
            - #empty, will just run plain bash
            - top
    - shell: git pull
    - guard:
        layout: tiled
        pre:
            - echo "I get run in each pane."
            - echo "Before each pane command!"
        panes:
            -
            - #empty, will just run plain bash
            -
    - database: bundle exec rails db
    - server: bundle exec rails s
    - logs: tail -f log/development.log
    - console: bundle exec rails c
    - capistrano:
    - server: ssh user@example.com
    """

    tmuxinator_dict = {
        'project_name': 'sample',
        'project_root': '~/test',
        'socket_name': 'foo',
        'pre': 'sudo /etc/rc.d/mysqld start',
        'rbenv': '2.0.0-p247',
        'cli_args': '-f ~/.tmux.mac.conf',
        'tabs': [
            {
                'editor': {
                    'pre': [
                        'echo "I get run in each pane, before each pane command!"',
                        None
                    ],
                    'layout': 'main-vertical',
                    'panes': [
                        'vim',
                        None,
                        'top'
                    ]
                }
            },
            {'shell': 'git pull', },
            {
                'guard': {
                    'layout': 'tiled',
                    'pre': [
                        'echo "I get run in each pane."',
                        'echo "Before each pane command!"'
                    ],
                    'panes': [
                        None,
                        None,
                        None
                    ]
                }
            },
            {'database': 'bundle exec rails db'},
            {'server': 'bundle exec rails s'},
            {'logs': 'tail -f log/development.log'},
            {'console': 'bundle exec rails c'},
            {'capistrano': None},
            {'server': 'ssh user@example.com'}
        ]
    }

    tmuxp_dict = {
        'session_name': 'sample',
        'socket_name': 'foo',
        'config': '~/.tmux.mac.conf',
        'shell_command_before': [
            'sudo /etc/rc.d/mysqld start',
            'rbenv 2.0.0-p247'
        ],
        'windows': [
            {
                'window_name': 'editor',
                'shell_command_before': [
                    'echo "I get run in each pane, before each pane command!"',
                    None
                ],
                'layout': 'main-vertical',
                'panes': [
                    'vim',
                    None,
                    'top'
                ]
            },
            {
                'window_name': 'shell',
                'layout': 'layout',
                'panes': [
                    'git pull'
                ]
            },
            {
                'window_name': 'guard',
                'layout': 'tiled',
                'shell_command_before': [
                    'echo "I get run in each pane."',
                    'echo "Before each pane command!"'
                ],
                'panes': [
                    None,
                    None,
                    None
                ]
            },
            {
                'window_name': 'database',
                'panes': [
                    'bundle exec rails db'
                ]
            },
            {
                'window_name': 'server',
                'panes': [
                    'bundle exec rails s'
                ]
            },
            {
                'window_name': 'logs',
                'panes': [
                    'tail -f log/development.log'
                ]
            },
            {
                'window_name': 'console',
                'panes': [
                    'bundle exec rails c'
                ]
            },
            {
                'window_name': 'capistrano',
                'panes': [
                    None
                ]
            },
            {
                'window_name': 'server',
                'panes': [
                    'ssh user@example.com'
                ]
            }
        ]
    }

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.tmuxinator_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.tmuxinator_dict)

        self.assertDictEqual(tmuxinator_to_tmuxp(yaml_to_dict), self.tmuxp_dict)


class TmuxinatoriSampleTest(unittest.TestCase):

    '''https://github.com/aziz/tmuxinator/blob/master/spec/fixtures/sample.yml

    LICENSE: https://github.com/aziz/tmuxinator/blob/master/LICENSE
    '''

    tmuxinator_yaml = """\
    # ~/.tmuxinator/sample.yml
    # you can make as many tabs as you wish...

    name: sample
    root: ~/test
    socket_name: foo # Remove to use default socket
    pre: sudo /etc/rc.d/mysqld start # Runs before everything
    pre_window: rbenv shell 2.0.0-p247 # Runs in each tab and pane
    tmux_options: -f ~/.tmux.mac.conf # Pass arguments to tmux
    windows:
    - editor:
        pre:
            - echo "I get run in each pane, before each pane command!"
            -
        layout: main-vertical
        panes:
            - vim
            - #empty, will just run plain bash
            - top
    - shell:
        - git pull
        - git merge
    - guard:
        layout: tiled
        pre:
            - echo "I get run in each pane."
            - echo "Before each pane command!"
        panes:
            -
            - #empty, will just run plain bash
            -
    - database: bundle exec rails db
    - server: bundle exec rails s
    - logs: tail -f log/development.log
    - console: bundle exec rails c
    - capistrano:
    - server: ssh user@example.com
    """

    tmuxinator_dict = {
        'name': 'sample',
        'root': '~/test',
        'socket_name': 'foo',
        'tmux_options': '-f ~/.tmux.mac.conf',
        'pre': 'sudo /etc/rc.d/mysqld start',
        'pre_window': 'rbenv shell 2.0.0-p247',
        'windows': [
            {
                'editor': {
                    'pre': [
                        'echo "I get run in each pane, before each pane command!"',
                        None
                    ],
                    'layout': 'main-vertical',
                    'panes': [
                        'vim',
                        None,
                        'top'
                    ]
                }
            },
            {
                'shell': [
                    'git pull',
                    'git merge'
                ]
            },
            {
                'guard': {
                    'layout': 'tiled',
                    'pre': [
                        'echo "I get run in each pane."',
                        'echo "Before each pane command!"'
                    ],
                    'panes': [
                        None,
                        None,
                        None
                    ]
                }
            },
            {'database': 'bundle exec rails db'},
            {'server': 'bundle exec rails s'},
            {'logs': 'tail -f log/development.log'},
            {'console': 'bundle exec rails c'},
            {'capistrano': None},
            {'server': 'ssh user@example.com'}
        ]
    }

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.tmuxinator_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.tmuxinator_dict)

if __name__ == '__main__':
    unittest.main()