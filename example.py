# coding: utf-8

from __future__ import unicode_literals
from html_nested_tables import build_table_dict, build_optimal_table_dict, \
    v, h


d = (
    ('1901', (
        ('maison d’arrêt', (
            ('hommes', 50),
            ('femmes', 30),
        )),
        ('quartier de détention', (
            ('garçons', 8),
            ('jeunes filles', 1),
        )),
    )),
    ('1902', (
        ('maison d’arrêt', (
            ('hommes', 80),
            ('femmes', 40),
        )),
        ('quartier correctionnel', (
            ('hommes', 12),
            ('garçons', 3),
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
            ('garçons', 4),
        )),
        ('quartier de détention', (
            ('hommes', 6,),
            ('garçons', 2),
            ('jeunes filles', 1),
        )),
    )),
)


structures = ((a, b, c) for a in (v, h) for b in (v, h) for c in (v, h))
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
