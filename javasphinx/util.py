# Copyright (c) 2012 Bronto Software Inc.
# Licensed under the MIT License

import re

class StringBuilder(list):
    def build(self):
        return unicode(self)

    def __str__(self):
        return ''.join(self)

class Directive(object):

    def __init__(self, type, argument=''):
        self.type = type
        self.argument = argument

        self.options = []
        self.content = []

    def add_option(self, name, value=''):
        self.options.append((name, value))

    def add_content(self, o):
        assert o is not None
        self.content.append(o)

    def build(self):
        doc = Document()
        doc.add_line('.. %s:: %s' % (self.type, self.argument))

        for name, value in self.options:
            doc.add_line('   :%s: %s\n' % (name, value))

        content = Document()

        for obj in self.content:
            content.add_object(obj)

        doc.clear()
        for line in content.build().splitlines():
            doc.add_line('   ' + line)
        doc.clear()

        return doc.build()

class Document(object):
    remove_trailing_whitespace_re = re.compile('[ \t]+$', re.MULTILINE)
    collapse_empty_lines_re = re.compile('\n' + '{3,}', re.DOTALL)

    def __init__(self):
        self.content = []

    def add_object(self, o):
        assert o is not None

        self.content.append(o)

    def add(self, s):
        self.add_object(s)

    def add_line(self, s):
        self.add(s)
        self.add('\n')

    def add_heading(self, s, t='-'):
        self.add_line(s)
        self.add_line(t * len(s))

    def clear(self):
        self.add('\n\n')

    def build(self):
        output = StringBuilder()

        for obj in self.content:
            if isinstance(obj, Directive):
                output.append('\n\n')
                output.append(obj.build())
                output.append('\n\n')
            elif isinstance(obj, Document):
                output.append(obj.build())
            else:
                output.append(unicode(obj))

        output.append('\n\n')

        output = unicode(output)
        output = self.remove_trailing_whitespace_re.sub('', output)
        output = self.collapse_empty_lines_re.sub('\n\n', output)

        return output
