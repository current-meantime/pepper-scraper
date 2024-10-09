from playwright.sync_api import sync_playwright
import json
from pathlib import Path
import time
from datetime import datetime
from bs4 import BeautifulSoup

class Config:
    """Configuration class to store paths and settings."""

    def __init__(self):
        self.browser_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe" # Change to your own chrome.exe path if it's different
        self.chrome_user_data_dir = r"C:\Users\this_user\AppData\Local\Google\Chrome\User Data" # Change to your own Chrome's User Data dir path
        self.profile_directory_name = "Profile 6" # Change to your chosen profile directory's name
        self.this_script_file_path = Path(__file__)
        self.this_script_directory = self.this_script_file_path.parent
        self.output_path = self.this_script_directory # update output_path with your chosen output path in string format
        self.json_output_dir = self.output_path / "scraped_data" # One json file per scraped deal will be stored there
        self.state_file = self.this_script_directory / "state.json"
        self.saved_deals_page = "https://www.pepper.pl/profile/this_user/saved-deals" # Change the url to your Saved Deals page


class StateManager:
    """Manages the state file for tracking comment counts."""

    def __init__(self, state_file):
        self.state_file = state_file

    def create_state_file(self):
        """Creates a new empty state file and returns an empty dictionary."""
        with open(self.state_file, "w") as f:
            json.dump({}, f)
        print(f"Creating a new state file at '{self.state_file}'.")
        return {}

    def get_comment_count(self):
        """
        Retrieves the comment count for each deal from the state file
        to compare it with the current comment count of a deal that is being scraped.
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"The state file contains invalid JSON.")
                return self.create_state_file()
        else:
            print(f"\nThe state file does not exist.")
            return self.create_state_file()

    def save_data_to_state_file(self, comments_count):
        """Updates the state file with current comment count bound to a deal's url."""
        with open(self.state_file, "w") as f:
            json.dump(comments_count, f)
        print(f"Saving the new state file at '{self.state_file}'.")

