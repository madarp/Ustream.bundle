BASE_URL = 'http://www.ustream.tv'
EXPLORE_URL = 'http://www.ustream.tv/new/explore/%s/all'
AJAX_URL = 'http://www.ustream.tv/ajax-alwayscache/new/explore/%s/all.json?subCategory=%s&type=live&location=anywhere&page=%d'
RE_CATEGORY = Regex('explore/([^/]+)')

####################################################################################################
def Start():

	ObjectContainer.title1 = 'Ustream'
	HTTP.CacheTime = 60
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17'
	HTTP.Headers['Accept-Language'] = 'en-US,en;q=0.5'

####################################################################################################
@handler('/video/ustream', 'Ustream')
def MainMenu():

	oc = ObjectContainer()

	for category in HTML.ElementFromURL(BASE_URL, cacheTime=CACHE_1WEEK).xpath('//li[contains(@class, "categories")]/ul//a'):
		title = category.text
		url = category.get('href')
		category_id = RE_CATEGORY.search(url)

		if category_id:
			oc.add(DirectoryObject(
				key = Callback(Subcategory, title=title, category_id=category_id.group(1)),
				title = title
			))

	oc.add(SearchDirectoryObject(
		identifier = 'com.plexapp.plugins.ustream',
		title = 'Search Live Channels',
		prompt = 'Search Ustream',
		thumb = R('search.png')
	))

	return oc

####################################################################################################
@route('/video/ustream/{category_id}')
def Subcategory(title, category_id):

	oc = ObjectContainer(title2=title)
	url = EXPLORE_URL % category_id

	for subcategory in HTML.ElementFromURL(url, cacheTime=CACHE_1WEEK).xpath('//select[@id="FilterSubCategory"]/option'):
		title = subcategory.text
		subcategory_id = subcategory.get('value')

		if subcategory_id == '':
			continue

		oc.add(DirectoryObject(
			key = Callback(Streams, title=title, category_id=category_id, subcategory_id=subcategory_id, page=1),
			title = title
		))

	return oc

####################################################################################################
@route('/video/ustream/{category_id}/{subcategory_id}/{page}', page=int)
def Streams(title, category_id, subcategory_id, page=1):

	oc = ObjectContainer(title2=title, no_cache=True)
	url = AJAX_URL % (category_id, subcategory_id, page)

	json_obj = JSON.ObjectFromURL(url)
	html = HTML.ElementFromString(json_obj['pageContent'])

	for stream in html.xpath('//div[contains(@class, "media-item")]'):
		url = stream.xpath('.//img/parent::a/@href')[0]
		stream_title = stream.xpath('.//h4/a/text()')[0]
		thumb = stream.xpath('.//img/@src')[0]

		try:
			summary = stream.xpath('.//span[@class="item-location"]/a/text()')[0]
			summary = String.DecodeHTMLEntities(summary)
		except:
			summary = None

		oc.add(VideoClipObject(
			url = '%s/%s' % (BASE_URL, url.lstrip('/')),
			title = stream_title,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(thumb)
		))

	if len(oc) < 1:
		return ObjectContainer(header="No content", message="This directory is empty")

	if json_obj['pageMeta']['infinite'] == 1:
		oc.add(NextPageObject(
			key = Callback(Streams, title=title, category_id=category_id, subcategory_id=subcategory_id, page=page+1),
			title = 'More...'
		))

	return oc
