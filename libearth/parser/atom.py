""":mod:`libearth.parser.atom` --- Atom parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parsing Atom feed. Atom specification is :rfc:`4287`

.. todo::

   Parsing text construct which ``type`` is ``'xhtml'``.

"""
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from ..codecs import Rfc3339
from ..compat.etree import fromstring
from ..feed import (Category, Content, Entry, Feed, Generator, Link,
                    Person, Source, Text)
from .util import normalize_xml_encoding

__all__ = 'XMLNS_ATOM', 'XMLNS_XML', 'parse_atom'


#: (:class:`str`) The XML namespace for Atom format.
XMLNS_ATOM = 'http://www.w3.org/2005/Atom'

#: (:class:`str`) The XML namespace for the predefined ``xml:`` prefix.
XMLNS_XML = 'http://www.w3.org/XML/1998/namespace'


class ElementBase(object):
    XMLNS = XMLNS_ATOM
    element_name = None
    xml_base = None

    @classmethod
    def get_element_uri(cls):
        return '{' + cls.XMLNS + '}' + cls.element_name

    def __init__(self, data, xml_base=None):
        self.data = data
        self.xml_base = xml_base

    def parse(self):
        raise NotImplementedError('')

    def _get_xml_base(self):
        if '{' + XMLNS_XML + '}' + 'base' in self.data.attrib:
            return self.data.attrib['{' + XMLNS_XML + '}' + 'base']
        else:
            return self.xml_base


class RootElement(object):

    def parse_meta_data(self, element_obj):
        element_obj.id = self.parse_element(AtomId) or self.xml_base
        element_obj.title = self.parse_element(AtomTitle)
        element_obj.updated_at = self.parse_element(AtomUpdated)
        element_obj.authors = self.parse_multiple_element(AtomAuthor)
        element_obj.categories = self.parse_multiple_element(AtomCategory)
        element_obj.contributors = self.parse_multiple_element(AtomContributor)
        element_obj.links = self.parse_multiple_element(AtomLink)
        element_obj.generator = self.parse_element(AtomGenerator)
        element_obj.icon = self.parse_element(AtomIcon)
        element_obj.logo = self.parse_element(AtomLogo)
        element_obj.rights = self.parse_element(AtomRights)
        element_obj.subtitle = self.parse_element(AtomSubtitle)
        return element_obj

    def parse_element(self, element_type):
        element = self.data.findall(element_type.get_element_uri())
        num_of_element = len(element)
        if num_of_element > 1:
            raise ValueError('Multiple {0} elements exists'.format(
                element_type.get_element_uri()
            ))
        elif num_of_element == 0:
            return None
        element = element[0]
        return element_type(element, self.xml_base).parse()

    def parse_multiple_element(self, element_type):
        elements = self.data.findall(element_type.get_element_uri())
        parsed_elements = []
        for element in elements:
            parsed_elements.append(element_type(element, self.xml_base).parse())
        return parsed_elements


class AtomFeed(ElementBase, RootElement):
    element_name = 'feed'

    def parse(self):
        return self.parse_meta_data(Feed())


class AtomEntry(ElementBase, RootElement):
    element_name = 'entry'

    def parse(self):
        entry = self.parse_meta_data(Entry())
        entry.content = self.parse_element(AtomContent)
        entry.published_at = self.parse_element(AtomPublished)
        entry.rights = self.parse_element(AtomRights)
        entry.source = self.parse_element(AtomSource)
        entry.summary = self.parse_element(AtomSummary)
        return entry


class AtomSource(ElementBase, RootElement):
    element_name = 'source'

    def parse(self):
        return self.parse_meta_data(Source())


class AtomTextConstruct(ElementBase):

    def parse(self):
        text = Text()
        text_type = self.data.get('type')
        if text_type is not None:
            text.type = text_type
        if text.type in ('text', 'html'):
            text.value = self.data.text
        elif text.value == 'xhtml':
            text.value = ''  # TODO
        return text


