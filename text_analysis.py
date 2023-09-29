import requests
from bs4 import BeautifulSoup
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from textstat import flesch_reading_ease, syllable_count, lexicon_count, sentence_count
from collections import Counter
import re

# Load the NLTK sentiment analyzer
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Load positive and negative word lists
with open('positive-words.txt', 'r') as positive_file:
    positive_words = set(positive_file.read().splitlines())

with open('negative-words.txt', 'r') as negative_file:
    negative_words = set(negative_file.read().splitlines())

# Function to count positive and negative words
def count_positive_negative_words(text):
    words = re.findall(r'\b\w+\b', text)
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    return positive_count, negative_count

# Function to count complex words based on syllable count
def count_complex_words(text, syllable_threshold=2):
    words = re.findall(r'\b\w+\b', text)
    complex_count = sum(1 for word in words if syllable_count(word) >= syllable_threshold)
    return complex_count

# Function to perform text analysis
def perform_text_analysis(text):
    # Initialize the 'words' variable
    words = re.findall(r'\b\w+\b', text)
    
    # Count positive and negative words
    positive_count, negative_count = count_positive_negative_words(text)

    # Compute polarity score
    polarity_score = sia.polarity_scores(text)['compound']

    # Compute subjectivity score (using the compound score from VADER sentiment)
    subjectivity_score = abs(polarity_score)

    # Calculate Flesch Reading Ease (similar to Flesch-Kincaid Grade Level)
    flesch_score = flesch_reading_ease(text)

    # Calculate percentage of complex words
    total_words = lexicon_count(text)
    percentage_complex_words = (count_complex_words(text) / total_words) * 100

    # Calculate FOG index
    fog_index = 0.4 * (flesch_score + percentage_complex_words)

    # Calculate average number of words per sentence
    avg_words_per_sentence = total_words / sentence_count(text)

    # Count personal pronouns (assuming common pronouns)
    pronoun_counts = Counter(word.lower() for word in words if word.lower() in ['i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'])

    # Calculate word count
    word_count = total_words

    # Calculate average word length
    avg_word_length = sum(len(word) for word in words) / word_count

    # Calculate syllables per word
    syllables_per_word = sum(syllable_count(word) for word in words) / word_count

    return {
        'POSITIVE SCORE': positive_count,
        'NEGATIVE SCORE': negative_count,
        'POLARITY SCORE': polarity_score,
        'SUBJECTIVITY SCORE': subjectivity_score,
        'AVG SENTENCE LENGTH': flesch_score,
        'PERCENTAGE OF COMPLEX WORDS': percentage_complex_words,
        'FOG INDEX': fog_index,
        'AVG NUMBER OF WORDS PER SENTENCE': avg_words_per_sentence,
        'COMPLEX WORD COUNT': count_complex_words(text),
        'WORD COUNT': word_count,
        'SYLLABLE PER WORD': syllables_per_word,
        'PERSONAL PRONOUNS': pronoun_counts['i'] + pronoun_counts['we'],
        'AVG WORD LENGTH': avg_word_length,
    }

# Load the input.xlsx file to get the list of URLs and corresponding URL_IDs
input_file = "input.xlsx"
df = pd.read_excel(input_file)

# Assuming the input.xlsx file has columns named 'URL_ID' and 'URL'
# You can adjust the column names accordingly if they are different in your file
url_ids = df['URL_ID'].tolist()
urls = df['URL'].tolist()

# Create a dictionary to store the results of text analysis for each URL
text_analysis_results = []

# Loop through the URLs, extract the content, and perform text analysis
for url_id, url in zip(url_ids, urls):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the article text
        article_text = ''
        for paragraph in soup.find_all('p'):
            if len(paragraph.text) > 50:  # Exclude short paragraphs
                article_text += paragraph.text + '\n'

        # Perform text analysis on the extracted article text
        analysis_result = perform_text_analysis(article_text)

        # Store the results in the list along with URL_ID and URL
        analysis_result['URL_ID'] = url_id
        analysis_result['URL'] = url

        text_analysis_results.append(analysis_result)

        print(f"Text analysis completed for URL_ID {url_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url} for URL_ID {url_id}: {e}")
    except Exception as e:
        print(f"Error performing text analysis for URL_ID {url_id}: {e}")

# Create a DataFrame from the list of text analysis results
output_df = pd.DataFrame(text_analysis_results)

# Save the DataFrame to an output Excel file with column names
output_file = "output_structure.xlsx"
output_df.to_excel(output_file, index=False, header=True)

print("Text analysis results saved to output_structure.xlsx")
