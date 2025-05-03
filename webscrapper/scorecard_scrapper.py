# # import requests
# # from bs4 import BeautifulSoup
# # import csv
# # import logging
# # import time

# # # Configure logging
# # logging.basicConfig(filename='cricbuzz_scorecard_scraper.log', level=logging.INFO,
# #                     format='%(asctime)s - %(levelname)s - %(message)s')


# # def get_scorecard_link(match_url):
# #     """
# #     Visits a Cricbuzz match page and extracts the link to the scorecard.

# #     Args:
# #         match_url (str): The URL of the Cricbuzz match page.

# #     Returns:
# #         str: The URL of the scorecard page, or None if not found.
# #     """
# #     logging.info(f"Fetching scorecard link from: {match_url}")
# #     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
# #     try:
# #         response = requests.get(match_url, headers=headers)
# #         response.raise_for_status()
# #         soup = BeautifulSoup(response.content, 'html.parser')

# #         # Find the link to the scorecard.
# #         # After inspecting the Cricbuzz match page, the scorecard link is within this div.
# #         scorecard_link_tag = soup.find('a', {'href': lambda href: href and 'live-cricket-scorecard' in href})
# #         if scorecard_link_tag and 'href' in scorecard_link_tag.attrs:
# #             scorecard_link = f"https://www.cricbuzz.com{scorecard_link_tag['href']}"
# #             logging.info(f"Found scorecard link: {scorecard_link}")
# #             return scorecard_link
# #         else:
# #             logging.warning(f"Scorecard link not found on: {match_url}")
# #             return None

# #     except requests.exceptions.RequestException as e:
# #         logging.error(f"Error fetching the match URL: {e}")
# #         return None
# #     except Exception as e:
# #         logging.error(f"Error parsing HTML: {e}")
# #         return None



# # def read_match_links_from_csv(filename="cricbuzz_matches.csv"):
# #     """
# #     Reads match links from a CSV file.

# #     Args:
# #         filename (str): The name of the CSV file.

# #     Returns:
# #         list: A list of match URLs.
# #     """
# #     logging.info(f"Reading match links from CSV file: {filename}")
# #     match_links = []
# #     try:
# #         with open(filename, 'r', encoding='utf-8') as csvfile:
# #             reader = csv.DictReader(csvfile)
# #             for row in reader:
# #                 if 'link' in row:
# #                     match_links.append(row['link'])
# #                 else:
# #                     logging.warning(f"Skipping row with missing 'link' column: {row}")
# #         logging.info(f"Read {len(match_links)} match links from CSV.")
# #         return match_links
# #     except FileNotFoundError:
# #         logging.error(f"File not found: {filename}")
# #         return []
# #     except Exception as e:
# #         logging.error(f"Error reading CSV file: {e}")
# #         return []

# # def scrape_scorecard(scorecard_url):
# #     """
# #     Scrapes the scorecard data from a Cricbuzz scorecard page.

# #     Args:
# #         scorecard_url (str): The URL of the Cricbuzz scorecard page.

# #     Returns:
# #         dict: A dictionary containing the scorecard data, or None on error.
# #     """
# #     logging.info(f"Scraping scorecard from: {scorecard_url}")
# #     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
# #     try:
# #         response = requests.get(scorecard_url, headers=headers)
# #         response.raise_for_status()
# #         soup = BeautifulSoup(response.content, 'html.parser')

# #         #  Extract the scorecard data.  This is the most complex part,
# #         #  and you'll need to inspect the Cricbuzz scorecard page's HTML
# #         #  structure very carefully to find the relevant elements.
# #         #  The example code below is just a placeholder - replace it
# #         #  with code that correctly extracts the data you need.
# #         scorecard_data = {}

# #         # Example:  This is where you'd put the logic to extract
# #         #  team names, batting tables, bowling tables, etc.
# #         #  Find the relevant HTML elements using soup.find(), soup.find_all(), etc.
# #         #  and extract the text and attributes you need.
# #         #  Store the data in the scorecard_data dictionary.

# #         team_names = [tag.text.strip() for tag in soup.find_all('h2', class_='cb-font-20')] # Example
# #         if len(team_names) > 1:
# #             scorecard_data['team1'] = team_names[0]
# #             scorecard_data['team2'] = team_names[1]

# #         # batting_tables = soup.find_all('table', class_='...')  #  Find batting tables
# #         # for table in batting_tables:
# #         #     #  Extract batting data (batsman, runs, etc.) from each table
# #         #     pass

# #         # bowling_tables = soup.find_all('table', class_='...')  # Find bowling tables
# #         # for table in bowling_tables:
# #         #    # Extract bowling data
# #         #    pass

# #         logging.info(f"Successfully scraped scorecard from: {scorecard_url}")
# #         return scorecard_data