class DataSaver:
    """Handles saving scraped data to JSON files."""

    @staticmethod
    def save_data_to_json(data, file_path):
        """Saves data to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data saved to {file_path}")

class DateHelper:
    """Helper class for date-related operations."""

    @staticmethod
    def get_date(item='full date'):
        """Returns the current date in the specified format."""
        now = datetime.now()
        current_day = now.day
        current_month = now.month
        current_year = str(now.year)
        date = f"{current_day}.{current_month}.{current_year}"
        return current_year if item == 'year' else date

class PepperScraper:
    """Main class for scraping Pepper website."""

    def __init__(self, config, state_manager):
        self.config = config
        self.state_manager = state_manager

    def get_saved_deals(self, page):
        """Collects links and titles of saved deals."""
        page.goto(self.config.saved_deals_page)
        print("Navigated to saved deals page.")
        time.sleep(2)

        strong_elements = page.locator('strong.thread-title')
        div_parent = strong_elements.locator('xpath=..')
        strong_elements_count = strong_elements.count()
        saved_deals = {}

        for i in range(strong_elements_count):
            div = div_parent.nth(i)
            first_a = div.locator('a').nth(0)
            href = first_a.get_attribute('href')
            title = first_a.text_content()
            print(f"Deal found: {title}, Link: {href}")
            comments_icon = page.locator('a[title="Comments"]').nth(i)
            comment_count = int(comments_icon.text_content())
            print("Comment count of this deal: " + str(comment_count))

            saved_deals[href] = {
                "Title": title,
                "Comment count": comment_count
            }

        return saved_deals

    def expand_visible_replies(self, page):
        """Scrolls the page and clicks visible 'more replies' buttons."""
        previous_height = 0
        
        while True:
            more_replies_buttons = page.locator('button[data-t="moreReplies"]:visible')
            count = more_replies_buttons.count()
            print(f"Found {count} visible 'See more replies' buttons.")

            for i in range(count):
                try:
                    button = more_replies_buttons.nth(i)
                    button.click()
                    print(f"Clicked visible button {i + 1} of {count}.")
                    page.wait_for_load_state('networkidle')
                    time.sleep(1)
                except Exception as e:
                    print(f"Error clicking visible button {i + 1}: {e}")
                    break

            page.evaluate('window.scrollBy(0, window.innerHeight)')
            time.sleep(1)

            new_height = page.evaluate('document.body.scrollHeight')
            if new_height == previous_height:
                print("Reached the bottom of the page.")
                break
            previous_height = new_height

    def click_next_page(self, page):
        """Clicks the 'Next page' button if it's not disabled."""
        try:
            next_button = page.locator('button[aria-label="Następna strona"]')
            is_disabled = next_button.get_attribute('disabled')
            
            if not is_disabled:
                next_button.click()
                print("Clicked 'Next page'.")
                page.wait_for_load_state('networkidle')
                return True
            else:
                print("'Next page' is disabled.")
                return False
        except:
            print("There is only one page.")
            return False

    def extract_comment_content(self, comment_element):
        """Extracts comment content including emoticons and images."""
        content = ""
        comment_body = comment_element.locator('> div > div')
        if comment_body.count() > 0:
            html_content = comment_body.inner_html()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for element in soup.children:
                if element.name == 'i' and 'emoji' in element.get('class', []):
                    content += f" {element.get('title', '')} "
                elif element.name == 'img':
                    content += f" [Image: {element.get('src', '')}] "
                elif element.name != 'span':
                    content += element.get_text() if element.name else str(element)

            return content.strip()
        else:
            print("Comment body element not found")
            return ""

    def get_comments(self, page):
        """Collects main comments and their replies."""
        comments_data = []

        while True:
            self.expand_visible_replies(page)
            comment_containers = page.locator('div.commentList-comment')

            comment_list_count = comment_containers.count()
            print(f"There are {comment_list_count} comment lists")
            for i in range(comment_list_count):
                main_comment_container = comment_containers.nth(i)

                only_main_comment_container = main_comment_container.locator('article.comment').nth(0)
                only_main_comment_body = only_main_comment_container.locator('div.comment-body')
                
                comment_body = self.extract_comment_content(only_main_comment_body)
                print(f"Main comment: {comment_body}")

                username = only_main_comment_container.locator('button[data-t="showUserShortProfile"]').text_content().strip()
                print(f"Username: {username}")

                comment_reactions = self.get_reactions(only_main_comment_container)

                time_elements = main_comment_container.locator('time')
                if time_elements.count() > 1:
                    comment_date = time_elements.nth(1).text_content()
                else:
                    comment_date = time_elements.nth(0).text_content()
                    comment_date_list = comment_date.split()
                    # If a comment has been recently added, it's not going to have a proper datetime format but rather minutes and hours stated
                    if 'min' in comment_date_list or 'g' in comment_date_list:
                        # In this case, we fetch the current datetime
                        comment_date = DateHelper.get_date()
                    else:
                        # Otherwise, the format is only date and month, so a year needs to be added
                        comment_date = comment_date + ' ' + DateHelper.get_date('year')

                print(f"Comment date: {comment_date}")

                replies = self.get_replies(main_comment_container)

                comments_data.append({
                    "username": username,
                    "comment_body": comment_body,
                    "comment_date": comment_date,
                    "reactions": comment_reactions,
                    "replies": replies
                })

            if not self.click_next_page(page):
                break

        return comments_data

    def get_reactions(self, container):
        """Collects reaction data for a comment or reply."""
        comment_reactions = {}
        reaction_button = container.locator('button[title="Reakcje"]')
        img_element = reaction_button.locator('img')
        img_element_count = img_element.count()

        for i in range(img_element_count):
            single_reaction = img_element.nth(i)
            reaction_type = single_reaction.get_attribute('alt')
            span_element = single_reaction.locator('xpath=following-sibling::span')
            reaction_count = span_element.text_content()
            comment_reactions[reaction_type] = int(reaction_count)

        return comment_reactions

    def get_replies(self, main_comment_container):
        """Collects replies to the main comment."""
        replies = []
        replies_container = main_comment_container.locator("section.comment-replies")
        reply_items = replies_container.locator("article.comment")
        reply_count = reply_items.count()
        print(f"Found {reply_count} replies")

        for i in range(reply_count):
            reply_item = reply_items.nth(i)
            username = reply_item.locator('button[data-t="showUserShortProfile"]').text_content().strip()
            print(f"Reply by: {username}")
            
            comment_div = reply_item.locator('div.comment-body')
            try:
                reply_addressee = comment_div.locator('button').text_content().strip()
            except:
                reply_addressee = "-"
            comment_body = self.extract_comment_content(comment_div)
            print(f"Reply content: {comment_body}")
            
            comment_date = reply_item.locator('time').nth(0).text_content()
            comment_date_list = comment_date.split()
            if 'min' in comment_date_list or 'g' in comment_date_list:
                comment_date = DateHelper.get_date()
            else:
                comment_date = comment_date + ' ' + DateHelper.get_date('year')
            print(f"Reply date: {comment_date}")

            comment_reactions = self.get_reactions(reply_item)

            replies.append({
                "username": username,
                "specifically replied to": reply_addressee,
                "comment_body": comment_body,
                "comment_date": comment_date,
                "reactions": comment_reactions
            })
        
        return replies

    def scrape_deal_details(self, page, deal_url):
        """Collects deal details: description and comments."""
        print(f"Scraping deal page: {deal_url}")
        page.goto(deal_url)
        title = page.locator('title').text_content()
        author = page.locator('span.thread-user span').text_content()

        group = ""
        groups = page.query_selector_all('a[data-t="group"]')
        print(f"Found {len(groups)} group elements.")

        for element in groups:
            category = element.text_content().strip()
            group += category + ", "

        group = group[:-2] if group else group
        print(f"Group(s): {group}")
        
        description_element = page.locator('div.userHtml.userHtml-content.overflow--wrap-break.space--mt-3[data-t="description"]')
        description_text = description_element.locator('div').text_content()
        print(f"Deal description: {description_text}")

        comments = self.get_comments(page)

        return title, author, group, description_text, comments

    def scrape_data(self):
        """Main function to scrape data from Pepper website."""
        comments_count = self.state_manager.get_comment_count()

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.config.chrome_user_data_dir,
                executable_path=self.config.browser_path,
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    f"--profile-directory={self.config.profile_directory_name}"
                ]
            )

            page = browser.new_page()
            print("Browser launched and page created.")

            saved_deals = self.get_saved_deals(page)

            # A deal gets scraped if it hasn't been scraped before, i.e is not listed in the state.json file
            # and if new comments appeared from the last time it was scraped
            for deal_url, deal_data in saved_deals.items():
                if not deal_data.get("Comment count", 0):
                    print("Omitting a deal since there are no comments.")
                    continue
                if comments_count.get(deal_url, 0) >= deal_data["Comment count"]:
                    print("Omitting a deal since no new comments were added.")
                    continue
                title, author, group, description, comments = self.scrape_deal_details(page, deal_url)
                deal_data["Author"] = author.strip()
                deal_data["Group"] = group
                deal_data["Description"] = description
                deal_data["Comments"] = comments
                
                title = title[:-9].strip()  # Remove "- Pepper.pl" suffix
                title = ''.join(c for c in title if c.isalnum() or c.isspace())
                title = title.replace(' ', '_')
                filename = f"{title}.json"

                json_file_path = self.config.json_output_dir / filename
                DataSaver.save_data_to_json(deal_data, json_file_path)

                comments_count[deal_url] = deal_data["Comment count"]

                self.state_manager.save_data_to_state_file(comments_count)

            browser.close()

def main():
    """Main function to run the scraper."""
    print("Starting the Pepper scraper...")
    config = Config()
    state_manager = StateManager(config.state_file)
    scraper = PepperScraper(config, state_manager)
    scraper.scrape_data()
    print("Scraping completed.")

if __name__ == "__main__":
    main()
