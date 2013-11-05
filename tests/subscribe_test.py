from datetime import datetime
from pytest import fixture

from libearth.feed import Person
from libearth.subscribe import Body, Category, Subscription, SubscriptionList
from libearth.schema import read
from libearth.tz import utc


@fixture
def fx_subscription():
    return Subscription(
        label='Title',
        feed_uri='http://example.com/rss.xml',
        alternate_uri='http://example.com/'
    )


def test_count_empty_list():
    subs = SubscriptionList()
    assert len(subs) == 0
    subs = SubscriptionList(body=Body())
    assert len(subs) == 0


def test_count_duplicated_url(fx_subscription):
    subs = SubscriptionList()
    subs.add(fx_subscription)
    assert len(subs) == 1
    assert list(subs) == [fx_subscription]
    subs.add(fx_subscription)
    assert len(subs) == 1
    assert list(subs) == [fx_subscription]


def test_count_after_remove(fx_subscription):
    subs = SubscriptionList()
    subs.add(fx_subscription)
    assert len(subs) == 1
    assert list(subs) == [fx_subscription]
    subs.discard(fx_subscription)
    assert not subs
    assert len(subs) == 0
    assert list(subs) == []


XML = '''
<opml version="2.0">
    <head>
        <title>Earth Reader's Subscriptions</title>
        <dateCreated>Sat, 18 Jun 2005 12:11:52 +0000</dateCreated>
        <ownerName>Earth Reader Team</ownerName>
        <ownerEmail>earthreader@librelist.com</ownerEmail>
        <ownerId>http://earthreader.org/</ownerId>
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
        <outline text="test.com" type="rss" xmlUrl="http://test.com/"/>
    </body>
</opml>
'''

XML_CATEGORY = '''
<opml version="2.0">
    <head>
        <title>Earth Reader's Subscriptions</title>
        <dateCreated>Sat, 18 Jun 2005 12:11:52 +0000</dateCreated>
        <ownerName>Earth Reader Team</ownerName>
        <ownerEmail>earthreader@librelist.com</ownerEmail>
        <ownerId>http://earthreader.org/</ownerId>
        <expansionState>a,b,c,d</expansionState>
        <vertScrollState>1</vertScrollState>
        <windowTop>12</windowTop>
        <windowLeft>34</windowLeft>
        <windowBottom>56</windowBottom>
        <windowRight>78</windowRight>
    </head>
    <body>
        <outline text="Game" title="Game" type="category">
            <outline text="valve" title="valve" xmlUrl="http://valve.com/" />
            <outline text="nintendo" title="nintendo"
            xmlUrl="http://nintendo.com/" />
        </outline>
        <outline text="Music" title="Music" type="category">
            <outline text="capsule" title="capsule"
            xmlUrl="http://www.capsule-web.com/" />
        </outline>
    </body>
</opml>
'''


@fixture
def fx_subscription_list():
    return read(SubscriptionList, XML)


def test_subscription_list_datetime(fx_subscription_list):
    expected_datetime = datetime(2005, 6, 18, 12, 11, 52, tzinfo=utc)
    assert fx_subscription_list.head.created_at == expected_datetime
    assert fx_subscription_list.head.updated_at is None


def test_subscription_list_title(fx_subscription_list):
    assert fx_subscription_list.head.title == "Earth Reader's Subscriptions"
    assert fx_subscription_list.title == "Earth Reader's Subscriptions"
    fx_subscription_list.title = "Hong Minhee's Subscriptions"
    assert fx_subscription_list.head.title == "Hong Minhee's Subscriptions"


def test_subscription_list_owner(fx_subscription_list):
    assert fx_subscription_list.head.owner_name == 'Earth Reader Team'
    assert (fx_subscription_list.head.owner_email ==
            'earthreader' '@' 'librelist.com')
    assert fx_subscription_list.head.owner_uri == 'http://earthreader.org/'
    assert fx_subscription_list.owner == Person(
        name='Earth Reader Team',
        email='earthreader' '@' 'librelist.com',
        uri='http://earthreader.org/'
    )
    fx_subscription_list.owner = Person(
        name='Hong Minhee',
        email='minhee' '@' 'dahlia.kr',
        uri='http://dahlia.kr/'
    )
    assert fx_subscription_list.head.owner_name == 'Hong Minhee'
    assert fx_subscription_list.head.owner_email == 'minhee' '@' 'dahlia.kr'
    assert fx_subscription_list.head.owner_uri == 'http://dahlia.kr/'


def test_subscription_list_iter(fx_subscription_list):
    assert frozenset(fx_subscription_list) == frozenset([
        Subscription(label='CNET News.com',
                     feed_uri='http://news.com/2547-1_3-0-5.xml'),
        Subscription(label='test.com', feed_uri='http://test.com/')
    ])


def test_subscription_list_contains_category():
    subs = read(SubscriptionList, XML_CATEGORY)
    expected = {
        Category(label='Game'): frozenset([
            Subscription(label='valve', feed_uri='http://valve.com/'),
            Subscription(label='nintendo', feed_uri='http://nintendo.com/')
        ]),
        Category(label='Music'): frozenset([
            Subscription(label='capsule',
                         feed_uri='http://www.capsule-web.com/')
        ])
    }
    assert frozenset(subs) == frozenset(expected)
    for outline in subs:
        print(outline.label)
        assert outline.type == 'category'
        print(list(outline))
        assert frozenset(outline) == expected[outline]
