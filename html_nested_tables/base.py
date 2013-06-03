# coding: utf-8

from __future__ import unicode_literals, division
from collections import OrderedDict
from itertools import product


__all__ = (
    'HORIZONTAL', 'VERTICAL',
    'TableDict', 'HorizontalTableDict', 'VerticalTableDict', 'h', 'v',
    'get_all_structures', 'build_table_dict', 'build_optimal_table_dict',
)


HORIZONTAL = 'horizontal'
VERTICAL = 'vertical'


def build_tag(name, props, content):
    props_str = ' '.join('%s="%s"' % (k, v) for k, v in props.items())
    return '<%s %s>%s</%s>' % (name, props_str, content, name)


class TableDict(OrderedDict):
    """
    TableDict objects are ordered dicts with methods that renders HTML tables.

    Here is an ugly schema to define the terms I’m using:

    +---------+-------------+-------------+-------------+-------------+
    |         |     hh1     |     hh2     |     hh3     |     hh4     |
    |         +------+------+------+------+------+------+------+------+
    |         | hh11 | hh12 | hh21 | hh22 | hh31 | hh32 | hh41 | hh42 |
    +=========+======+======+======+======+======+======+======+======+
    | **vh1** |  dA  |  dB  |  dC  |  dE  |  dF  |  dG  |  dH  |  dI  |
    +---------+------+------+------+------+------+------+------+------+
    | **vh2** |  dJ  |  dK  |  dL  |  dM  |  dN  |  dO  |  dP  |  dQ  |
    +---------+------+------+------+------+------+------+------+------+
    | **vh3** |  dR  |  dS  |  dT  |  dU  |  dV  |  dW  |  dX  |  dY  |
    +---------+------+------+------+------+------+------+------+------+

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

        DictClass = {HORIZONTAL: HorizontalTableDict,
                     VERTICAL: VerticalTableDict}[side]
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
        return self._get_headers(HORIZONTAL)

    def vertical_headers(self):
        return self._get_headers(VERTICAL)

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
            return isinstance(l, (list, tuple, dict)) and max(map(max_depth, l)) + 1

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
            if isinstance(item, (list, tuple)):
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
        max_depth = self._get_headers_depth(self.horizontal_headers())
        for item in headers:
            group = None
            if isinstance(item, list):
                header, group = item
                props = {'colspan': self._get_final_length(group)}
                to_be_explored.extend(group)
            else:
                header = item
                props = {}
            if not group and depth <= max_depth:
                props['rowspan'] = max_depth - depth
            yield header, depth, props, not group
        if to_be_explored:
            for subheader, subdepth, subprops, is_leaf \
                in self._horizontal_header_iterator(
                    to_be_explored, depth + 1):
                yield subheader, subdepth, subprops, is_leaf

    def _vertical_header_iterator(self, headers=None, depth=0):
        """
        Returns a generator that iterates over vertical headers.

        This is designed to ease HTML generation.
        """

        headers = headers or self.vertical_headers()
        max_depth = self._get_headers_depth(self.vertical_headers())
        for item in headers:
            group = None
            if isinstance(item, list):
                header, group = item
                props = {'rowspan': self._get_final_length(group)}
            else:
                header = item
                props = {}
            if not group and depth <= max_depth:
                props['colspan'] = max_depth - depth
            yield header, depth, props, not group
            if group:
                for subheader, subdepth, subprops, is_leaf \
                        in self._vertical_header_iterator(group, depth + 1):
                    yield subheader, subdepth, subprops, is_leaf

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

    def _horizontal_accessors(self):
        if not hasattr(self, '__horizontal_accessors'):
            self.__horizontal_accessors = list(
                self._accessors_iterator(self.horizontal_headers()))
        return self.__horizontal_accessors

    def _vertical_accessors(self):
        if not hasattr(self, '__vertical_accessors'):
            self.__vertical_accessors = list(
                self._accessors_iterator(self.vertical_headers()))
        return self.__vertical_accessors

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
                    if table_class.direction == HORIZONTAL:
                        accessor = horizontal_accessor[x]
                        x += 1
                    else:
                        accessor = vertical_accessor[y]
                        y += 1
                except IndexError:
                    break
                try:
                    v = v[accessor]
                except (TypeError, KeyError):
                    return

            if isinstance(v, TableDict):
                return

            return v

        vertical_accessors = self._vertical_accessors() or (None,)
        horizontal_accessors = self._horizontal_accessors() or (None,)
        for vertical_accessor in vertical_accessors:
            for horizontal_accessor in horizontal_accessors:
                yield inner_generator(vertical_accessor, horizontal_accessor)

    def _get_data(self):
        if not hasattr(self, '__data'):
            self.__data = list(self._data_iterator())
        return self.__data

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
            for header, depth, props, is_leaf \
                    in self._horizontal_header_iterator(horizontal_headers):
                if depth != previous_depth:
                    out += '</tr><tr>'
                    previous_depth = depth
                out += build_tag('th', props, header)

        horizontal_length = self._get_final_length(horizontal_headers) or 1

        def display_data(data_index=0):
            out = ''
            for data in self._get_data()[
                    horizontal_length * data_index:
                    horizontal_length * (data_index + 1)]:
                out += '<td>%s</td>' % ('-' if data is None else data)
            return out

        # Creates lines of vertical headers et data.
        if vertical_headers:
            previous_depth = 0
            data_index = -1
            for header, depth, props, is_leaf \
                    in self._vertical_header_iterator(vertical_headers):
                if depth <= previous_depth:
                    out += '</tr><tr>'
                    data_index += 1
                out += build_tag('th', props, header)
                if is_leaf:
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
    direction = HORIZONTAL


class VerticalTableDict(TableDict):
    __doc__ = HorizontalTableDict.__doc__
    __metaclass__ = VerticalTableDictMeta
    direction = VERTICAL


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

    return list(product((v, h), repeat=TableDict._get_headers_depth(datadict)))


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
