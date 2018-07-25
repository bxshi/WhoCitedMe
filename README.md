# Who Cited Me?

Ever need to know any big names or famous papers cited you? 
Ever need to get a detailed list of citations for some application (_cough EB-1 cough_)? 

This handy script could help you.

# What does this script do?

1. It will go through a person's Google Scholar page, parse every publication, its citation count, 
all citations' citation count, the basic information of their authors (if they happen to have a GScholar
page), and store them into JSON files for you.
2. It will sort all authors that cited your work in descending order based on their citations. This could
help you identify established scholars who cited you.
3. It will also sort all publications that cited your work in descending order based on their citations. 

# What is the catch?
Well, I only tested this with less than hundred citations, and some time Google aware that I'm a bot.
So this may not work if you have a huge number of citations. You might be able to workaround this by
adding some code to pause the process when a captcha appears.

Secondly, I use Selenium to do the scraping, and this script will open a lot Chrome windows, which might
be annoying depending on how you feel about it.

# Installation

First, please install Headless Chrome. A Google search could do the trick, or 
[Let Me Google This For You](http://lmgtfy.com/?q=chrome+headless+selenium+linux)

Then, please clone the repo, install all required packages, and run the script.

```bash
git clone https://github.com/bxshi/WhoCitedMe.git
cd WhoCitedMe
pip install selenium
python3 gscholar.py GSCHOLAR_URL
```

Enjoy :)

# TODO
* [ ] Initialize `Paper`, `Author`, `Citation` objects via saved JSON file.
* [ ] Be more smart to avoid triggering captcha.