# #     except requests.exceptions.RequestException as e:
# #         logging.error(f"Error fetching scorecard URL: {e}")
# #         return None
# #     except Exception as e:
# #         logging.error(f"Error parsing scorecard HTML: {e}")
# #         return None



# # if __name__ == "__main__":
# #     match_links = read_match_links_from_csv()

# #     if match_links:
# #         for match_url in match_links:
# #             scorecard_link = get_scorecard_link(match_url)
# #             if scorecard_link:
# #                 print(f"Match URL: {match_url}")
# #                 print(f"Scorecard URL: {scorecard_link}")
# #                 scorecard_data = scrape_scorecard(scorecard_link) # added this line
# #                 if scorecard_data:
# #                     print(scorecard_data)
# #                 time.sleep(2)  # Be respectful to the server
# #             else:
# #                 logging.warning(f"Could not retrieve scorecard link for {match_url}")
# #     else:
# #         print("No match links found to process.")

# import requests
# from bs4 import BeautifulSoup
# import csv
# import logging
# import time
# import re  # Import the regular expression module


# # Configure logging
# logging.basicConfig(filename='cricbuzz_scorecard_scraper.log', level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')


# def get_scorecard_link(match_url):
#     """
#     Visits a Cricbuzz match page and extracts the link to the scorecard.

#     Args:
#         match_url (str): The URL of the Cricbuzz match page.

#     Returns:
#         str: The URL of the scorecard page, or None if not found.
#     """
#     logging.info(f"Fetching scorecard link from: {match_url}")
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
#     try:
#         response = requests.get(match_url, headers=headers)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.content, 'html.parser')

#         # Find the link to the scorecard.
#         # After inspecting the Cricbuzz match page, the scorecard link is within this div.
#         scorecard_link_tag = soup.find('a', {'href': lambda href: href and 'live-cricket-scorecard' in href})
#         if scorecard_link_tag and 'href' in scorecard_link_tag.attrs:
#             scorecard_link = f"https://www.cricbuzz.com{scorecard_link_tag['href']}"
#             logging.info(f"Found scorecard link: {scorecard_link}")
#             return scorecard_link
#         else:
#             logging.warning(f"Scorecard link not found on: {match_url}")
#             return None

#     except requests.exceptions.RequestException as e:
#         logging.error(f"Error fetching the match URL: {e}")
#         return None
#     except Exception as e:
#         logging.error(f"Error parsing HTML: {e}")
#         return None



# def read_match_links_from_csv(filename="cricbuzz_matches.csv"):
#     """
#     Reads match links from a CSV file.

#     Args:
#         filename (str): The name of the CSV file.

#     Returns:
#         list: A list of dictionaries, where each dictionary contains
#               'link', 'location', and 'date' for a match.  Returns empty list on error.
#     """
#     logging.info(f"Reading match links from CSV file: {filename}")
#     match_data = []
#     try:
#         with open(filename, 'r', encoding='utf-8') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 if 'link' in row and 'location' in row and 'date' in row:
#                     match_data.append({'link': row['link'], 'location': row['location'], 'date': row['date']})
#                 else:
#                     logging.warning(f"Skipping row with missing 'link', 'location', or 'date' column: {row}")
#         logging.info(f"Read {len(match_data)} match links from CSV.")
#         return match_data
#     except FileNotFoundError:
#         logging.error(f"File not found: {filename}")
#         return []
#     except Exception as e:
#         logging.error(f"Error reading CSV file: {e}")
#         return []



# def scrape_scorecard(match_data, scorecard_url):
#     """
#     Scrapes the scorecard data from a Cricbuzz scorecard page.

#     Args:
#         match_data (dict): A dictionary containing  'link', 'location', and 'date' for a match.
#         scorecard_url (str): The URL of the Cricbuzz scorecard page.

#     Returns:
#         list: A list of dictionaries, where each dictionary represents a batter's stats,
#               or None on error.
#     """
#     logging.info(f"Scraping scorecard from: {scorecard_url}")
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
#     try:
#         response = requests.get(scorecard_url, headers=headers)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.content, 'html.parser')



#         innings_data = []

#         # Find all innings containers.
#         innings_containers = soup.find_all('div', class_='cb-col cb-col-100 cb-ltst-wgt-hdr')
#         logging.info(f"Found {len(innings_containers)} innings containers")

#         for innings_container in innings_containers:


