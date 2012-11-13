
from docutils import nodes

def get_javadoc_ref(app, rawtext, text):
    javadoc_url_map = app.config.javadoc_url_map

    # Add default sources
    javadoc_url_map["java"] = ("http://docs.oracle.com/javase/6/docs/api", 'javadoc')
    javadoc_url_map["javax"] = ("http://docs.oracle.com/javase/6/docs/api", 'javadoc')
    javadoc_url_map["org.xml"] = ("http://docs.oracle.com/javase/6/docs/api", 'javadoc')
    javadoc_url_map["org.w3c"] = ("http://docs.oracle.com/javase/6/docs/api", 'javadoc')

    source = None
    package = ''

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
    elif ext_type == 'sphinx':
        source = baseurl + package.replace('.', '/') + '/' + cls.replace('.', '-') + '.html'
    else:
        raise ValueError('invalid target specifier ' + ext_type)

    return nodes.reference(rawtext, cls, refuri=source)

def javadoc_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """ Role for linking to external Javadoc """

    app = inliner.document.settings.env.app
    ref = get_javadoc_ref(app, rawtext, text)

    if not ref:
         raise ValueError("no Javadoc source found for %s in javadoc_url_map" % (text,))

    return [ref], []
