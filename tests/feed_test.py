from pytest import raises

from libearth.compat import binary_type, text_type, xrange
from libearth.feed import AlreadyExistException, Feed, OPMLDoc
from libearth.schema import Child, Content, DocumentElement, Element, Text


def test_count_empty_list():
    f = Feed()
    assert len(f) == 0


def test_count_duplicated_url():
    f = Feed()
    with raises(AlreadyExistException):
        for i in xrange(30):
            f.add_feed('title', 'url', 'type')

    assert len(f) == 1


def test_count_after_remove():
    f = Feed()
    f.add_feed('url', 'title', 'type')
    f.remove_feed('url')

    assert len(f) == 0

XML = """<?xml version="1.0" encoding="ISO-8859-1"?>
<opml version="2.0">
    <head>
        <title>EarthReader.opml</title>
        <dateCreated>Sat, 18 Jun 2005 12:11:52 GMT</dateCreated>
        <ownerName>libearth</ownerName>
        <ownerEmail>earthreader@librelist.com</ownerEmail>
        <expansionState>a,b,c,d</expansionState>
        <vertScrollState>1</vertScrollState>
        <windowTop>12</windowTop>
        <windowLeft>34</windowLeft>
        <windowBottom>56</windowBottom>
        <windowRight>78</windowRight>
    </head>
    <body>
        <outline text="CNET News.com" type="rss" version="RSS2"
            xmlUrl="http://news.com/2547-1_3-0-5.xml"/>
        <outline text="test.com" type="rss" xmlUrl="http://test.com"/>
    </body>
</opml>"""


def test_OPMLDocment():
    doc = OPMLDoc(XML)
    assert doc.head.title == "EarthReader.opml"
    assert doc.head.date_created == "Sat, 18 Jun 2005 12:11:52 GMT"
    assert doc.head.date_modified is None
    assert doc.head.owner_name == "libearth"
    assert doc.head.expansion_state == ['a', 'b', 'c', 'd']
    assert doc.head.window_top == 12

    assert len(doc.body.outline) == 2
    assert doc.body.outline[0].text == "CNET News.com"


def test_file_not_found():
    with raises(IOError):
        doc = Feed('this_file_must_be_not_found.ext')


def test_path_as_string():
    feed = Feed(XML, is_xml_string=True)
    assert feed.title == "EarthReader.opml"
    assert len(feed) == 2
    assert feed.get_feed('http://test.com')['type'] == 'rss'


def test_feed_as_iterator():
    feeds = Feed(XML, is_xml_string=True)
    expected = ['CNET News.com', 'test.com']
    for feed in feeds:
        expected.remove(feed['title'])
    assert not expected
