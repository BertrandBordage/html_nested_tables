# coding: utf-8

from __future__ import unicode_literals, division
from collections import OrderedDict
from itertools import product


__all__ = (
    'TableDict', 'HorizontalTableDict', 'VerticalTableDict', 'h', 'v',
    'get_all_structures', 'build_table_dict', 'build_optimal_table_dict',
)


class TableDict(OrderedDict):
    """
    TableDict objects are ordered dicts with methods that renders HTML tables.

    Here is an ugly schema to define the terms I’m using::

                 hh1        hh2        hh3        hh4
              hh11 hh12  hh21 hh22  hh31 hh32  hh41 hh42

        vh1   dA   dB    dC   dE    dF   dG    dH   dI
        vh2   dJ   dK    dL   dM    dN   dO    dP   dQ
        vh3   dR   dS    dT   dU    dV   dW    dX   dY

    `hh1`, `hh11`, `hh2` […] are horizontal headers,
    `vh1`, `vh2`, […] are vertical headers,
    and `dA`, `dB`, […] are data.
    """

    structure = ()
    direction = None

    def _get_headers(self, side):
        """
        Builds an nested headers list based on the side of the headers.

        This is a mix between lists and association lists, since we need to
        know which header(s) are nested inside which header(s).

        The returned value looks like:
        ['header1', 'header2', 'header3']
        or
        [['header1', ['header11', 'header12'], ['header2', ['header22']]]

        :arg unicode side: Side of the headers, ``'vertical'``
                           or ``'horizontal'``.
        :returns: A nested headers list.
        :rtype: list
        """

        DictClass = {'vertical': VerticalTableDict,
                     'horizontal': HorizontalTableDict}[side]
        headers = []
        for k, v in self.items():
            if isinstance(v, TableDict):
                child_headers = getattr(v, side + '_headers')()
                if child_headers:
                    if isinstance(self, DictClass):
                        headers.append([k, child_headers])
                    else:
                        for h in child_headers:
                            if h not in headers:
                                headers.append(h)
                    continue
            if isinstance(self, DictClass) and k not in headers:
                headers.append(k)
        return headers

    def horizontal_headers(self):
        return self._get_headers('horizontal')

    def vertical_headers(self):
        return self._get_headers('vertical')

    @staticmethod
    def _get_headers_depth(headers):
        """
        Returns the max depth of ``headers``.

        We cheat a bit, since the headers syntax is a mix between list and
        association list.

        :arg list headers: Can be gotten from ``TableDict._get_headers``.
        :returns: The max depth of ``headers``.
        :rtype: int

        >>> TableDict._get_headers_depth([1, 2, 3])
        1
        >>> TableDict._get_headers_depth([[1, [11, 12], [2, [21, 22]]]])
        2
        >>> TableDict._get_headers_depth([[1, [[11, [111, 112]]]]])
        3
        """

        # Taken from http://stackoverflow.com/a/6039138/1576438
        def max_depth(l):
            return isinstance(l, list) and max(map(max_depth, l)) + 1

        if not headers:
            return 1
        d = max_depth(headers)
        return d - d // 2

    @classmethod
    def _get_final_length(cls, l):
        """
        Returns the total length of the deepest lists inside ``ŀ``.

        :arg list l: A nested list.
        :returns: The total length of the deepest lists inside ``l``.
        :rtype: int

        >>> TableDict._get_final_length([['a', [1, 2, 3]], ['b', [4, 5]]])
        5
        """

        total = 0
        for item in l:
            if isinstance(item, list):
                header, group = item
                total += cls._get_final_length(group)
            else:
                total += 1
        return total

    def _horizontal_header_iterator(self, headers=None, depth=0):
        """
        Returns a generator that iterates over horizontal headers.

        This is designed to ease HTML generation.
        """

        to_be_explored = []
        headers = headers or self.horizontal_headers()
        for item in headers:
            if isinstance(item, list):
                header, group = item
                yield header, depth, {'colspan': self._get_final_length(group)}
                to_be_explored.extend(group)
            else:
                yield item, depth, {}
        if to_be_explored:
            for header, depth, props in self._horizontal_header_iterator(
                    to_be_explored, depth + 1):
                yield header, depth, props

    def _vertical_header_iterator(self, headers=None, depth=0):
        """
        Returns a generator that iterates over vertical headers.

        This is designed to ease HTML generation.
        """

        headers = headers or self.vertical_headers()
        for item in headers:
            if isinstance(item, list):
                header, group = item
                yield header, depth, {'rowspan': self._get_final_length(group)}
                for subheader, subdepth, subprops \
                        in self._vertical_header_iterator(group, depth + 1):
                    yield subheader, subdepth, subprops
            else:
                yield item, depth, {}

    def _accessors_iterator(self, headers, parent_accessors=()):
        """
        Returns a generator that allows to iterate over accessors to pieces of
        data.

        It is used to iterate easily over data.

        :arg list headers: Can be gotten from ``TableDict._get_headers``.
        :arg tuple parent_accessors: Parent accessors of ``headers``.  This is
                                     only used internally for recursion.
        :returns: A generator that iterates over tuples containing successive
                  accessors for a piece of data.
        :rtype: generator of tuple
        """

        for accessor in headers:
            if isinstance(accessor, list):
                header, group = accessor
                for sub_accessor in self._accessors_iterator(
                        group, parent_accessors + (header,)):
                    yield sub_accessor
            else:
                yield parent_accessors + (accessor,)

    def _data_iterator(self):
        """
        Returns a generator that iterates over data.

        This is designed to ease HTML generation.
        """

        def inner_generator(vertical_accessor, horizontal_accessor):
            v = self
            x, y = 0, 0
            for table_class in self.structure:
                try:
                    if table_class.direction == 'horizontal':
                        v = v[horizontal_accessor[x]]
                        x += 1
                    else:
                        v = v[vertical_accessor[y]]
                        y += 1
                except KeyError:
                    v = None
                    break
            return v

        vertical_accessors = \
            list(self._accessors_iterator(self.vertical_headers())) \
            or (None,)
        horizontal_accessors = \
            list(self._accessors_iterator(self.horizontal_headers())) \
            or (None,)
        for vertical_accessor in vertical_accessors:
            for horizontal_accessor in horizontal_accessors:
                yield inner_generator(vertical_accessor, horizontal_accessor)

    @staticmethod
    def tag(name, props, content):
        props_str = ' '.join('%s="%s"' % (k, v) for k, v in props.items())
        return '<%s %s>%s</%s>' % (name, props_str, content, name)

    def generate_html(self):
        """
        Generates an HTML table from the contents of ``self``.

        It creates an empty cell first, adds horizontal headers, then adds both
        vertical headers and data in the same time.

        This whole thing could be implemented using BeautifulSoup and its
        outstanding inplace modification possibilities.  That may be much more
        readable, but also much slower.

        :returns: A HTML table.
        :rtype: unicode
        """

        horizontal_headers = self.horizontal_headers()
        vertical_headers = self.vertical_headers()

        out = '<table>'
        if horizontal_headers:
            out += '<tr>'
            if vertical_headers:
                # Creates the top left empty cell.
                out += '<td colspan="%s" rowspan="%s" style="border: none;">' \
                    % (self._get_headers_depth(vertical_headers),
                       self._get_headers_depth(horizontal_headers))
            # Creates horizontal headers.
            previous_depth = 0
            for header, depth, props \
                    in self._horizontal_header_iterator(horizontal_headers):
                if depth != previous_depth:
                    out += '</tr><tr>'
                    previous_depth = depth
                out += self.tag('th', props, header)

        horizontal_length = self._get_final_length(horizontal_headers) or 1
        max_vertical_depth = self._get_headers_depth(vertical_headers) or 1

        def display_data(data_index=0):
            out = ''
            for data in list(self._data_iterator())[
                    horizontal_length * data_index:
                    horizontal_length * (data_index + 1)]:
                out += '<td>%s</td>' % (data or '-')
            return out

        # Creates lines of vertical headers et data.
        if vertical_headers:
            previous_depth = 0
            data_index = -1
            for header, depth, props \
                    in self._vertical_header_iterator(vertical_headers):
                if depth <= previous_depth:
                    out += '</tr><tr>'
                    data_index += 1
                out += self.tag('th', props, header)
                if depth == max_vertical_depth - 1:
                    if data_index != -1:
                        out += display_data(data_index)
                previous_depth = depth
        else:
            out += '</tr><tr>' + display_data() + '</tr>'
        out += '</table>'
        return out

    def get_ugliness(self):
        """
        Returns the ugliness of the current table.

        The uglier a table is, the less readable it becomes.

        :returns: The ugliness of the current table.
        :rtype: int
        """

        vertical_length = self._get_final_length(self.vertical_headers())
        horizontal_length = self._get_final_length(self.horizontal_headers())
        ugliness = vertical_length + horizontal_length
        ugliness += abs(vertical_length - horizontal_length)
        return ugliness


