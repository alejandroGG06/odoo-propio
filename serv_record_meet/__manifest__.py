# -*- coding: utf-8 -*-
{
    'name': 'serv record meet',
    'version': '18.0.2.0.1',
    'author': 'Servinnova',
    'category': 'Productivity/Discuss',
    'summary': 'Permite grabar la pantalla durante las llamadas de Odoo Discusión.',
    'depends': ['mail'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'serv_record_meet/static/src/components/call_action_list/call_action_list.xml',
            'serv_record_meet/static/src/components/call_action_list/call_action_list.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}