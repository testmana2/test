# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module defining the default search engines.
"""

OpenSearchDefaultEngines = {
    "Amazon_com": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Amazon.com</ShortName>
            <Description>Amazon.com Search</Description>
            <Url method="get" type="text/html" template="http://www.amazon.com/exec/obidos/external-search/?field-keywords={searchTerms}" />
            <Image width="16" height="16">http://www.amazon.com/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "Beolingus": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>De-En Beolingus</ShortName>
            <Description>Beolingus: German-English Dictionary</Description>
            <Url method="get" template="http://dict.tu-chemnitz.de/?query={searchTerms}"/>
            <Url method="get" type="application/x-suggestions+json" template="http://dict.tu-chemnitz.de/sugg.php?json=1;s={searchTerms}"/>
            <Image width="16" height="16">http://dict.tu-chemnitz.de/pics/beo-de.png</Image>
        </OpenSearchDescription>""",

    "Bing": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Bing</ShortName>
            <Description>Bing Web Search</Description>
            <Url method="get" type="text/html" template="http://www.bing.com/search?cc={language}&amp;q={searchTerms}" />
            <Url method="get" type="application/x-suggestions+xml" template="http://api.search.live.com/qsml.aspx?query={searchTerms}"/>
            <Image width="16" height="16">http://www.bing.com/s/wlflag.ico</Image>
        </OpenSearchDescription>""",
    
    "Facebook": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Facebook</ShortName>
            <Description>Search Facebook</Description>
            <Url method="get" template="http://www.facebook.com/search/?src=os&amp;q={searchTerms}"/>
            <Url method="get" type="application/x-suggestions+xml" template="http://www.facebook.com/search/opensearch_typeahead.php?format=xml&amp;q={searchTerms}"/>
            <Image width="16" height="16">http://www.facebook.com/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "Google": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Google</ShortName>
            <Description>Google Web Search</Description>
            <Url method="get" type="text/html" template="http://www.google.com/search?hl={language}&amp;lr=lang_{language}&amp;q={searchTerms}" />
            <Url method="get" type="application/x-suggestions+json" template="http://suggestqueries.google.com/complete/search?json=t&amp;hl={language}&amp;q={searchTerms}&amp;nolabels=t" />
            <Image width="16" height="16">http://www.google.com/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "Google_Im_Feeling_Lucky": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Google (I'm Feeling Lucky)</ShortName>
            <Description>Google Web Search</Description>
            <Url method="get" type="text/html" template="http://www.google.com/search?btnI=&amp;hl={language}&amp;lr=lang_{language}&amp;q={searchTerms}" />
            <Url method="get" type="application/x-suggestions+json" template="http://suggestqueries.google.com/complete/search?json=t&amp;hl={language}&amp;q={searchTerms}&amp;nolabels=t" />
            <Image width="16" height="16">http://www.google.com/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "Leo_de_en": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>LEO Deu-Eng</ShortName>
            <Description>Deutsch-Englisch Woerterbuch von LEO</Description>
            <Url method="get" type="text/html" template="http://dict.leo.org/?lp=ende&amp;search={searchTerms}"/>
            <Image width="16" height="16">http://dict.leo.org/favicon_en.ico</Image>
        </OpenSearchDescription>""",

    "LinuxMagazin_de": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Linux-Magazin</ShortName>
            <Description>Suche auf www.linux-magazin.de</Description>
            <Url type="text/html" method="GET" template="http://www.linux-magazin.de/content/search?SearchText={searchTerms}" />
            <Image width="16" height="16">http://www.linux-magazin.de/extension/lnm/design/linux_magazin/images/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "Reddit": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Reddit</ShortName>
            <Description>Reddit Site Search</Description>
            <Url method="get" type="text/html" template="http://www.reddit.com/search?q={searchTerms}" />
            <Image width="16" height="16">http://www.reddit.com/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "Wikia": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Wikia</ShortName>
            <Description>Wikia Site Search</Description>
            <Url method="get" template="http://{country}.wikia.com/index.php?title=Special:Search&amp;search={searchTerms}"/>
            <Url method="get" type="application/x-suggestions+json" template="http://{country}.wikia.com/api.php?action=opensearch&amp;search={searchTerms}&amp;namespace=0"/>
            <Image width="16" height="16">http://images.wikia.com/wikiaglobal/images/6/64/Favicon.ico</Image>
        </OpenSearchDescription>""",

    "Wikia_en": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Wikia (en)</ShortName>
            <Description>Wikia Site Search English</Description>
            <Url method="get" template="http://www.wikia.com/index.php?title=Special:Search&amp;search={searchTerms}"/>
            <Url method="get" type="application/x-suggestions+json" template="http://www.wikia.com/api.php?action=opensearch&amp;search={searchTerms}&amp;namespace=1"/>
            <Image width="16" height="16">http://images.wikia.com/wikiaglobal/images/6/64/Favicon.ico</Image>
        </OpenSearchDescription>""",

    "Wikipedia": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Wikipedia</ShortName>
            <Description>Full text search in Wikipedia</Description>
            <Url method="get" type="text/html" template="http://{country}.wikipedia.org/wiki/Special:Search?search={searchTerms}&amp;fulltext=Search" />
            <Url method="get" type="application/x-suggestions+json" template="http://{country}.wikipedia.org/w/api.php?action=opensearch&amp;search={searchTerms}&amp;namespace=0" />
            <Image width="16" height="16">http://en.wikipedia.org/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "Wiktionary": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Wiktionary</ShortName>
            <Description>Wiktionary</Description>
            <Url method="get" template="http://{country}.wiktionary.org/w/index.php?title=Special:Search&amp;search={searchTerms}"/>
            <Url method="get" type="application/x-suggestions+xml" template="http://{country}.wiktionary.org/w/api.php?action=opensearch&amp;format=xml&amp;search={searchTerms}&amp;namespace=0"/>
            <Image width="16" height="16">http://en.wiktionary.org/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "Yahoo": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>Yahoo!</ShortName>
            <Description>Yahoo! Web Search</Description>
            <Url method="get" type="text/html" template="http://{country}.search.yahoo.com/search?ei=utf-8&amp;fr=sfp&amp;iscqry=&amp;p={searchTerms}" />
            <Url method="get" type="application/x-suggestions+json" template="http://ff.search.yahoo.com/gossip?output=fxjson&amp;command={searchTerms}" />
            <Image width="16" height="16">http://m.www.yahoo.com/favicon.ico</Image>
        </OpenSearchDescription>""",
    
    "YouTube": """<?xml version="1.0" encoding="UTF-8"?>
        <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>YouTube</ShortName>
            <Description>YouTube</Description>
            <Url method="get" type="text/html" template="http://www.youtube.com/results?search_query={searchTerms}&amp;search=Search" />
            <Url method="get" type="application/x-suggestions+json" template="http://suggestqueries.google.com/complete/search?ds=yt&amp;json=t&amp;hl={language}&amp;q={searchTerms}&amp;nolabels=t" />
            <Image width="16" height="16">http://www.youtube.com/favicon.ico</Image>
        </OpenSearchDescription>""",
}
