import os
import random
from datetime import date
import unicodedata

import pandas as pd
import tweepy as tw
from pymed import PubMed
from pymed.article import PubMedArticle

consumer_key = str(os.getenv("CONSUMER_KEY"))
consumer_secret = str(os.getenv("CONSUMER_SECRET"))

access_token = str(os.getenv("ACCESS_TOKEN"))
access_secret = str(os.getenv("ACCESS_SECRET"))

auth = tw.OAuthHandler(consumer_key, consumer_secret)

api = tw.API(auth, wait_on_rate_limit=True)

day = date.today().weekday()


def load_account_data() -> pd.DataFrame:
    data = None

    try:
        data = pd.read_csv("account.csv")
    except IOError:
        print("Accounts file does not exist! Will create new one.")

    return data


def login(account_data: pd.DataFrame):
    if account_data is None or account_data.empty:
        try:
            redirect_url = auth.get_authorization_url()
            print("Log in with this link: " + redirect_url)
            verifier = input("Verification Code: ")
            auth.get_access_token(verifier=verifier)

            # String access token
            a_t = str(unicodedata.normalize('NFKD', auth.access_token).encode("ascii", "ignore"))

            # String access secret
            a_s = str(unicodedata.normalize('NFKD', auth.access_token_secret).encode("ascii", "ignore"))

            account_data = pd.DataFrame(data={"access_token": a_t, "access_secret":
                a_s}, index=["value"])
            pd.DataFrame(account_data).to_csv("account.csv")
        except tw.TweepError or IOError:
            print("An error occurred during authorization!")
    else:
        a_t = str(account_data.iat[0, 1]).replace('b', '', 1).replace("'", "")
        a_s = str(account_data.iat[0, 2]).replace('b', '', 1).replace("'", "")

        auth.set_access_token(a_t, a_s)


articles = []
selected_articles = []


def build_tweet(article: PubMedArticle) -> []:
    title = article.title
    if article.publication_date is not None:
        title_date = article.title + " (" + str(article.publication_date) + ")"
    abstract = article.abstract
    if article.abstract is not None:
        if len(article.abstract) >= 229:
            abstract = article.abstract[0:220] + "..."
    else:
        abstract = "No abstract available for this article."
    link = "https://www.ncbi.nlm.nih.gov/pubmed/" + str(article.pubmed_id)

    # Tweet Title
    tt = "Title: " + title_date + '\n\n' + "Link: " + link

    if len(tt) >= 240:
        tt = -1

    return [tt, "Abstract: " + abstract]


def send_tweets(components: []):
    try:
        if components[0] != -1:
            title_tweet = api.update_status(status=components[0])
            api.update_status(status=components[1], in_reply_to_status_id=title_tweet.id)
        else:
            pass
    except tw.TweepError as error:
        print(error)


def pre_frame_all_tweets() -> {}:
    tweet_ids = []
    tweet_interactions = []

    all_tweets = tw.Cursor(api.user_timeline).items()

    for tweet in all_tweets:
        all_interactions = tweet.retweet_count + tweet.favorite_count

        tweet_ids.append(tweet.id)
        tweet_interactions.append(all_interactions)

    return {"Tweet ID": tweet_ids, "Tweet Interactions": all_interactions}


def main():
    login(load_account_data())

    mode = int(input("Select a mode (1 - Data test | 2 - Post): "))

    if mode == 1:
        data = pre_frame_all_tweets()
        tweet_frame = pd.DataFrame(data)

        print(tweet_frame.head(15))
    elif mode == 2:
        topic = input("What would you like to post about?: ")
        pubmed = PubMed(tool=str(os.getenv("APP_NAME")), email=str(os.getenv("APP_EMAIL")))
        results = pubmed.query(topic, max_results=100)

        for article in results:
            articles.append(article)

        for count in range(0, 5):
            chosen_article = articles[random.randrange(0, len(articles))]

            if chosen_article not in selected_articles:
                selected_articles.append(chosen_article)

        for art in selected_articles:
            tweet = build_tweet(art)
            send_tweets(tweet)
    else:
        print("Invalid input! Use 1 or 2!")
    if input("Run again? (Y/N): ").capitalize() == "Y":
        main()
    else:
        print("Exiting!")


if __name__ == '__main__':
    print("=======================================\n",
          "        Canary Curator            ",
          "\n=======================================")
    main()
