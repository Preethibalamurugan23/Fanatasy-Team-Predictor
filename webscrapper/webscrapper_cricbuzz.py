# # import requests
# # from bs4 import BeautifulSoup
# # import datetime

# # def get_match_info_cricbuzz(base_url):
# #     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
# #     try:
# #         response = requests.get(base_url, headers=headers)
# #         response.raise_for_status()
# #         soup = BeautifulSoup(response.content, 'html.parser')
# #         match_info_list = []
# #         match_containers = soup.find_all('div', class_='cb-col-75 cb-col')
# #         for container in match_containers:
# #             link_tag = container.find('a', class_='text-hvr-underline')
# #             location_div = container.find('div', class_='text-gray')
# #             date_span = container.find('span', class_='schedule-date')
# #             link = None
# #             location = None
# #             date_object = None

# #             if link_tag and 'href' in link_tag.attrs:
# #                 link = f"https://www.cricbuzz.com{link_tag['href']}"

# #             if location_div:
# #                 location = location_div.text.strip()

# #             if date_span and 'timestamp' in date_span.attrs:
# #                 timestamp_ms = int(date_span['timestamp'])
# #                 date_object = datetime.datetime.fromtimestamp(timestamp_ms / 1000).date()

# #             if link and location and date_object:
# #                 match_info_list.append({'link': link, 'location': location, 'date': date_object})

# #         return match_info_list
# #     except requests.exceptions.RequestException as e:
# #         print(f"Error fetching the base URL: {e}")
# #         return []

# # if __name__ == "__main__":
# #     ipl_2025_url = "https://www.cricbuzz.com/cricket-series/9237/indian-premier-league-2025/matches"
# #     match_info = get_match_info_cricbuzz(ipl_2025_url)

# #     if match_info:
# #         print(f"Found information for {len(match_info)} matches:")
# #         for info in match_info:
# #             print(f"Link: {info['link']}")
# #             print(f"Location: {info['location']}")
# #             print(f"Date: {info['date']}")
# #             # print(f"Date Type: {type(info['date'])}")
# #             print("-" * 30)
# #     else:
# #         print("No match information found.")

# import requests
# from bs4 import BeautifulSoup
# import datetime
# import csv
# import logging

# # Configure logging
# logging.basicConfig(filename='cricbuzz_scrapper.log', level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')


# def get_match_info_cricbuzz(base_url):
#     logging.info(f"Fetching match info from: {base_url}")
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
#     try:
#         response = requests.get(base_url, headers=headers)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.content, 'html.parser')
#         match_info_list = []
#         match_containers = soup.find_all('div', class_='cb-col-75 cb-col')
#         logging.info(f"Found {len(match_containers)} match containers.")
#         for container in match_containers:
#             link_tag = container.find('a', class_='text-hvr-underline')
#             location_div = container.find('div', class_='text-gray')
#             date_span = container.find('span', class_='schedule-date')
#             link = None
#             location = None
#             date_object = None

#             if link_tag and 'href' in link_tag.attrs:
#                 link = f"https://www.cricbuzz.com{link_tag['href']}"
#                 logging.debug(f"Extracted link: {link}")

#             if location_div:
#                 location = location_div.text.strip()
#                 logging.debug(f"Extracted location: {location}")

#             if date_span and 'timestamp' in date_span.attrs:
#                 timestamp_ms = int(date_span['timestamp'])
#                 date_object = datetime.datetime.fromtimestamp(timestamp_ms / 1000).date()
#                 logging.debug(f"Extracted date: {date_object}")

#             if link and location and date_object:
#                 match_info_list.append({'link': link, 'location': location, 'date': date_object})
#                 logging.debug(f"Appended match info: Link={link}, Location={location}, Date={date_object}")

#         logging.info(f"Successfully extracted info for {len(match_info_list)} matches.")
#         return match_info_list
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Error fetching the base URL: {e}")
#         return []


# def save_to_csv(match_info_list, filename="cricbuzz_matches.csv"):
#     logging.info(f"Saving match info to CSV file: {filename}")
#     try:
#         with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
#             fieldnames = ['date', 'link', 'location']
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#             writer.writeheader()
#             for match_info in match_info_list:
#                 writer.writerow(match_info)
#                 logging.debug(f"Wrote row to CSV: {match_info}")
#             logging.info(f"Successfully saved match info to {filename}")

#         print("Match information saved to cricbuzz_matches.csv")

#     except Exception as e:
#         logging.error(f"Error saving to CSV: {e}")


# if __name__ == "__main__":
#     ipl_2025_url = "https://www.cricbuzz.com/cricket-series/9237/indian-premier-league-2025/matches"
#     match_info = get_match_info_cricbuzz(ipl_2025_url)

#     if match_info:
#         for info in match_info:
#             print(f"Link: {info['link']}")
#             print(f"Location: {info['location']}")
#             print(f"Date: {info['date']}")
#             print(f"Date Type: {type(info['date'])}")
#             print("-" * 30)
#         save_to_csv(match_info)
#     else:
#         print("No match information found.")

import requests
from bs4 import BeautifulSoup
import datetime
import csv
import logging

# Configure logging
logging.basicConfig(filename='cricbuzz_scrapper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_match_info_cricbuzz(base_url):
    logging.info(f"Fetching match info from: {base_url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        match_info_list = []
        match_containers = soup.find_all('div', class_='cb-col-75 cb-col')
        logging.info(f"Found {len(match_containers)} match containers.")
        for container in match_containers:
            link_tag = container.find('a', class_='text-hvr-underline')
            location_div = container.find('div', class_='text-gray')
            date_span = container.find('span', class_='schedule-date')
            link = None
            location = None
            date_object = None

            if link_tag and 'href' in link_tag.attrs:
                link = f"https://www.cricbuzz.com{link_tag['href']}"
                logging.debug(f"Extracted link: {link}")
            else:
                logging.debug("No link found in this match container.")

            if location_div:
                location = location_div.text.strip()
                logging.debug(f"Extracted location: {location}")
            else:
                logging.debug("No location found in this match container.")

            if date_span and 'timestamp' in date_span.attrs:
                timestamp_ms = int(date_span['timestamp'])
                date_object = datetime.datetime.fromtimestamp(timestamp_ms / 1000).date()
                logging.debug(f"Extracted date: {date_object}")
            else:
                logging.debug("No date information found in this match container.")

            if link and location and date_object:
                match_info_list.append({'link': link, 'location': location, 'date': date_object})
                logging.info(f"Extracted and stored match info: Link={link}, Location={location}, Date={date_object}")
            elif link:
                logging.warning(f"Incomplete match info found (missing location or date): Link={link}")

        logging.info(f"Successfully processed {len(match_info_list)} matches.")
        return match_info_list
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the base URL: {e}")
        return []


def save_to_csv(match_info_list, filename="cricbuzz_matches.csv"):
    logging.info(f"Saving match info to CSV file: {filename}")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'link', 'location']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for match_info in match_info_list:
                writer.writerow(match_info)
                logging.debug(f"Wrote row to CSV: {match_info}")
            logging.info(f"Successfully saved match info to {filename}")

        print("Match information saved to cricbuzz_matches.csv")

    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")


if __name__ == "__main__":
    ipl_2025_url = "https://www.cricbuzz.com/cricket-series/9237/indian-premier-league-2025/matches"
    match_info = get_match_info_cricbuzz(ipl_2025_url)

    if match_info:
        for info in match_info:
            print(f"Link: {info['link']}")
            print(f"Location: {info['location']}")
            print(f"Date: {info['date']}")
            print("-" * 30)
        save_to_csv(match_info)
    else:
        print("No match information found.")