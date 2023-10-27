import json
import os
from os import path

import requests
from lxml import html

from ITEMS import item_ids, id_to_item

site = 'https://dragonsdogma.fandom.com'
idir = 'resources/images'


def slurp(url, dst):
    if not path.exists(dst):
        print(dst)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dst, 'wb') as fo:
                for chunk in r.iter_content(chunk_size=8192):
                    fo.write(chunk)


def scrape_item(url, dest, idx=-1):
    print(url, end='\n')
    with requests.get(url) as page:
        page.raise_for_status()
        dom = html.fromstring(page.text)
    aside = dom.find('.//aside[@role="region"]')
    imga = aside.find('./figure/a')
    imgu = imga.attrib['href']
    imgn = imga.find('./img').attrib["data-image-name"]
    ext = path.splitext(imgn)[1]
    slurp(imgu, dest+ext)
    name = aside.find('h2', {'data-source': 'name'}).text
    if name == 'Silk Lingerie' or name == 'Free-Spoken Earring' or name == 'Sanguine Stalk':
        pass  # breakpointing
    typ = aside.find('.//div[@data-source="type"]//a')
    if typ is not None:
        typ = typ.text_content()
    else:
        typ = 'Special'
        print(f'Warning: no type found for {name}({url}), "{typ}" supplied')
    desc = dom.find('.//meta[@property="og:description"]').attrib['content'].strip()
    table_list = dom.xpath('.//table/tbody')
    if not table_list:
        usable = None
    else:
        usable = {}
        try:
            for u in table_list:
                al = u.findall('./tr/td//a')
                if len(al) == 9:
                    imgs = us = None
                    try:
                        imgs = {x.attrib['title']: x.find('./img').attrib['data-image-name'] for x in al}
                        us = {k: v.startswith('DDicon') for k, v in imgs.items()}
                    except (KeyError, AttributeError):
                        try:
                            if imgs and len(imgs) == 9:
                                imgs = {['Fighter', 'Strider', 'Mage',
                                         'Assassin', 'MagicK Archer', 'Magick Knight',
                                         'Warrior', 'Ranger', 'Sorcerer', ][n]: x.find('./img').attrib['data-image-name']
                                        for n, x in enumerate(imgs)}
                                us = {k: v.startswith('DDicon') for k, v in imgs.items()}
                        except:
                            print(f'ERROR: unable to parse: ({html.tostring(usable)})')
                    if us is not None:
                        usable.update(us)
                elif len(al) == 1:
                    try:
                        sex = 'BOTH'
                        t = al.find('./img').attrib['alt']
                        if t == 'FEMALE' or t == 'MALE':
                            sex = t
                        else:
                            pass
                        usable['sex'] = sex
                    except AttributeError:
                        pass
        except Exception as e:
            print(f'ERROR: {e} while parsing [')
            for table in table_list:
                print(f'    {html.tostring(table)},')
            print(']')
            usable = None

    # usable = dom.xpath('.//h2/span[translate(@id, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")="usable_by"]/../following-sibling::table')
    # if usable:
    #     usable = usable[0]
    #     # print(html.tostring(usable))
    #     imgs = None
    #     try:
    #         sex = 'BOTH'
    #         cols = usable.findall('.//td')
    #         if len(cols) > 1:
    #             try:
    #                 t = cols[0].find('.//a/img').attrib['alt']
    #                 if t == 'FEMALE' or t == 'MALE':
    #                     sex = t
    #                 else:
    #                     pass
    #             except AttributeError:
    #                 pass
    #             cols = cols[1:]
    #         imgs = cols[0].findall('.//a')
    #         imgs = {x.attrib['title']: x.find('./img').attrib['data-image-name'] for x in imgs}
    #         usable = {k: v.startswith('DDicon') for k, v in imgs.items()}
    #         usable['sex'] = sex
    #     except:
    #         try:
    #             if imgs is not None:
    #                 imgs = {['Fighter', 'Strider', 'Mage',
    #                          'Assassin', 'MagicK Archer', 'Magick Knight',
    #                          'Warrior', 'Ranger', 'Sorcerer', ][n]: x.find('./img').attrib['data-image-name']
    #                         for n, x in enumerate(imgs)}
    #                 usable = {k: v.startswith('DDicon') for k, v in imgs.items()}
    #         except:
    #             usable = {'Fighter': True, 'Strider': True, 'Mage': True,
    #                       'Assassin': True, 'MagicK Archer': True, 'Magick Knight': True,
    #                       'Warrior': True, 'Ranger': True, 'Sorcerer': True, 'sex': 'BOTH'}
    #             print(f'ERROR: unable to parse: ({html.tostring(usable)})')
    #
    # else:
    #     usable = None

    if isinstance(usable, html.HtmlElement):
        usable = None
    if idx < 0:
        return dest+ext, desc, usable

    return {'ID': idx, 'Name': name, 'Type': typ, 'img': dest+ext, 'desc': desc, 'usable': usable}


