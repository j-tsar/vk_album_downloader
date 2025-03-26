import argparse
import csv
from datetime import datetime
import os
import re
import requests
import sys
import vk_api


def handler_captcha(captcha):
    key = input(f'Enter captcha code: {captcha.get_url()}: ').strip()
    return captcha.try_again(key)


def handler_2fa():
    code = input(f'Enter 2FA code: ').strip()
    return code, False


def print_progress(value, end_value, bar_length=20):
    percent = float(value) / end_value
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write("\rProgress: [{0}] {1}% ({2} / {3})".format(
        arrow + spaces, int(round(percent * 100)),
        value, end_value))
    sys.stdout.flush()


SERVICE_IDS = {'0': '-6', '00': '-7', '000': '-15'}


def process_url(url):
    verification = re.compile(r'^https://vk.com/album(-?[\d]+)_([\d]+)$')
    o = verification.match(url)
    if not o:
        raise ValueError('invalid album link: {}'.format(url))
    owner_id = o.group(1)
    album_id = o.group(2)
    if album_id in SERVICE_IDS:
        return {'owner_id': owner_id, 'album_id': SERVICE_IDS.get(o.group(2))}
    else:
        return {'owner_id': owner_id, 'album_id': album_id}


def read_data(path_to_user_data, path_to_albums_list):
    lines = []
    try:
        with open(path_to_user_data, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError as e:
        print(e)
        print('please, fix the file name or either path to it')
        sys.exit(e.errno)

    if (lines.__len__() < 2):
        print('unable to read user credentials')
        print('please, check your user data in the file')
        sys.exit(1)
    l = lines[0]
    p = lines[1]

    queries = []
    try:
        with open(path_to_albums_list, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError as e:
        print(e)
        print('please, fix the file name either in the folder or in the script')
        sys.exit(e.errno)

    queries = []
    for url in lines:
        try:
            queries.append(process_url(url))
        except ValueError as e:
            print(e)
    return l, p, queries


def download_image(url, local_file_name):
    response = requests.get(url, stream=True)
    if not response.ok:
        print('bad response:', response)
        return
    with open(local_file_name, 'wb') as file:
        for chunk in response.iter_content(1024):
            # if not chunk:
            #     break
            file.write(chunk)
    return


def gather_comments(api, o, a):
    comments = []
    temp = []
    i = 0
    while True:
        temp += api.photos.getAllComments(owner_id=o, album_id=a, need_likes=1, offset=i, count=100)['items']
        comments += temp
        if len(temp) < 100:
            break

        temp.clear()
        i += 100
    return comments


PAT_ILLEGAL_CHARS = re.compile(r'[/|:?<>*"\\]')


def fix_illegal_album_title(title: str) -> str:
    return PAT_ILLEGAL_CHARS.sub('_', title.rstrip())


def main():
    parser = argparse.ArgumentParser(
                    prog='VK Album Downloader',
                    description='Python script for bulk downloading'
                    ' photo albums from VK.')
    parser.add_argument('-u', '--user_data',
                        help='where the file with user data is'
                        ' (default: "data.txt")',
                        default='data.txt')
    parser.add_argument('-a', '--albums_list',
                        help='path to text file with albums links'
                        ' (default: "albums_list.txt")',
                        default='albums_list.txt')
    parser.add_argument('-o', '--output_folder',
                    help='where to put downloaded albums'
                    ' (default: "vk_downloaded_albums")',
                    default='vk_downloaded_albums')
    parser.add_argument('-m', '--export_metadata',
                        help='export albums\' metadata (photos,'
                        ' comments, etc.) to CSV file',
                        action='store_true')
    parser.add_argument('-l', '--log',
                        help='output a script run to .log file instead',
                        action='store_true')
    args = parser.parse_args()

    if args.log:
        log_file = open("vk_album_downloader.log", "a")
        sys.stdout = log_file
        print("started " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    l, p, queries = read_data(args.user_data, args.albums_list)
    vk_session = vk_api.VkApi(l, p, captcha_handler=handler_captcha, auth_handler=handler_2fa)

    try:
        vk_session.auth()
    except Exception as e:
        print('could not authenticate to vk.com')
        print(e)
        print('please, check your user data in the file')
        sys.exit(1)

    api = vk_session.get_api()
    l = None
    p = None

    print('number of albums to download: {}'.format(queries.__len__()))
    for q in queries:
        o = q['owner_id']
        a = q['album_id']

        try:
            album = api.photos.getAlbums(owner_id=o, album_ids=a)['items'][0]
            images_num = album['size']
            album_title = "[{o_id}]-[{a_id}] ".format(o_id=o, a_id=a) + fix_illegal_album_title(album['title'])

            photos = []

            for i in range(1 + images_num // 1000):
                photos += api.photos.get(owner_id=o, album_id=a, photo_sizes=1, count=min(images_num - i*1000, 1000), offset=i*1000)['items']
        except vk_api.exceptions.ApiError as e:
            print('exception:')
            print(e)
            return

        album_path = os.path.join(args.output_folder, album_title)
        if not os.path.exists(album_path):
            os.makedirs(album_path)

        if args.export_metadata:
            metadata_album = open(os.path.join(album_path, 'album.csv'),
                                    'w', newline='', encoding="utf-8-sig")
            fieldnames_album = list(album.keys())
            writer = csv.DictWriter(metadata_album, fieldnames=fieldnames_album)
            writer.writeheader()
            row_data = {key: value for key, value in zip(fieldnames_album, album.values())}
            writer.writerow(row_data)
            metadata_album.close()

            metadata_comments = open(os.path.join(album_path, 'comments.csv'),
                                     'w', newline='', encoding="utf-8-sig")
            comments = gather_comments(api, o, a) if args.export_metadata else None
            fieldnames_comments = list(comments[0].keys())
            writer = csv.DictWriter(metadata_comments, fieldnames=fieldnames_comments)
            writer.writeheader()
            for i in range(len(comments)):
                row_data = {key: value for key, value in zip(fieldnames_comments, comments[i].values())}
                writer.writerow(row_data)
            metadata_comments.close()

            metadata_photos = open(os.path.join(album_path, 'photos.csv'),
                                   'w', newline='', encoding="utf-8-sig")
            fieldnames_photos = list(photos[0])
            writer = csv.DictWriter(metadata_photos, fieldnames=fieldnames_photos)
            writer.writeheader()

        print('downloading album: ' + a)
        cnt = 0
        for p in photos:
            largest_image_width = p['sizes'][0]['width']
            largest_image_src = p['sizes'][0]['url']

            if largest_image_width == 0:
                largest_image_src = p['sizes'][p['sizes'].__len__() - 1]['url']
            else:
                for size in p['sizes']:
                    if size['width'] > largest_image_width:
                        largest_image_width = size['width']
                        largest_image_src = size['url']

            extension = os.path.splitext(largest_image_src)[-1].split('?')[0]
            download_image(largest_image_src, os.path.join(album_path, str(p['id']) + extension))
            cnt += 1
            print_progress(cnt, images_num)

            if args.export_metadata:
                row_data = {key: value for key, value in zip(fieldnames_photos, p.values())}
                writer.writerow(row_data)
        if args.export_metadata:
            metadata_photos.close()
        print()
    if args.log:
        print("\nfinished " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("======================================================")
        log_file.close()


if __name__ == "__main__":
    main()
