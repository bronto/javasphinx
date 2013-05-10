# Copyright (c) 2012 Bronto Software Inc.
# Licensed under the MIT License

import collections
import re
from xml.sax.saxutils import escape as html_escape

from bs4 import BeautifulSoup

unknown_tags = set()

def separate(s, strip=True):
    if strip:
        s = s.strip()
    return u'\n\n' + s + u'\n\n'

def header(s, c):
    s = s.strip()
    return separate('**' + s + '**')

def inline(f, sub):
    # Seems fishy if our inline markup spans lines. We will instead just return
    # the string as is
    if sub.find('\n') != -1:
        return sub

    # There must be contents for the inline formatter
    if sub.strip() == '':
        return ''

    if not isinstance(f, unicode):
        f = unicode(f)

    # Format as inline with escaped spaces on both sides so that docutils
    # doesn't mistake the markup as literals
    return '\\ ' + f.format(sub.strip()) + '\\ '

def left_justify(s):
    lines = s.split('\n')
    n = 1

    while True:
        prefixes = set(l[:n] for l in lines)

        if len(prefixes) > 1 or prefixes.pop().strip() != '':
            break

        n = n + 1

    return '\n'.join(l[n - 1:] for l in lines)

def _process(node):
    if isinstance(node, basestring):
        return re.sub(r'[\s\n]+', ' ', node.strip('\n'))

    tags = {
        'b'      : lambda s: inline(u'**{0}**', s),
        'strong' : lambda s: inline(u'**{0}**', s),
        'i'      : lambda s: inline(u'*{0}*', s),
        'em'     : lambda s: inline(u'*{0}*', s),
        'tt'     : lambda s: inline(u'``{0}``', s),
        'code'   : lambda s: inline(u'``{0}``', s),
        'sub'    : lambda s: inline(u':sub:`{0}`', s),
        'sup'    : lambda s: inline(u':sup:`{0}`', s),
        'hr'     : lambda s: separate(''), # Transitions not allowed
        'p'      : lambda s: separate(s),
        'h1'     : lambda s: header(s, '#'),
        'h2'     : lambda s: header(s, '*'),
        'h3'     : lambda s: header(s, '='),
        'h4'     : lambda s: header(s, '-'),
        'h5'     : lambda s: header(s, '^'),
        'h6'     : lambda s: header(s, '"')
        }

    text_only = set(('b', 'strong', 'i', 'em', 'tt', 'code', 'sub', 'sup',
                     'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'))

    if node.name in tags:
        if node.name in text_only:
            return tags[node.name](_process_text(node))
        else:
            return tags[node.name](_process_children(node))

    if node.name == 'pre':
        text = left_justify(_process_text(node))
        lines = text.split('\n')
        lines = ['   ' + l for l in lines]
        return separate('.. parsed-literal::') + separate('\n'.join(lines), False)

    if node.name == 'a':
        if 'name' in node.attrs:
            return separate('.. _' + node['name'] + ':')
        elif 'href' in node.attrs:
            target = node['href']

            if target.startswith('#'):
                label = re.sub(r'[\s\n]+', ' ', _process_text(node).strip('\n'))
                return inline(u':ref:`{{0}} <{0}>`'.format(target[1:]), label)
            elif target.startswith('@'):
                label = re.sub(r'[\s\n]+', ' ', _process_text(node).strip('\n'))
                if label:
                    return inline(u':java:ref:`{{0}} <{0}>`'.format(target[1:]), label)
                else:
                    return inline(u':java:ref:`{0}`', target[1:])
            else:
                label = re.sub(r'[\s\n]+', ' ', _process_text(node).strip('\n'))
                return inline(u'`{{0}} <{0}>`_'.format(target), label)

    if node.name == 'ul':
        items = [_process(n) for n in node.find_all('li', recursive=False)]
        items = ['* ' + item for item in items]
        items = '\n'.join(items)
        lines = items.split('\n')
        lines = ['  ' + l for l in lines]

        return separate('..') + separate('\n'.join(lines), False)

    if node.name == 'ol':
        items = [_process(n) for n in node.find_all('li', recursive=False)]
        items = ['# ' + item for item in items]
        items = '\n'.join(items)
        lines = items.split('\n')
        lines = ['  ' + l for l in lines]

        return separate('..') + separate('\n'.join(lines), False)

    if node.name == 'li':
        s = _process_children(node)
        s = s.strip()

        # If it's multiline clear the end to correcly support nested lists
        if s.find('\n') != -1:
            s = s + '\n\n'

        return s

    if node.name == 'table':
        return _process_table(node)

    unknown_tags.add(node.name)

    return _process_children(node)

Cell = collections.namedtuple('Cell', ['type', 'rowspan', 'colspan', 'contents'])

def _get_table_rows(table):
    return table.find_all('tr', recursive=False)

def _get_table_cells(row):
    cells = []

    for c in row.contents:
        if getattr(c, 'name', 'str') in ('td', 'th'):
            cells.append(c)

    return cells

def _process_cell(cell, row_num):
    cell_type = cell.name
    rowspan = int(cell.attrs.get('rowspan', 1))
    colspan = int(cell.attrs.get('colspan', 1))
    contents =_process_children(cell)

    if cell_type == 'th' and row_num > 0:
        contents = inline(u'**{0}**', contents)

    return Cell(cell_type, rowspan, colspan, contents)