def scrape_items():
    url = site + '/wiki/List_of_Items'
    page = requests.get(url)
    dom = html.fromstring(page.text)
    table = dom.find('.//table[@class="sortable"]')
    tab = []
    headers = []
    for i in table.findall('.//th'):
        title = i.text_content().strip()
        headers.append(title)
    for j in table.findall('.//tr')[1:]:
        row_data = j.findall('./td')
        row = [i.text_content().strip() for i in row_data]
        dic = {headers[i]: row[i] for i in range(len(headers))}
        try:
            sub_page = row_data[1].find('./a').attrib['href']
            if sub_page:
                i, d, u = scrape_item(site + sub_page, path.join(idir, dic["Name"]))
                dic['img'] = i
                dic['desc'] = d
                dic['usable'] = u
        except TypeError:
            pass
        tab.append(dic)
    return tab


def scrape_weapon(url, typ):
    page = requests.get(url)
    dom = html.fromstring(page.text)
    table = dom.xpath('.//table[contains(@class, "sortable")]')
    # table = dom.find('.//table[@class="sortable"]')
    # if table is None:
    #     table = dom.find('.//table[@class="wikitable sortable"]')

    tab = []
    headers = []
    if len(table) > 1:
        print(f'Warning: multiple sortable tables ({url})')
    table = table[0]
    rows = table.findall('.//tr')
    for i in rows[0].findall('./th'):
        title = i.text.strip()
        headers.append(title)
    for j in rows[1:]:
        row_data = j.findall('./*')
        row = [i.text_content().strip() for i in row_data]
        dic = {headers[i]: row[i] for i in range(len(headers))}
        try:
            sub_page = row_data[0].find('.//a').attrib['href']
            if sub_page:
                i, d, u = scrape_item(site + sub_page, path.join(idir, dic["Name"]))
                dic['img'] = i
                dic['desc'] = d
                dic['usable'] = u
        except TypeError:
            pass
        match row_data[0].attrib['class']:
            case 'txtbg1':
                dic['release'] = 'DD'
            case 'txtbg2':
                dic['release'] = 'DLC'
            case 'txtbg3':
                dic['release'] = 'DDDA'
        dic['Type'] = typ

        tab.append(dic)
    return tab


def scrape_weapons():
    allw = []
    allw.extend(scrape_weapon(site + '/wiki/Category:Archistaves', 'Archistaves'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Daggers', 'Daggers'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Longbows', 'Longbows'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Longswords', 'Longswords'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Maces', 'Mace'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Magick_Bows', 'Magick Bows'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Magick_Shields', 'Magick Shields'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Shields', 'Shields'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Shortbows', 'Shortbows'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Staves', 'Staves'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Swords', 'Swords'))
    allw.extend(scrape_weapon(site + '/wiki/Category:Warhammers', 'Warhammers'))
    return allw


def parse_resist(data):
    res = {}
    for r in data.findall('.//tr'):
        try:
            t = r.find('.//a').attrib['title']
            v = r.find('td').text_content().strip()
            res[t] = v
        except AttributeError:
            pass
    return res


