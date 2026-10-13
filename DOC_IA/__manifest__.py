{
    'name': 'DOC_IA',
    'version': '1.0',
    'category': 'Tools',
    'Author': 'Alejandro/Servinnova',
    'summary': 'Modulo personal para la generacion de documentos informativos con ia sobre los modulos de Odoo',
    'depends': ['base', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/generador_views.xml',
        'views/facturas_generador_view.xml',
        'views/crm_inherit_view.xml',
        'views/facturas_xml.xml'
    ],

    'installable': True,
    'application': True,
    


}