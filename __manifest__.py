{
    'name': "Construction Management",
    'author': "Mohammed Hesham",
    'category': '',
    'version': '17.0.0.1.0',
    'depends': ['base', 'contacts', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/project_sequence.xml',
        'data/site_sequence.xml',
        'data/workforce_sequence.xml',
        'views/construction_menu.xml',
        'views/construction_project_view.xml',
        'views/construction_site_view.xml',
        'views/construction_workforce_view.xml',
    ],

    'application': True,
}
