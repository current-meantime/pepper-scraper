# Pepper Scraper

Pepper Scraper is a Python utility designed to extract and organize comments from selected threads on the Pepper.pl platform. This tool serves as the initial stage in building a comprehensive knowledge base on various topics.

## Overview

The scraper collects comments, replies, and associated metadata from specified Pepper.pl threads, organizing the information into structured JSON files. These files can then be utilized for further processing, analysis, or as input for AI-powered knowledge extraction.

## Key Features

- Scrapes comments and replies from Pepper.pl threads
- Captures metadata such as usernames, timestamps, and reaction counts
- Organizes scraped data into JSON files for easy processing
- Supports multi-page comment sections
- Handles nested replies and expanded comment threads

Additionally:
- The scraper is adjusted to **Chrome**
- Most scraping is done with Playwright

## Intended Use

While the primary intention is to feed the scraped data into an AI API for knowledge extraction and refinement, the collected information can be used for various purposes, including:

- Sentiment analysis
- User behavior studies
- Topic modeling
- Content summarization
- Trend identification

Since the reactions to the comments are included in the output and are a valuable source for assessing mood, intent, etc., it may be beneficial to prompt an AI going through the scraped data to take them into consideration.

The scraper is designed in a way that the selection of the treads that are supposed to be scraped is done by **manually adding Pepper deals to the Saved Tab**. If you scroll through the Pepper platform and encounter a deal that may contain an informative discussion, add it to this tab by clicking on a bookmark icon. You may run the scraper after each added deal or after many of them have been added - that's up to you.

## Intended behavior of the script
The program decides to scrape a deal if:
1. It hasn't been scraped before.
2. It has been scraped before but new comments appeared.

That's why it creates a state.json file on the first run and compares data that is stored there with the deals in the Saved Tab to avoid unneccesary scraping.

## Setup

In order to run this program smoothly, you'll need to:
1. Create a clean Google Chrome profile or choose an existing one.
2. Create an account on `pepper.pl`. (unless you already have one)
3. While using the chosen Chrome profile, log into your account. **Enable the option to stay logged in.**
4. Navigate to your profile's page and then to the "Saved" tab (pl. "Zapisane"). Save the link of this page.
5. In your file system, find out the path to `chrome.exe` and save it.
It's typically: `C:/Program Files/Google/Chrome/Application/chrome.exe`
6. Find out the directory path of the Chrome's user profile that you will use for scraping. Save this path.
7. Choose the directory path that will be the output directory for the program and save it.
8. Update the `pepper-scraper.py` with proper paths in the Config class.
9. Use `pip` to install `playwright` and `beautifulsoup4`.

It may be benefictial to ensure there are no extensions installed, as they could disrupt the flow of the program. Feel free to experiment, though. In my case, the script works without issues with uBlockOrigin installed.

Aditionally, **the scraper might not work if there are other Chrome instances open**. It is best to close them all before running the script.


### Advice on finding the chrome user profile's directory path

Paths to non-default profiles are typically:

`C:/Users/YourUsername/AppData/Local/Google/Chrome/User Data/Profile 1` (or any other number after 'Profile')

The default user profile's path is typically:

`C:\Users\alemr\AppData\Local\Google\Chrome\User Data\Default`

You may actually use 'Default' as the scraping profile as well.

If you see many user profile directories and you're not sure which corresponds to the profile that you've just created for the purpose of scraping:
1. Open Chrome's `User Data` directory in your file manager.
2. Look at the modification date of the 'Profile' folders - which one is the latest? Save its directory path.
3. Alternatively, open the 'Profile' folders one by one and look for the `Googe Profile.ico` file. They're going to have a miniature picture of your profile's picture contained within the icon. If it's the one you want to use, save its directory path.
4. Alternatively, in this `User Data` directory, go to the search tab, type `Googe Profile.ico` and look through the results to find this minature picture, then save the directory path.

## Usage
After you finished the setup and entered the data to `pepper-scraper.py`'s Config class correctly, add at least one item to the 'Saved' tab in your Pepper account, then run the program.

Note: When I stopped the running script prematurely, the next time it tried to open the "Saved deals" page, Chrome had some problems with loading it. In that case, I had to manually close the browser, open it again and click on the chosen profile, close the browser again, then run the script once more. You may want to try it out if you encounter such problems.

## Future plans
As of now, the script is quite slow. In the future, its performance most likely will get optimized.