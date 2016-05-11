# coding: utf-8
__author__ = 'rik91'

import common
import re, string, unicodedata
from bs4 import BeautifulSoup
from quasar import provider

# this read the settings
settings = common.Settings()
# define the browser
browser = common.Browser()
# create the filters
filters = common.Filtering()


def extract_torrents(data):
    sint = common.ignore_exception(ValueError)(int)
    results = []
    cont = 0
    if data is not None:
        filters.information()  # print filters settings
        soup = BeautifulSoup(data, 'html5lib')
        links = soup.findAll('div', {'class': ['ligne0', 'ligne1']})
        for link in links:
            name = link.a.text  # name
            magnet = "%s/telechargement/%s" % (settings.value["url_address"], link.a["href"].rpartition('/')[2].replace(".html",".torrent"))  # magnet
            size = link.find('div', class_="poid").text  # size
            seeds = link.find('div', class_="up").span.text  # seeds
            peers = link.find('div', class_="down").text  # peers
            # info_magnet = common.Magnet(magnet)
            if filters.verify(name, size):
                cont += 1
                results.append({"name": name.strip(),
                                "uri": magnet,
                                #"info_hash": info_magnet.hash,
                                "size": size.strip(),
                                "seeds": sint(seeds),
                                "peers": sint(peers),
                                "language": settings.value.get("language", "fr"),
                                "provider": settings.name,
                                "icon": settings.icon,
                                })  # return the torrent
                if cont >= int(settings.value.get("max_magnets", 10)):  # limit magnets
                    break
            else:
                provider.log.warning(filters.reason)
    provider.log.info('>>>>>>' + str(cont) + ' torrents sent to Quasar<<<<<<<')
    return results


def search(query):
    info = {"query": query,
            "type": "general"}
    return search_general(info)


def search_general(info):
    folders = {"movie": "films/", "show": "series/", "anime": "", "general" : ""}
    info["extra"] = settings.value.get("extra", "")  # add the extra information
    info["query"] = cleanQuery(info["query"])
    query = filters.type_filtering(info, '-')  # check type filter and set-up filters.title
    url_search = "%s/recherche/%s%s.html" % (settings.value["url_address"], folders[info["type"]], query)
    provider.log.info(url_search)
    browser.open(url_search)
    return extract_torrents(browser.content)


def cleanQuery(query):
    import types
    #Suppression de la ponctuation
    regex = re.compile("[%s]" % re.escape(string.punctuation + u"’…"))
    query = regex.sub(" ", query)
    #Suppression des accents
    query = ''.join((c for c in unicodedata.normalize('NFD', query.decode('utf-8')) if unicodedata.category(c) != 'Mn'))
    return query


def search_movie(info):
    info["type"] = "movie"
    query = common.translator(info['imdb_id'], 'fr', False)  # Just title
    info["query"] = query + ' ' + str(info['year'])
    return search_general(info)


def search_episode(info):
    if info['absolute_number'] == 0:
        info["type"] = "show"
        info["query"] = info['title'].encode('utf-8') + ' s%02de%02d' % (info['season'], info['episode'])  # define query
    else:
        info["type"] = "anime"
        info["query"] = info['title'].encode('utf-8') + ' %02d' % info['absolute_number']  # define query anime
    return search_general(info)


def search_season(info):
    info["type"] = "show"
    info["query"] = info['title'].encode('utf-8') + ' %s %s' % (common.season_names[settings.value.get("language", "fr")], info['season'])  # define query
    return search_general(info)

# This registers your module for use
if "false" == settings.value.get("episodes", "false"):
    provider.register(search, search_movie, search_episode, search_season)
else:
    provider.register(search, search_movie, search_season, search_season)

del settings
del browser
del filters