class AtomPersonConstruct(ElementBase):

    def parse(self):
        person = Person()
        xml_base = self._get_xml_base()
        for child in self.data:
            if child.tag == '{' + XMLNS_ATOM + '}' + 'name':
                person.name = child.text
            elif child.tag == '{' + XMLNS_ATOM + '}' + 'uri':
                person.uri = urlparse.urljoin(xml_base, child.text)
            elif child.tag == '{' + XMLNS_ATOM + '}' + 'email':
                person.email = child.text
        return person


class AtomDateConstruct(ElementBase):

    def parse(self):
        return Rfc3339().decode(self.data.text)


class AtomId(ElementBase):
    element_name = 'id'

    def parse(self):
        xml_base = self._get_xml_base()
        return urlparse.urljoin(xml_base, self.data.text)


class AtomTitle(AtomTextConstruct):
    element_name = 'title'


class AtomSubtitle(AtomTextConstruct):
    element_name = 'subtitle'


class AtomRights(AtomTextConstruct):
    element_name = 'rights'


class AtomSummary(AtomTextConstruct):
    element_name = 'summary'


class AtomAuthor(AtomPersonConstruct):
    element_name = 'author'


class AtomContributor(AtomPersonConstruct):
    element_name = 'contributor'


class AtomPublished(AtomDateConstruct):
    element_name = 'published'


class AtomUpdated(AtomDateConstruct):
    element_name = 'updated'


class AtomCategory(ElementBase):
    element_name = 'category'

    def parse(self):
        if not self.data.get('term'):
            return
        category = Category()
        category.term = self.data.get('term')
        category.scheme_uri = self.data.get('scheme')
        category.label = self.data.get('label')
        return category


class AtomLink(ElementBase):
    element_name = 'link'

    def parse(self):
        link = Link()
        xml_base = self._get_xml_base()
        link.uri = urlparse.urljoin(xml_base, self.data.get('href'))
        link.relation = self.data.get('rel')
        link.mimetype = self.data.get('type')
        link.language = self.data.get('hreflang')
        link.title = self.data.get('title')
        link.byte_size = self.data.get('length')
        return link


class AtomGenerator(ElementBase):
    element_name = 'generator'

    def parse(self):
        generator = Generator()
        xml_base = self._get_xml_base()
        generator.value = self.data.text
        if 'uri' in self.data.attrib:
            generator.uri = urlparse.urljoin(xml_base, self.data.attrib['uri'])
        generator.version = self.data.get('version')
        return generator


class AtomIcon(ElementBase):
    element_name = 'icon'

    def parse(self):
        xml_base = self._get_xml_base()
        return urlparse.urljoin(xml_base, self.data.text)


class AtomLogo(ElementBase):
    element_name = 'logo'

    def parse(self):
        xml_base = self._get_xml_base()
        return urlparse.urljoin(xml_base, self.data.text)


class AtomContent(ElementBase):
    element_name = 'content'

    def parse(self):
        content = Content()
        content.value = self.data.text
        content_type = self.data.get('type')
        if content_type is not None:
            content.type = content_type
        if 'src' in self.data.attrib:
            xml_base = self._get_xml_base()
            content.source_uri = urlparse.urljoin(xml_base,
                                                  self.data.attrib['src'])
        return content


def parse_atom(xml, feed_url, parse_entry=True):
    """Atom parser.  It parses the Atom XML and returns the feed data
    as internal representation.

    :param xml: target atom xml to parse
    :type xml: :class:`str`
    :param feed_url: the url used to retrieve the atom feed.
                     it will be the base url when there are any relative
                     urls without ``xml:base`` attribute
    :type feed_url: :class:`str`
    :param parse_entry: whether to parse inner items as well.
                        it's useful to ignore items when retrieve
                        ``<source>`` in rss 2.0.  :const:`True` by default.
    :type parse_item: :class:`bool`
    :returns: a pair of (:class:`~libearth.feed.Feed`, crawler hint)
    :rtype: :class:`tuple`

    """
    root = fromstring(normalize_xml_encoding(xml))
    feed = AtomFeed(root, feed_url)
    feed_data = feed.parse()
    if parse_entry:
        feed_data.entries = feed.parse_multiple_element(AtomEntry)
    return feed_data, None
