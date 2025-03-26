# vk_album_downloader
Python script to download list of albums (including albums from private communities) from [vk.com](https://www.vk.com). Implemented using VK API.

## Installation ##
In order to use this script you need to install [Python 3](https://www.python.org/downloads/).

You also need additional [vk_api](https://github.com/python273/vk_api) module. Clone its repo from Github to your local storage (e.g. folder where you have cloned the downloader) and write in CMD:

`$ cd vk_api`\
`$ py setup.py install`

**NOTE:** the pypi version of **vk_api** module doesn't work as of March 2025. Use the method provided above instead.

## Usage ##
```
usage: VK Album Downloader [-h] [-u USER_DATA] [-a ALBUMS_LIST] [-o OUTPUT_FOLDER] [-m] [-l]

Python script for bulk downloading photo albums from VK.

options:
  -h, --help            show this help message and exit
  -u USER_DATA, --user_data USER_DATA
                        where the file with user data is (default: "data.txt")
  -a ALBUMS_LIST, --albums_list ALBUMS_LIST
                        path to text file with albums links (default: "albums_list.txt")
  -o OUTPUT_FOLDER, --output_folder OUTPUT_FOLDER
                        where to put downloaded albums (default: "vk_downloaded_albums")
  -m, --export_metadata
                        export albums' metadata (photos, comments, etc.) to CSV file
  -l, --log             output a script run to .log file instead
```

This script allows you to download:
* albums from user's page: profile photos, wall photos, saved photos;
* albums from communities, including private ones.

You have to create following files to gather input information:
* *data.txt*. (Because of the *vk.com* privacy policy script needs to perform authentication before interacting with VK API. So put your login / phone number and password into this file).
* *albums_list.txt* (Just put list of url to the albums that you want do download).

Script will automatically create directory **vk_downloaded_albums** to save albums to in the directory where the script is located, if not specified.

**NOTE:** all the file / directory names and paths can be specified in the script, via passed arguments.

## Examples of the input files ##
### data.txt ###
File with user data:

```
test@gmail.com
super_strong_password
```

### albums_list.txt ###
File with list of album URLs:

```
https://vk.com/album-23402051_225962711
https://vk.com/album-23402051_249165407
```
