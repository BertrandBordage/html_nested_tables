# coding: utf-8

from __future__ import unicode_literals
from html_nested_tables import build_table_dict, build_optimal_table_dict, \
    get_all_structures


d = (
    ('1901', (
        ('maison d’arrêt', (
            ('hommes', 50),
            ('femmes', 30),
        )),
        ('quartier de détention', (
            ('garçons', (
                ('moins de 13 ans', 1),
                ('plus de 13 ans', 7),
            )),
            ('jeunes filles', 0),
        )),
    )),
    ('1902', (
        ('maison d’arrêt', (
            ('hommes', 80),
            ('femmes', 40),
        )),
        ('quartier correctionnel', (
            ('hommes', 12),
            ('garçons', (
                ('moins de 13 ans', 1),
                ('plus de 13 ans', 2),
            )),
        )),
    )),
    ('1903', (
        ('maison d’arrêt', (
            ('hommes', 70),
            ('femmes', 38),
            ('jeunes filles', 2),
        )),
        ('quartier correctionnel', (
            ('hommes', 5),
            ('garçons', (
                ('moins de 13 ans', 1),
                ('plus de 13 ans', 3),
            )),
        )),
        ('quartier de détention', (
            ('hommes', 6,),
            ('garçons', (
                ('moins de 13 ans', 0),
                ('plus de 13 ans', 2),
            )),
            ('jeunes filles', 1),
        )),
    )),
)


structures = get_all_structures(d)
tables = [build_table_dict(d, structure) for structure in structures]


with open('example.html', 'w') as f:
    f.write((
        '<style>table { border-collapse: collapse; }'
        'td, th { border: 1px solid grey; padding: 0 5px; }</style>'
        + '<h1>Optimal table</h1>'
        + build_optimal_table_dict(d).generate_html()
        + '<h1>All possible tables</h1>'
        + ''.join(repr(table.structure) +
                  ' ugliness : ' + str(table.get_ugliness()) +
                  table.generate_html() for table in tables)
    ).encode('utf-8'))
