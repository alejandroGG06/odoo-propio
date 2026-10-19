{
    'name': 'Serv portal signing',
    'version': '18.0.0.0.0',
    'category': 'Tools',
    'author': 'Servinnova',
    'summary': ' integrates document portal signing.',
    'depends': ['base', 'contacts','project'],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_sign_views.xml',
        'views/project_task_views.xml',
        
    ],
    
    'assets': {
    'web.assets_frontend': [
        'serv_project_sign/static/src/js/portal_signature.js',
    ],
},
   
    'installable': True,
    'application': False,
    'License': 'LGPL-3',
}  
