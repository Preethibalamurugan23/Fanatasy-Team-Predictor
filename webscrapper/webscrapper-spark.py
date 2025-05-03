import requests
from bs4 import BeautifulSoup
import datetime
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StructType, StructField, StringType, DateType
import os

# Configure logging
logging.basicConfig(filename='cricbuzz_spark_scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_match_info_cricbuzz(base_url):
    """
    Fetches match information (link, location, date) from a Cricbuzz URL.
    This function is designed to be used within a Spark UDF.

    Args:
        base_url (str): The URL of the Cricbuzz match page.

    Returns:
        dict: A dictionary containing 'link', 'location', and 'date', or None on error.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        match_info = {}

        link_tag = soup.find('a', class_='text-hvr-underline')
        location_div = soup.find('div', class_='text-gray')
        date_span = soup.find('span', class_='schedule-date')

        if link_tag and 'href' in link_tag.attrs:
            link = f"https://www.cricbuzz.com{link_tag['href']}"
            match_info['link'] = link
            logging.debug(f"Extracted link: {link}")
        else:
            logging.debug("No link found in this match container.")
            match_info['link'] = None

        if location_div:
            location = location_div.text.strip()
            match_info['location'] = location
            logging.debug(f"Extracted location: {location}")
        else:
            logging.debug("No location found in this match container.")
            match_info['location'] = None

        if date_span and 'timestamp' in date_span.attrs:
            timestamp_ms = int(date_span['timestamp'])
            date_object = datetime.datetime.fromtimestamp(timestamp_ms / 1000).date()
            match_info['date'] = date_object
            logging.debug(f"Extracted date: {date_object}")
        else:
            logging.debug("No date information found in this match container.")
            match_info['date'] = None

        return match_info

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the base URL: {e}")
        return None
    except Exception as e:
        logging.error(f"Error processing HTML: {e}")
        return None



def main():
    """
    Main function to orchestrate the scraping process using Spark.
    """
    # Initialize Spark session
    spark = SparkSession.builder.appName("CricbuzzMatchScraper").getOrCreate()
    logging.info("Spark session initialized.")

    ipl_2025_url = "https://www.cricbuzz.com/cricket-series/9237/indian-premier-league-2025/matches"
    
    # Fetch the initial page to get the list of match URLs
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(ipl_2025_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        match_containers = soup.find_all('div', class_='cb-col-75 cb-col')  # Corrected class name
        match_links = [f"https://www.cricbuzz.com{c.find('a', class_='text-hvr-underline')['href']}"
                       for c in match_containers
                       if c.find('a', class_='text-hvr-underline') and 'href' in c.find('a', class_='text-hvr-underline').attrs]

        match_links_df = spark.createDataFrame(match_links, StringType()).toDF("url")
        logging.info(f"Created DataFrame with {match_links_df.count()} match URLs.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching initial match list: {e}")
        print(f"Error fetching initial match list: {e}")
        spark.stop()
        return
    except Exception as e:
        logging.error(f"Error parsing initial match list HTML: {e}")
        print(f"Error parsing initial match list HTML: {e}")
        spark.stop()
        return


    # Register the Python function as a Spark UDF
    get_match_info_udf = udf(get_match_info_cricbuzz,
                            StructType([
                                StructField("link", StringType()),
                                StructField("location", StringType()),
                                StructField("date", DateType())  # Changed to DateType()
                            ]))

    # Apply the UDF to each row of the DataFrame
    match_info_df = match_links_df.withColumn("match_info", get_match_info_udf(col("url")))
    logging.info("Applied UDF to extract match information.")

    # Select the exploded columns
    match_info_df = match_info_df.select(
        col("match_info.link").alias("link"),
        col("match_info.location").alias("location"),
        col("match_info.date").alias("date")
    )

    # Show the output in the console
    match_info_df.show(truncate=False)

    # Write to CSV using Spark
    csv_path = "cricbuzz_matches_spark.csv"
    match_info_df.write.csv(csv_path, header=True, mode="overwrite")
    logging.info(f"Saved match information to CSV: {csv_path}")
    print(f"Match information saved to {csv_path}")

    # Stop the Spark session
    spark.stop()
    logging.info("Spark session stopped.")



if __name__ == "__main__":
    main()
