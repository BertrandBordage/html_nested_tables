# coding: utf-8

import os.path
import unittest
from html_nested_tables import build_optimal_table_dict, build_table_dict, h, v


PATH = os.path.abspath(os.path.dirname(__file__))
CONTROL_TABLES_DIR = 'control_tables/'
CONTROL_TABLES_PATH = os.path.join(PATH, CONTROL_TABLES_DIR)
FAILED_TESTS_DIR = 'failed/'
FAILED_TESTS_PATH = os.path.join(PATH, FAILED_TESTS_DIR)
if not os.path.exists(FAILED_TESTS_PATH):
    os.makedirs(FAILED_TESTS_PATH)


class TableTest(unittest.TestCase):
    def assertEqualControl(self, html, filename, result_filename=None):
        absolute_file_path = os.path.join(CONTROL_TABLES_PATH, filename)
        control = open(absolute_file_path).read()
        if html != control:
            with open(os.path.join(FAILED_TESTS_PATH,
                                   result_filename or filename), 'w') as f:
                f.write('<p>Control table:</p>' + control
                        + '<p>Failed result:</p>' + html)
        self.assertEqual(html, control)


class Level1TableTest(TableTest):
    def setUp(self):
        self.data = (
            ('a', 1),
            ('b', 2),
            ('c', 3),
        )

    def testHorizontal(self):
        html = build_table_dict(self.data, (h,)).generate_html()
        self.assertEqualControl(html, 'level_1_h.html')

    def testVertical(self):
        html = build_table_dict(self.data, (v,)).generate_html()
        self.assertEqualControl(html, 'level_1_v.html')

    def testOptimal(self):
        html = build_optimal_table_dict(self.data).generate_html()
        self.assertEqualControl(html, 'level_1_v.html', 'level_1_optimal.html')


class Level2TableTest(TableTest):
    def setUp(self):
        self.data = (
            ('a', (
                ('aa', 11),
                ('ab', 12),
            )),
            ('b', (
                ('ba', 21),
                ('bb', 22),
                ('bc', 23),
            )),
            ('c', (
                ('ca', 31),
            )),
        )

    def testHorizontal(self):
        html = build_table_dict(self.data, (h, h)).generate_html()
        self.assertEqualControl(html, 'level_2_hh.html')

    def testHorizontalVertical(self):
        html = build_table_dict(self.data, (h, v)).generate_html()
        self.assertEqualControl(html, 'level_2_hv.html')

    def testVerticalHorizontal(self):
        html = build_table_dict(self.data, (v, h)).generate_html()
        self.assertEqualControl(html, 'level_2_vh.html')

    def testVertical(self):
        html = build_table_dict(self.data, (v, v)).generate_html()
        self.assertEqualControl(html, 'level_2_vv.html')

    def testOptimal(self):
        html = build_optimal_table_dict(self.data).generate_html()
        self.assertEqualControl(html, 'level_2_vv.html',
                                'level_2_optimal.html')


class MixedLevelsTableTest(TableTest):
    def setUp(self):
        self.data = (
            ('a', (
                ('aa', 11),
                ('ab', 12),
            )),
            ('b', 2),
        )

    def testHorizontal(self):
        html = build_table_dict(self.data, (h, h)).generate_html()
        self.assertEqualControl(html, 'level_mixed_hh.html')

    # FIXME: How should we render such a case?
    # def testHorizontalVertical(self):
    #     html = build_table_dict(self.data, (h, v)).generate_html()
    #     self.assertEqualControl(html, 'level_mixed_hv.html')

    # FIXME: How should we render such a case?
    # def testVerticalHorizontal(self):
    #     html = build_table_dict(self.data, (v, h)).generate_html()
    #     self.assertEqualControl(html, 'level_mixed_vh.html')

    def testVertical(self):
        html = build_table_dict(self.data, (v, v)).generate_html()
        self.assertEqualControl(html, 'level_mixed_vv.html')

    # FIXME: How should we render it?
    # def testOptimal(self):
    #     html = build_optimal_table_dict(self.data).generate_html()
    #     self.assertEqualControl(html, 'level_mixed_hh.html',
    #                             'level_mixed_optimal.html')


if __name__ == '__main__':
    unittest.main()