def scrape_armor(url, typ):
    page = requests.get(url)
    dom = html.fromstring(page.text)
    table = dom.xpath('.//table[contains(@class, "sortable")]')
    # if table is None:
    #     table = dom.find('.//table[@class="wikitable sortable"]')
    #     if table is None:
    #         table = dom.find('.//table[@class="wikitable sortable jquery-tablesorter"]')
    tab = []
    headers = []
    rows = table[0].findall('./tbody/tr')
    for i in rows[0].findall('.//th'):
        title = i.text.strip()
        headers.append(title)
    for n, j in enumerate(rows[1:]):
        row_data = j.findall('./*')
        row = [i.text_content().strip() for i in row_data]
        if len(row) == len(headers):
            dic = {headers[i]: row[i] for i in range(len(headers))}
            try:
                sub_page = row_data[0].find('.//a').attrib['href']
                if sub_page:
                    i, d, u = scrape_item(site + sub_page, path.join(idir, dic["Name"]))
                    dic['img'] = i
                    dic['desc'] = d
                    dic['usable'] = u
            except TypeError:
                pass
            er = dr = None
            if headers[7].startswith('Elemental'):
                dic['ElementalResist'] = parse_resist(row_data[7])
            if headers[8].startswith('Debilitation'):
                dic['DebilitationResist'] = parse_resist(row_data[7])
            dic['Type'] = typ

            tab.append(dic)
        else:
            print(f'Warning: invalid row {n} ({len(row)} != {len(headers)})')
    return tab


def scrape_armors():
    allw = []
    allw.extend(scrape_armor(site + '/wiki/List_of_Arms_Armor', 'Arms Armor'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Cloaks', 'Cloak'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Head_Armor', 'Head Armor'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Leg_Armor', 'Leg Armor'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Leg_Clothing', 'Leg Clothing'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Chest_Clothing', 'Chest Clothing'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Head_Armor', 'Head Armor'))
    allw.extend(scrape_armor(site + '/wiki/List_of_Torso_Armor', 'Torso Armor'))
    return allw


def backcheck(tab):
    all_by_id = {x["ID"]: x for x in tab}
    changed = False

    def try_url(url, img, idx):
        try:
            return scrape_item(url, img, idx)
        except AttributeError:
            print(f'ERROR: page found but scrape failed ({url})')
            return {'ID': i, 'Name': n, 'Type': 'malformed', 'img': None, 'desc': url}
        except requests.HTTPError as e:
            return None
        except:
            return None

    for i in range(item_ids['Used']):
        try:
            print(f'{i:04d} - {all_by_id[i]["Name"]}', end='\r')
        except KeyError:
            n = id_to_item[i]
            if n != 'Unknown Item':
                print(f'Info: index {i} not found ({n}): Trying recovery...')
                url = f'{site}/wiki/{n.replace(" ", "_")}'
                d = try_url(url, path.join(idir, n), i)
                if d is None:
                    match n.split():
                        case ['Small', *tail] | ['Large', *tail] | ['Huge', *tail] | ['Giant', *tail]:
                            d = try_url(f'{site}/wiki/{"_".join(tail)}', path.join(idir, n), i)
                        case [*head, 'Forgery']:
                            d = try_url(f'{site}/wiki/{"_".join(head)}', path.join(idir, n), i)
                    if d is None:
                        d = {'ID': i, 'Name': n, 'Type': 'Unknown', 'img': None,
                             'desc': 'This item was not found in "dragonsdogma.fandom.com'}
                    else:
                        d['Name'] = n
                print(d)
                tab.append(d)
                changed = True

    return changed


if __name__ == '__main__':
    def save(what, where):
        t = [x for x in sorted(what, key=lambda item: item['ID'])]
        with open(where, 'w') as fo:
            json.dump(t, fo, indent=2)


    if not path.isdir(idir):
        os.makedirs(idir)
    if path.isfile('fandom_tab.json'):
        with open('fandom_tab.json') as fi:
            tab = json.load(fi)
    else:
        tab = []
        tab.extend(scrape_items())
        tab.extend(scrape_weapons())
        tab.extend(scrape_armors())
        with open('fandom_tab.json', 'w') as fo:
            json.dump(tab, fo, indent=2)
    for w in tab:
        n = w['Name']
        idx = item_ids[n]
        w['ID'] = idx

    save(tab, 'sorted_tab.json')
    if backcheck(tab):
        save(tab, 'sorted_checked_tab.json')

    with open('Fandom.py', 'w') as fo:
        fo.write('_all_items = [\n')
        for w in tab:
            n = w['Name']
            idx = item_ids[n]
            w['id'] = idx
            fo.write(f'    {w},\n')
        fo.write('    ]\n')
        fo.write('all_by_id = {x["ID"]: x for x in _all_items}\n')
        fo.write('all_by_name = {x["Name"]: x for x in _all_items}\n')
