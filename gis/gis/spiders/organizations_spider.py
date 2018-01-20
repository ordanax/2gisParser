import json

from scrapy import Spider, Request
from gis.items import OrgItem


# noinspection SpellCheckingInspection
CAT_URL_TEMPLATE = 'https://catalog.api.2gis.ru/3.0/rubricator/list' \
                   '?parent_id={parent_id}&locale=ru_RU&region_id=5&key=rutnpt3272'

# noinspection SpellCheckingInspection
ORG_URL_TEMPLATE = 'https://catalog.api.2gis.ru/2.0/catalog/branch/list' \
                   '?page=1' \
                   '&page_size=50' \
                   '&rubric_id={rubric_id}' \
                   '&region_id=5' \
                   '&locale=ru_RU' \
                   '&fields=items.contact_groups%2Citems.point' \
                   '&key=rutnpt3272'


class OrganizationsSpider(Spider):
    name = 'organizations'
    start_urls = [
        'https://catalog.api.2gis.ru/3.0/rubricator/list?locale=ru_RU&region_id=5&key=rutnpt3272',
    ]

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.fingerprints = set()

    def parse(self, response):
        data = json.loads(response.text)
        if data['meta']['code'] == 404:
            return
        for item in data['result']['items']:
            uid = item.get('id')
            name = item.get('name')
            if uid is not None and name is not None:
                yield Request(url=CAT_URL_TEMPLATE.format(parent_id=uid))
                yield Request(url=ORG_URL_TEMPLATE.format(rubric_id=uid), callback=self.parse_category)

    def parse_category(self, response):
        data = json.loads(response.text)
        if data['meta']['code'] == 404:
            return
        for item in data['result']['items']:
            emails = list()
            if len(item.get('contact_groups', [])) == 0:
                return
            for contact in item.get('contact_groups', [{}])[0].get('contacts', []):
                if contact.get('type') == 'email':
                    emails.append(contact.get('value'))
            if emails:
                name = item.get('name')
                address = item.get('address_name')
                fingerprint = f'{name}#{address}'
                if fingerprint not in self.fingerprints:
                    self.fingerprints.add(fingerprint)
                    point = item.get('point', {})
                    point = point if point is not None else {}
                    yield OrgItem(
                        name=name,
                        address=address,
                        lat=point.get('lat'),
                        lon=point.get('lon'),
                        email=emails[0] if len(emails) > 0 else None,
                        email2=emails[1] if len(emails) > 1 else None,
                        email3=emails[2] if len(emails) > 2 else None,
                    )
