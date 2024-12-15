from flask import Flask, request, jsonify, render_template
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import googleapiclient.discovery
import matplotlib.pyplot as plt

app = Flask(__name__)

DEVELOPER_KEY = "AIzaSyAUXWjWm153kY3mjqnWPfANnwENPd83Niw"
video_id = "elmZ-SFw5a4"
max_results = 1000
min_likes_threshold = 0


def get_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = analyzer.polarity_scores(text)

    if sentiment_scores['compound'] >= 0.05:
        return "positive"
    elif sentiment_scores['compound'] <= -0.05:
        return "negative"
    else:
        return "neutral"


def retrieve_comments(video_id, max_results):
    comments = []

    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=DEVELOPER_KEY)

    next_page_token = None
    while len(comments) < max_results:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, max_results - len(comments)),  # Maximum comments per request
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            text = comment['textDisplay']
            sentiment = get_sentiment(text)

            if comment['likeCount'] >= min_likes_threshold:
                comments.append({
                    'author': comment['authorDisplayName'],
                    'published_at': comment['publishedAt'],
                    'updated_at': comment['updatedAt'],
                    'like_count': comment['likeCount'],
                    'text': text,
                    'sentiment': sentiment
                })

        if 'nextPageToken' in response:
            next_page_token = response['nextPageToken']
        else:
            break

    return comments


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/input')
def input():
    return render_template('input.html')


@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    try:
        video_id = request.form['video_id']
        comments_count = int(request.form['comments'])
        comments = retrieve_comments(video_id, comments_count)
        return render_template('result.html', comments=comments)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/pie_chart')
def show_pie_chart():
    try:
        comments = retrieve_comments(video_id, max_results)
        sentiment_stats = calculate_sentiment_statistics(comments)
        plot_pie_chart(sentiment_stats)
        return render_template('pie_chart.html')
    except Exception as e:
        return jsonify({'error': str(e)})


def calculate_sentiment_statistics(comments):
    sentiment_stats = {
        'positive': sum(1 for comment in comments if comment['sentiment'] == 'positive'),
        'neutral': sum(1 for comment in comments if comment['sentiment'] == 'neutral'),
        'negative': sum(1 for comment in comments if comment['sentiment'] == 'negative')
    }
    return sentiment_stats


def plot_pie_chart(sentiment_stats):
    labels = ['Positive', 'Neutral', 'Negative']
    sizes = [sentiment_stats['positive'], sentiment_stats['neutral'], sentiment_stats['negative']]
    colors = ['green', 'gray', 'red']
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Sentiment Distribution')
    plt.axis('equal')
    plt.savefig('static/pie_chart.png')


if __name__ == '__main__':
    app.run(debug=True)
