# Copyright (c) 2012 Bronto Software Inc.
# Licensed under the MIT License

from docutils import nodes, utils
from sphinx.util.nodes import split_explicit_title

def get_javadoc_ref(app, rawtext, text):
    javadoc_url_map = app.config.javadoc_url_map

    # Add default sources
    javadoc_url_map["java"] = ("http://docs.oracle.com/javase/6/docs/api", 'javadoc')
    javadoc_url_map["javax"] = ("http://docs.oracle.com/javase/6/docs/api", 'javadoc')
    javadoc_url_map["org.xml"] = ("http://docs.oracle.com/javase/6/docs/api", 'javadoc')
    javadoc_url_map["org.w3c"] = ("http://docs.oracle.com/javase/6/docs/api", 'javadoc')

    source = None
    package = ''
    method = None

    if '(' in text:
        split_point = text.rindex('.', 0, text.index('('))
        method = text[split_point + 1:]
        text = text[:split_point]

    for pkg, (baseurl, ext_type) in javadoc_url_map.items():
        if text.startswith(pkg + '.') and len(pkg) > len(package):
            source = baseurl, ext_type

    if not source:
        return None

    baseurl, ext_type = source

    package_parts = []
    cls_parts = []

    for part in text.split('.'):
        if cls_parts or part[0].isupper():
            cls_parts.append(part)
        else:
            package_parts.append(part)

    package = '.'.join(package_parts)
    cls = '.'.join(cls_parts)

    if not baseurl.endswith('/'):
        baseurl = baseurl + '/'

    if ext_type == 'javadoc':
        source = baseurl + package.replace('.', '/') + '/' + cls + '.html'
        if method:
            source = source + '#' + method
    elif ext_type == 'sphinx':
        source = baseurl + package.replace('.', '/') + '/' + cls.replace('.', '-') + '.html'
        if method:
            source = source + '#' + package + '.' + cls + '.' + method
    else:
        raise ValueError('invalid target specifier ' + ext_type)

    title = '.'.join(filter(None, (package, cls, method)))
    node = nodes.reference(rawtext, '')
    node['refuri'] = source
    node['reftitle'] = title

    return node

def javadoc_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """ Role for linking to external Javadoc """

    has_explicit_title, title, target = split_explicit_title(text)
    title = utils.unescape(title)
    target = utils.unescape(target)

    if not has_explicit_title:
        target = target.lstrip('~')

        if title[0] == '~':
            title = title[1:].rpartition('.')[2]

    app = inliner.document.settings.env.app
    ref = get_javadoc_ref(app, rawtext, target)

    if not ref:
         raise ValueError("no Javadoc source found for %s in javadoc_url_map" % (target,))

    ref.append(nodes.Text(title, title))

    return [ref], []