def _process_table(node):
    rows = []

    for tr in _get_table_rows(node):
        row = []
        for cell in _get_table_cells(tr):
            row.append(_process_cell(cell, len(rows)))
        rows.append(row)

    normalized = []

    width = max(sum(c.colspan for c in row) for row in rows) if rows else 0

    for row in rows:
        row_width = sum(c.colspan for c in row)

        if row_width < width:
            cell_type = row[-1].type if row else 'td'
            row.append(Cell(cell_type, width - row_width, 1, ''))

    col_widths = [0] * width
    row_heights = [0] * len(rows)

    i = 0

    for row in rows:
        j = 0
        for cell in row:
            current_w = sum(col_widths[j:j + cell.colspan])
            required_w = max(len(l) for l in cell.contents.split('\n'))

            if required_w > current_w:
                additional = required_w - current_w
                col_widths[j] += additional - (cell.colspan - 1) * (additional // cell.colspan)
                for jj in range(j + 1, j + cell.colspan):
                    col_widths[jj] += (additional // cell.colspan)

            current_h = row_heights[i]
            required_h = len(cell.contents.split('\n'))

            if required_h > current_h:
                row_heights[i] = required_h

            j += cell.colspan
        i += 1

    row_sep = '+' + '+'.join('-' * (l + 2) for l in col_widths) + '+'
    header_sep = '+' + '+'.join('=' * (l + 2) for l in col_widths) + '+'
    lines = [row_sep]

    i = 0

    for row in rows:
        for y in range(0, row_heights[i]):
            line = []
            j = 0
            for c in row:
                w = sum(n + 3 for n in col_widths[j:j+c.colspan]) - 2
                h = row_heights[i]

                line.append('| ')
                cell_lines = c.contents.split('\n')
                content = cell_lines[y] if y < len(cell_lines) else ''
                line.append(content.ljust(w))
                j += 1
            line.append('|')
            lines.append(''.join(line))

        if i == 0 and all(c.type == 'th' for c in row):
            lines.append(header_sep)
        else:
            lines.append(row_sep)

        i += 1

    return separate('\n'.join(lines))

def _smart_join(parts):
    new_parts = []
    clear = False

    for part in parts:
        if not part:
            continue

        if clear:
            new_parts.append(part.lstrip())
        else:
            new_parts.append(part)

        clear = (part[-1] == '\n')

    return ''.join(new_parts)

def _process_children(node):
    parts = []

    for c in node.contents:
        parts.append(_process(c))
    out = _smart_join(parts)

    return out

def _process_text(node):
    return ''.join(node.strings)

def _find_javadoc_tag_end(s, i):
    j = i + 1

    while s.count('{', i, j) != s.count('}', i, j):
        j = s.find('}', j) + 1

        if j == 0:
            return len(s)

    return j

def _replace_javadoc_tags(tag, f, s):
    parts = []
    search = '{@' + tag

    i = s.find(search)
    j = 0

    while i != -1:
        parts.append(s[j:i])

        j = _find_javadoc_tag_end(s, i)
        parts.append(f(s[i + len(search):j - 1].strip()))
        i = s.find(search, j)

    parts.append(s[j:])
    return ''.join(parts)

def _replace_inline_tags_pre_html(s):
    # Escape contents of {@code ...} tags and put inside of <code></code> tags
    s = _replace_javadoc_tags('code',
                          lambda m: '<code>%s</code>' % (html_escape(m),),
                          s)

    # Escape contents of {@literal ...} tags and put inside of <span></span> tags
    s = _replace_javadoc_tags('literal',
                          lambda m: '<span>%s</span>' % (html_escape(m),),
                          s)

    # Just remove @docRoot tags
    s = _replace_javadoc_tags('docRoot', lambda m: '', s)

    # Precondition internal links
    s = _replace_javadoc_tags('linkplain', _replace_javadoc_link, s)
    s = _replace_javadoc_tags('link', _replace_javadoc_link, s)

    return s

def _replace_javadoc_link(s):
    s = s.strip().replace('\t', ' ').replace('\n', ' ')
    target = None
    label = ''

    if ' ' not in s:
        target = s
    else:
        i = s.find(' ')

        while s.count('(', 0, i) != s.count(')', 0, i):
            i = s.find(' ', i + 1)

            if i == -1:
                i = len(s)
                break

        target = s[:i]
        label = s[i:]

    if target[0] == '#':
        target = target[1:]

    target = target.replace('#', '.').replace(' ', '').strip()
    label = label.strip()

    return r'<a href="@%s">%s</a>' % (target, label)

def _condition_anchors_pre_html(s):
    # Add closing tags to all anchors so they are better handled by the parser
    s = re.sub(r'<a\s+name\s*=\s*["\']?(.+?)["\']?\s*>', r'<a name="\1"></a>', s)

    return s

def convert(s_html):
    if not isinstance(s_html, unicode):
        s_html = unicode(s_html, 'utf8')

    # Convert Javadoc tags to psuedo-HTML
    s_html = _replace_inline_tags_pre_html(s_html)

    # Make sure all anchor tags are closed
    s_html = _condition_anchors_pre_html(s_html)

    if not s_html.strip():
        return ''

    soup = BeautifulSoup(s_html, 'lxml')
    top = soup.html.body

    result = _process_children(top)
    result = re.compile(r'^\s+$', re.MULTILINE).sub('', result)
    result = re.compile(r'\n{3,}').sub('\n\n', result)
    result = result.strip()

    return result

if __name__ == '__main__':
    import sys
    import javalang
    import time

    f = sys.argv[1]
    s = open(f).read()

    matches = re.findall(r'/\*\*.*?\*/', s, re.MULTILINE | re.DOTALL)

    for match in matches:
        doc = javalang.javadoc.parse(match).description

        t = time.time()
        print doc
        print '^' * 80
        print convert_1(doc)
        print '-' * 80
        print
        print

    print
    print '-' * 80
    print 'Generated in %.3f ms' % (1000 * (time.time() - t),)
    print 'Unknown tags:', ' '.join(unknown_tags)