#             batter_rows = innings_container.find_all('div', class_='cb-col cb-col-100 cb-scrd-itms')
#             logging.info(f"Found {len(batter_rows)} batter rows")
#             for row in batter_rows:
#                 # Extract the data.
#                 name_element = row.find('a')
#                 if name_element:
#                     batter_name = name_element.text.strip()
#                 else:
#                     name_element = row.find('div', class_='cb-col cb-col-25')
#                     if name_element:
#                         batter_name = name_element.text.strip()
#                     else:
#                         batter_name = "NA"
#                 cols = row.find_all('div', class_=re.compile(r'cb-col cb-col-8 text-right')) # Changed selector
#                 if len(cols) >= 4:  # Changed condition
#                     runs = cols[0].text.strip()
#                     balls = cols[1].text.strip()
#                     fours = cols[2].text.strip()
#                     sixes = cols[3].text.strip()
#                     logging.debug(f"Extracted batter data: {batter_name}, {runs}, {fours}, {sixes}")
#                     innings_data.append({
#                         'venue': match_data['location'],
#                         'date': match_data['date'],
#                         'batter_name': batter_name,
#                         'runs': runs,
#                         'fours': fours,
#                         'sixes': sixes
#                     })
#                 else:
#                     logging.warning(f"Incorrect number of columns in batter row. Expected at least 4, got {len(cols)} for {batter_name}")
#         return innings_data

#     except requests.exceptions.RequestException as e:
#         logging.error(f"Error fetching scorecard URL: {e}")
#         return None
#     except Exception as e:
#         logging.error(f"Error parsing scorecard HTML: {e}")
#         return None



# def save_to_csv(data, filename="batting_stats.csv"):
#     """
#     Saves the extracted batting data to a CSV file.

#     Args:
#         data (list): A list of dictionaries, where each dictionary represents a batter's stats.
#         filename (str): The name of the CSV file to save to.
#     """
#     logging.info(f"Saving batting data to CSV file: {filename}")
#     if not data:
#         logging.warning("No data to save to CSV.")
#         return

#     fieldnames = ['venue', 'date', 'batter_name', 'runs', 'fours', 'sixes'] # Removed team names
#     try:
#         with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#             writer.writeheader()
#             for row in data:
#                 writer.writerow(row)
#         logging.info(f"Successfully saved batting data to {filename}")
#         print(f"Batting data saved to {filename}")
#     except Exception as e:
#         logging.error(f"Error saving to CSV: {e}")




# if __name__ == "__main__":
#     match_data_list = read_match_links_from_csv() # Changed to read match data

#     if match_data_list:
#         all_batting_data = [] # Changed variable name
#         for match_data in match_data_list: # Changed variable name
#             match_url = match_data['link']
#             scorecard_link = get_scorecard_link(match_url)
#             if scorecard_link:
#                 logging.info(f"Processing scorecard for : {match_url}")
#                 batting_data = scrape_scorecard(match_data, scorecard_link) # Pass match_data
#                 if batting_data:
#                     all_batting_data.extend(batting_data) # Extend the list
#                 time.sleep(2)  # Be respectful to the server
#             else:
#                 logging.warning(f"Could not retrieve scorecard link for {match_url}")
#         if all_batting_data:
#             save_to_csv(all_batting_data)
#         else:
#             print("No batting data to save.")
#     else:
#         print("No match links found to process.")

import requests
from bs4 import BeautifulSoup
import csv
import logging
import time
import re  # Import the regular expression module