class HorizontalTableDictMeta(type):
    def __repr__(cls):
        return 'h'


class VerticalTableDictMeta(type):
    def __repr__(cls):
        return 'v'


class HorizontalTableDict(TableDict):
    """
    Same as :class:`TableDict`, but with a direction.

    The direction is used to specify whether the headers of the first depth
    of the current object should be put on the horizontal or vertical axis.
    """

    __metaclass__ = HorizontalTableDictMeta
    direction = 'horizontal'


class VerticalTableDict(TableDict):
    __doc__ = HorizontalTableDict.__doc__
    __metaclass__ = VerticalTableDictMeta
    direction = 'vertical'


h = HorizontalTableDict
v = VerticalTableDict


def get_all_structures(datadict):
    """
    Returns all the possible structures for a datadict.

    :arg datadict: Nested dicts or association lists.  Association lists have
                   the advantage of being ordered.
    :returns: All possible structures.
    :rtype: list
    """

    return list(product((v, h), repeat=len(datadict)))


def build_table_dict(datadict, structure):
    """
    Automatically builds a TableDict from ``datadict`` and ``structure``.

    :arg datadict: Nested dicts or association lists.  Association lists have
                   the advantage of being ordered.
    :type datadict: dict or tuple or list
    :arg structure: Structure of the headers of the returned object.  This
                    must be a sequence of ``h`` and/or ``v``,
                    one per depth level of ``datadict``.
    :type structure: list or tuple
    :returns: Nested :class:`TableDict` s with horizontal and/or vertical
              structures applied, according to ``structure``.
    :rtype: HorizontalTableDict or VerticalTableDict
    """

    def apply_structure(datadict, structure, level=0):
        datadict = structure[level](datadict)
        for k, v in datadict.items():
            if isinstance(v, tuple):
                datadict[k] = apply_structure(v, structure, level + 1)
        return datadict

    new = apply_structure(datadict, structure)
    new.structure = structure
    return new


def build_optimal_table_dict(datadict):
    """
    Automatically builds the less ugly table possible from ``datadict``.

    :arg datadict: Nested dicts or association lists.  Association lists have
                   the advantage of being ordered.
    :type datadict: dict or tuple or list
    :returns: Nested :class:`TableDict` with horizontal and/or vertical
                  structures applied, according to ``structure``.
    :rtype: HorizontalTableDict or VerticalTableDict
    """

    structures = get_all_structures(datadict)
    tables = [build_table_dict(datadict, structure)
              for structure in structures]
    return sorted(tables, key=lambda t: t.get_ugliness())[0]
