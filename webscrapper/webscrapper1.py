# import requests
# from bs4 import BeautifulSoup
# import logging

# # Configure logging
# logging.basicConfig(filename='webscrapping.log', level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

# def scrape_match_links_and_venues(url):
#     """
#     Scrapes the match link and venue for each IPL match from the given URL.
#     """
#     logging.info(f"Starting scraping for match links and venues from: {url}")
#     match_details = []
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.content, 'html.parser')
#         logging.info(f"Successfully fetched content from: {url}")

#         match_blocks = soup.find_all('div', class_='ds-bg-fill-content-prime hover:ds-bg-ui-fill-translucent')

#         for block in match_blocks:
#             link_tag = block.find('a', class_='ds-no-tap-higlight')
#             if link_tag and 'href' in link_tag.attrs:
#                 match_link = "https://www.espncricinfo.com" + link_tag['href']

#                 venue_span = block.find('span', class_='ds-flex ds-items-center')
#                 venue = None
#                 if venue_span:
#                     anchor_tag = venue_span.find('a', title='IPL')
#                     if anchor_tag and anchor_tag.previous_sibling:
#                         parts = anchor_tag.previous_sibling.strip().split('•')
#                         if len(parts) > 1:
#                             venue_part = parts[1].split(',')[0].strip()
#                             venue = venue_part

#                 match_details.append({'link': match_link, 'venue': venue})
#                 logging.info(f"Found match link: {match_link}, Venue: {venue}")

#         logging.info(f"Found details for {len(match_details)} matches on {url}.")
#         return match_details

#     except requests.exceptions.RequestException as e:
#         logging.error(f"Error fetching {url}: {e}")
#         return []
#     except Exception as e:
#         logging.error(f"An error occurred during parsing: {e}")
#         return []

# if __name__ == "__main__":
#     target_url = "https://www.espncricinfo.com/series/ipl-2025-1449924/match-schedule-fixtures-and-results"
#     match_info = scrape_match_links_and_venues(target_url)

#     if match_info:
#         print("Match Links and Venues:")
#         for match in match_info:
#             print(f"Link: {match['link']}")
#             print(f"Venue: {match['venue']}")
#             print("-" * 20)
#     else:
#         print("Could not scrape match links and venues.")

import requests
from bs4 import BeautifulSoup
import logging
import time

# Configure logging
logging.basicConfig(filename='webscrapping.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_match_links_and_venues(url):
    """
    Scrapes the match link and venue for each IPL match from the given URL.
    Includes more headers and a delay to try and avoid blocking.
    """
    logging.info(f"Starting scraping for match links and venues from: {url}")
    match_details = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        logging.info(f"Successfully fetched content from: {url}")

        match_blocks = soup.find_all('div', class_='ds-bg-fill-content-prime hover:ds-bg-ui-fill-translucent')

        for block in match_blocks:
            time.sleep(1)  # Introduce a 1-second delay between processing each match block

            link_tag = block.find('a', class_='ds-no-tap-higlight')
            if link_tag and 'href' in link_tag.attrs:
                match_link = "https://www.espncricinfo.com" + link_tag['href']

                venue_span = block.find('span', class_='ds-flex ds-items-center')
                venue = None
                if venue_span:
                    anchor_tag = venue_span.find('a', title='IPL')
                    if anchor_tag and anchor_tag.previous_sibling:
                        parts = anchor_tag.previous_sibling.strip().split('•')
                        if len(parts) > 1:
                            venue_part = parts[1].split(',')[0].strip()
                            venue = venue_part

                match_details.append({'link': match_link, 'venue': venue})
                logging.info(f"Found match link: {match_link}, Venue: {venue}")

        logging.info(f"Found details for {len(match_details)} matches on {url}.")
        return match_details

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return []
    except Exception as e:
        logging.error(f"An error occurred during parsing: {e}")
        return []

if __name__ == "__main__":
    target_url = "https://www.espncricinfo.com/series/ipl-2025-1449924/match-schedule-fixtures-and-results"
    match_info = scrape_match_links_and_venues(target_url)

    if match_info:
        print("Match Links and Venues:")
        for match in match_info:
            print(f"Link: {match['link']}")
            print(f"Venue: {match['venue']}")
            print("-" * 20)
    else:
        print("Could not scrape match links and venues.")