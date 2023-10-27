This is a simple Python3 script to scrape  [Fandom site](https://dragonsdogma.fandom.com/wiki/)
and get  much information on various items available in the game.

List of defined numeric `ID`s is from [here](https://docs.google.com/spreadsheets/d/1ZhegmKtUfIFACWGAksZeSZMqOWG2YuzWcDA5aYm2PAc/edit#gid=2076196192)
with minor editing and corrections (BEWARE: I might have goofed badly!).

Installation under Linux is straightforward (I don't use Windows 
for programming):

```bash
# clone reository
git clone <repository>
#enter project root directory
cd ScrapeFandom/
# create basic Vitual ENVironment 
python3 -m venv venv
# install required non-standard-lib packages
# i.e.: lxml and requests
venv/bin/pip install -r requirements.txt
# run the script
venv/bin/python ParseFandom.py 
```
After execution (it takes a bit of time) you should have 
several new files: the most important are:
- `Fandom.py`: the resulting script containing the whole scraped 
   information in `list` format and a couple of helper `dict`s:
  - `all_by_id[int]`: access info by `ID` value
  - `all_by_name[int]`: access info by in-game name
- `resources/images/*`: collection of images pertaining to objects.

  Names are computed from in-game item name.

  Note: These are images and not the icons used in-game
  as I didn't find a reliable way to getthem fromFandom.
  I am thinking about scraping them from 
  [Fextralife](https://dragonsdogma.wiki.fextralife.com/Items)
  but that's for another day.

In the code there are several workarounds needed to account
for differences in Wiki pages edited over a quite sizable time span.
I wouldn't be surprised if "further enhancements" will break the 
scraping code; please notify me if you find inconsistencies.

Suggestions and comments (and patches) are always welcome.

Enjoy!