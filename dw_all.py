# %%
import bs4
import requests
import json
import pathlib
import time
import subprocess as sp

import RevUtilities.Logger as Rlog
import RevUtilities.General as Rgen

# %%

urls = dict()

'''
{
    <<<post_url>>>:
        {
            <<<urls>>>:[],
            <<<done>>>: True
        }
}
'''


def load():
    global urls

    urls = json.loads(pathlib.Path('urls.json.bk').read_text())


def save():
    global urls

    pathlib.Path('urls.json.bk').write_text(json.dumps(urls))


# %%

load()

# %%

main = 'http://panahian.ir/post/686'
main = requests.get(main).content.decode('utf8')
main = bs4.BeautifulSoup(markup=main, features='html.parser')
main = main.select('div.cnt li p a')

dw_dir = 'dw'

# %%
posts = [x["href"] for x in main]
posts = set(posts)

Rlog.info(f'{posts=}')
Rlog.info(f'{len(posts)=}')


# %%

def fix_url(url: str):
    if url.startswith('//'):
        return f'http:{url}'
    return url


def fix_title(title: str):
    rms = [
        ['|', '-'],
        ['\n', ''],
        ['(', ''],
        [')', ''],
        ['\xa0', ''],
        ['\u200c', ''],
        ['*', ''],
        ['?', ''],
        ['\\', ''],
        ['/', ''],
        ['"', ''],
        [':', ''],
        ['<', ''],
        ['>', ''],
    ]
    for rm in rms:
        title = title.replace(rm[0], rm[1])
    return title


def download(url: str, dir: str):
    aria2c = sp.Popen(['aria2c', '--file-allocation=none', '-s1', '-d', dir, url],
                      stdin=sp.PIPE,
                      stdout=sp.PIPE,
                      stderr=sp.PIPE)
    aria2c.wait(timeout=300)
    # result = aria2c.communicate()[0].decode()
    return aria2c.returncode


# %%

for post in posts:
    Rlog.info('*')

    if not post.startswith('http'):
        post = f'http://panahian.ir{post}'

    Rlog.info(f'{post=}')

    if post in urls:
        if urls[post]['done']:
            Rlog.info('post already done, skip...')
            continue
    else:
        urls[post] = {'urls': [], 'done': False}

    bs4_parsed = requests.get(post).content.decode('utf8')
    bs4_parsed = bs4.BeautifulSoup(bs4_parsed, features='html.parser')

    title = bs4_parsed.find(name='meta', attrs={'name': 'description'})['content']
    title = fix_title(title)
    Rlog.info(f'{title=}')

    post_dw_dir = f'{dw_dir}/{title}'
    Rgen.make_dirs_if_not_exists(post_dw_dir)

    bs4_parsed = bs4_parsed.select('.DivPlayerDownload')

    # print(f'{bs4_parsed=}')

    for i in range(len(bs4_parsed)):
        # Rlog.info(bs4_parsed[i])
        bs4_parsed[i] = bs4_parsed[i].select_one('a')

        if not bs4_parsed[i]:
            Rlog.info('not found!')
            continue

        bs4_parsed[i] = bs4_parsed[i]['href']
        bs4_parsed[i] = fix_url(bs4_parsed[i])
        Rlog.info(bs4_parsed[i])

        if bs4_parsed[i] in urls[post]['urls']:
            Rlog.info('url already downloaded, skip...')
            continue

        download(bs4_parsed[i], post_dw_dir)
        urls[post]['urls'].append(bs4_parsed[i])
        save()

    Rlog.info(f'{len(bs4_parsed)=}')
    urls[post]['done'] = True
    save()

    # time.sleep(.5)
