from .common import InfoExtractor
from ..utils import (
    clean_podcast_url,
    get_element_by_id,
    int_or_none,
    parse_iso8601,
    traverse_obj,
    try_call,
)


class ApplePodcastsIE(InfoExtractor):
    _VALID_URL = r'https?://podcasts\.apple\.com/(?:[^/]+/)?podcast(?:/[^/]+){1,2}.*?\bi=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://podcasts.apple.com/us/podcast/207-whitney-webb-returns/id1135137367?i=1000482637777',
        'md5': 'baf8a6b8b8aa6062dbb4639ed73d0052',
        'info_dict': {
            'id': '1000482637777',
            'ext': 'mp3',
            'title': '207 - Whitney Webb Returns',
            'description': 'md5:6388e95fe306e88fa61d85d683102944',
            'upload_date': '20200705',
            'timestamp': 1593932400,
            'duration': 5369,
            'series': 'The Tim Dillon Show',
            'thumbnail': 're:.+[.](png|jpe?g|webp)',
        },
    }, {
        'url': 'https://podcasts.apple.com/podcast/207-whitney-webb-returns/id1135137367?i=1000482637777',
        'only_matching': True,
    }, {
        'url': 'https://podcasts.apple.com/podcast/207-whitney-webb-returns?i=1000482637777',
        'only_matching': True,
    }, {
        'url': 'https://podcasts.apple.com/podcast/id1135137367?i=1000482637777',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        episode_id = self._match_id(url)
        webpage = self._download_webpage(url, episode_id)

        serialized_server_data = get_element_by_id('serialized-server-data', webpage)
        serialized_server_data = self._parse_json(serialized_server_data, episode_id)
        data = serialized_server_data[0]['data']

        # Shelves are like "blocks" of data which appear to be ordered and
        # organized similar to the visual ordering of data in the webpage
        # when opened in a web browser.
        shelves = data['shelves']
        main_shelf = shelves[0]['items'][0]  # Contains thumbnail, audio stream url, ...
        desc_shelf = traverse_obj(shelves, (1, 'items'))  # Contains the description
        info_shelf = traverse_obj(shelves, (-1, 'items'))  # Contains additional info such as "show name" (aka "series")

        episode = main_shelf['primaryButtonAction']['episodeOffer']

        artwork = traverse_obj(main_shelf, ('primaryArtwork', 'artwork'))
        artwork_template = artwork.get('template')
        artwork_width = artwork.get('width')
        artwork_height = artwork.get('height')

        if isinstance(artwork_template, str) and artwork_width is not None and artwork_height is not None:
            # We could also use python's built-in formatting, but that's too much flexible.
            artwork_url = try_call(
                lambda: artwork_template
                .replace('{w}', str(artwork_width))
                .replace('{h}', str(artwork_height))
                .replace('{f}', 'webp'))
        else:
            artwork_url = None

        return {
            'id': episode_id,
            'title': data.get('title') or episode['title'],
            'url': clean_podcast_url(episode['streamUrl']),
            'description': traverse_obj(desc_shelf, (0, 'text')) or self._og_search_description(webpage),
            'timestamp': parse_iso8601(episode.get('releaseDate')),
            'duration': int_or_none(episode.get('duration')),
            'series': traverse_obj(info_shelf, (0, 'clickAction', 'title')),
            'thumbnail': artwork_url or self._og_search_thumbnail(webpage),
            'vcodec': 'none',
        }
