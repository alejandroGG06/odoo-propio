{
    'name': 'Serv autofirma',
    'version': '18.0.0.0.0',
    'category': 'Tools',
    'author': 'Alejandro grajales',
    'summary': ' integrates the autofirma signing tool with Odoo for digital document signing.',
    'depends': ['base', 'contacts', 'sale_management'],
    'data': [
    ],
    'data': [
        'views/serv_autofirma_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 1. Cargamos primero la librería del Gobierno (se asume que guardaste ahí el código)
            'serv_autofirma/static/lib/autoscript.js',
            # 2. Cargamos el parche en OWL que interactúa con las vistas de Odoo 18
            'serv_autofirma/static/src/js/sale_order_sign.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}  