# Configure logging
logging.basicConfig(filename='cricbuzz_scorecard_scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_scorecard_link(match_url):
    """
    Visits a Cricbuzz match page and extracts the link to the scorecard.

    Args:
        match_url (str): The URL of the Cricbuzz match page.

    Returns:
        str: The URL of the scorecard page, or None if not found.
    """
    logging.info(f"Fetching scorecard link from: {match_url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    try:
        response = requests.get(match_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the link to the scorecard.
        # After inspecting the Cricbuzz match page, the scorecard link is within this div.
        scorecard_link_tag = soup.find('a', {'href': lambda href: href and 'live-cricket-scorecard' in href})
        if scorecard_link_tag and 'href' in scorecard_link_tag.attrs:
            scorecard_link = f"https://www.cricbuzz.com{scorecard_link_tag['href']}"
            logging.info(f"Found scorecard link: {scorecard_link}")
            return scorecard_link
        else:
            logging.warning(f"Scorecard link not found on: {match_url}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the match URL: {e}")
        return None
    except Exception as e:
        logging.error(f"Error parsing HTML: {e}")
        return None



def read_match_links_from_csv(filename="cricbuzz_matches.csv"):
    """
    Reads match links from a CSV file.

    Args:
        filename (str): The name of the CSV file.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              'link', 'location', and 'date' for a match.  Returns empty list on error.
    """
    logging.info(f"Reading match links from CSV file: {filename}")
    match_data = []
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'link' in row and 'location' in row and 'date' in row:
                    match_data.append({'link': row['link'], 'location': row['location'], 'date': row['date']})
                else:
                    logging.warning(f"Skipping row with missing 'link', 'location', or 'date' column: {row}")
        logging.info(f"Read {len(match_data)} match links from CSV.")
        return match_data
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        return []
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return []



def scrape_scorecard(match_data, scorecard_url):
    """
    Scrapes the scorecard data from a Cricbuzz scorecard page.

    Args:
        match_data (dict): A dictionary containing  'link', 'location', and 'date' for a match.
        scorecard_url (str): The URL of the Cricbuzz scorecard page.

    Returns:
        list: A list of dictionaries, where each dictionary represents a batter's stats,
              or None on error.
    """
    logging.info(f"Scraping scorecard from: {scorecard_url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    try:
        response = requests.get(scorecard_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')



        innings_data = []

        # Find all innings containers.
        innings_containers = soup.find_all('div', class_='cb-col cb-col-100 cb-ltst-wgt-hdr')
        logging.info(f"Found {len(innings_containers)} innings containers")

        for innings_container in innings_containers:


            batter_rows = innings_container.find_all('div', class_='cb-col cb-col-100 cb-scrd-itms')
            logging.info(f"Found {len(batter_rows)} batter rows")
            for row in batter_rows:
                # Extract the data.
                name_element = row.find('a')
                if name_element:
                    batter_name = name_element.text.strip()
                else:
                    name_element = row.find('div', class_='cb-col cb-col-25')
                    if name_element:
                        batter_name = name_element.text.strip()
                    else:
                        batter_name = "NA"
                cols = row.find_all('div', class_=re.compile(r'cb-col cb-col-8 text-right')) # Changed selector
                if len(cols) >= 4:  # Changed condition
                    runs = int(cols[0].text.strip())
                    balls = int(cols[1].text.strip())
                    fours = int(cols[2].text.strip())
                    sixes = int(cols[3].text.strip())
                    logging.debug(f"Extracted batter data: {batter_name}, {runs}, {fours}, {sixes}")

                    # Calculate fantasy score
                    fantasy_score = (
                        runs +
                        (fours * 1) +  # 1 point per boundary
                        (fours * 4) +  # Boundary bonus
                        (sixes * 1) +  # 1 point per six
                        (sixes * 6)  # Six bonus
                    )
                    if runs >= 25:
                        fantasy_score += 4
                    if runs >= 50:
                        fantasy_score += 8
                    if runs >= 75:
                        fantasy_score += 12
                    if runs >= 100:
                        fantasy_score += 16
                    if runs == 0:
                        fantasy_score -= 2

                    innings_data.append({
                        'venue': match_data['location'],
                        'date': match_data['date'],
                        'batter_name': batter_name,
                        'runs': runs,
                        'fours': fours,
                        'sixes': sixes,
                        'fantasy_score': fantasy_score
                    })
                    logging.info(f"Extracted data for {batter_name}: Runs={runs}, 4s={fours}, 6s={sixes}, Fantasy Score={fantasy_score}") # added log
                else:
                    logging.warning(f"Incorrect number of columns in batter row. Expected at least 4, got {len(cols)} for {batter_name}")
        return innings_data

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching scorecard URL: {e}")
        return None
    except Exception as e:
        logging.error(f"Error parsing scorecard HTML: {e}")
        return None



def save_to_csv(data, filename="batting_Fantasy.csv", write_header=True):
    """
    Saves the extracted batting data to a CSV file.

    Args:
        data (list): A list of dictionaries, where each dictionary represents a batter's stats.
        filename (str): The name of the CSV file to save to.
        write_header (bool): Whether to write the header row.
    """
    logging.info(f"Saving batting data to CSV file: {filename}, write_header={write_header}")
    if not data:
        logging.warning("No data to save to CSV.")
        return

    fieldnames = ['venue', 'date', 'batter_name', 'runs', 'fours', 'sixes', 'fantasy_score'] # Added fantasy_score
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile: # changed to 'a'
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            for row in data:
                writer.writerow(row)
        logging.info(f"Successfully saved batting data to {filename}")
        print(f"Batting data saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")




if __name__ == "__main__":
    match_data_list = read_match_links_from_csv() # Changed to read match data

    if match_data_list:
        all_batting_data = [] # Changed variable name
        for match_data in match_data_list: # Changed variable name
            match_url = match_data['link']
            scorecard_link = get_scorecard_link(match_url)
            if scorecard_link:
                logging.info(f"Processing scorecard for : {match_url}")
                batting_data = scrape_scorecard(match_data, scorecard_link) # Pass match_data
                if batting_data:
                    all_batting_data.extend(batting_data) # Extend the list
                    save_to_csv(batting_data, write_header=(len(all_batting_data) == 0)) # save after each match
                time.sleep(2)  # Be respectful to the server
            else:
                logging.warning(f"Could not retrieve scorecard link for {match_url}")
        if all_batting_data:
            print("All batting data processed.")
        else:
            print("No batting data to save.")
    else:
        print("No match links found to process.")
