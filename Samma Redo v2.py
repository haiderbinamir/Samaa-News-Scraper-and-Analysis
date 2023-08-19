# Import necessary libraries
import requests
import nltk
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import RegexpTokenizer
from nltk.probability import FreqDist
from nltk.stem import WordNetLemmatizer

# Define the base URL and date range
base_url = "https://www.samaaenglish.tv/money/"
start_date = "2023-01-1"
end_date = "2023-01-2"
start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

# Generate a list of URLs based on the date range
url_list = []
current_date = start_date_dt
while current_date <= end_date_dt:
    formatted_date = current_date.strftime("%Y-%m-%d")
    url = f"{base_url}{formatted_date}"
    url_list.append(url)
    current_date += timedelta(days=1)

# Retrieve article URLs
urls = url_list
all_article_list = []
for url in urls:
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')
        article_list = []

        for article in articles:
            title = article.find('h2', class_='story__title').text.strip()
            article_url = article.find('a', class_='story__link')['href']
            timestamp_element = article.find('span', class_='timestamp--time')
            timestamp = timestamp_element['title'] if timestamp_element else None

            if timestamp:
                article_info = {
                    "Title": title,
                    "URL": article_url,
                    "Timestamp": timestamp
                }
                article_list.append(article_info)

        all_article_list.extend(article_list)
    else:
        print(f"Failed to retrieve the webpage for URL: {url}. Status code: {response.status_code}")

# Extract article texts from the URLs
urls = [entry['URL'] for entry in all_article_list]
url_text_list = []

for url in urls:
    retries = 3

    while retries > 0:
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            url_texts = []

            for paragraph in paragraphs:
                text = paragraph.get_text()

                if text.strip() != "Get the latest news and updates from Samaa TV" and \
                   text.strip() != "Copyright © 2023 SAMAA TV. All Rights Reserved.":
                    url_texts.append(text)

            url_text_list.append({'URL': url, 'Text': url_texts})
            break
        else:
            print(f"Failed to retrieve the webpage for URL: {url}, Status code: {response.status_code}")
            retries -= 1
            if retries > 0:
                print("Retrying...")

# Combine and clean article texts
for data in url_text_list:
    text_entries = data['Text']
    combined_text = '\n'.join(text_entries).replace('\n', ' ')
    data['Text'] = combined_text

# Combine article information and texts
combined_list = []
for article in all_article_list:
    matching_url_dict = next((item for item in url_text_list if item['URL'] == article['URL']), None)

    if matching_url_dict:
        combined_dict = {**article, **matching_url_dict}
        combined_list.append(combined_dict)

# Perform sentiment analysis on article texts
nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

data_list = combined_list
result_frames = []

tokenizer = RegexpTokenizer('\w+')
stopwords = nltk.corpus.stopwords.words("english")
wordnet_lem = WordNetLemmatizer()
sid = SentimentIntensityAnalyzer()

for data_dict in data_list:
    text = data_dict['Text']
    tokenized_text = tokenizer.tokenize(text.lower())
    filtered_text = [word for word in tokenized_text if word not in stopwords]
    fdist = FreqDist(filtered_text)
    lemmatized_text = [wordnet_lem.lemmatize(word) for word in filtered_text if fdist[word] >= 1]
    sentiment_scores = sid.polarity_scores(' '.join(lemmatized_text))
    temp_df = pd.DataFrame({
        'Title': [data_dict['Title']],
        'URL': [data_dict['URL']],
        'Timestamp': [data_dict['Timestamp']],
        'Text': [text],
        'Positive': [sentiment_scores['pos']],
        'Negative': [sentiment_scores['neg']],
        'Neutral': [sentiment_scores['neu']],
        'Compound': [sentiment_scores['compound']]
    })
    result_frames.append(temp_df)

# Combine sentiment analysis results
results = pd.concat(result_frames, ignore_index=True)

print(results)