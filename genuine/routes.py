import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from genuine import app, db, bcrypt, mail
from genuine.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             PostForm, RequestResetForm, ResetPasswordForm)
from genuine.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
import re
import csv
import pandas as pd
import nltk
import tweepy  # To consume Twitter's API  # For number computing
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, send_file
from textblob import TextBlob

#nltk.download()
import collections
from nltk.corpus import stopwords
stemmer=nltk.PorterStemmer()
stops = set(stopwords.words("english"))

@app.route("/")

@app.route("/home")
def home():
    return render_template('home.html')

@app.route('/credentials',methods=['GET','POST'])
def credentials():
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('analysis'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

consumer_key ='VTJBKxgKMle3ajF6yKGlMgB3f'
consumer_secret='PPOikMrLC33ZIwLMhpHsejE2QDbawo5ONmOz2zVjQ3xRoEnlAg'

access_token='1154630220558696448-KDqGJGhimyFYk4nlPJ1xiKdOaMk6ZO'
access_token_secret='esQD1aO6SPKL7eusI4FUSJUNlam4ulEi1HIkvTQniga2O'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
size=1000

# Return API with authentication:
api = tweepy.API(auth)

@app.route('/index',methods=['GET','POST'])
def analysis():
    if request.method=="POST":
        topic=request.form['topic'] #topic request keyword
        topic=topic+'-filter:retweets'
        test_data=api.search(topic, count =size,lang="en",tweet_mode='extended')
        user_name=[]
        creationdatee=[]
        polarity=[]
        image=[]
        follower_count=[]
        verified_check=[]
        following_count=[]
        retweets_count=[]
        favourite_count=[]
        tweet_id=[]
        actual_tweets=[]
        bio=[]

        def truncate(f, n):
            '''Truncates/pads a float f to n decimal places without rounding'''
            s = '{}'.format(f)
            if 'e' in s or 'E' in s:
                return '{0:.{1}f}'.format(f, n)
            i, p, d = s.partition('.')
            return '.'.join([i, (d + '0' * n)[:n]])

        for tweet in test_data:
            user_name.append(tweet.user.screen_name)
            creationdatee.append(tweet.created_at)
            polarity.append(truncate((TextBlob(tweet.full_text).sentiment.polarity), 3))
            image.append(tweet.user.profile_image_url_https)
            follower_count.append(tweet.user.followers_count)
            verified_check.append(tweet.user.verified)
            following_count.append(tweet.user.friends_count)
            retweets_count.append(tweet.retweet_count)
            favourite_count.append(tweet.favorite_count)
            tweet_id.append(tweet.id)
            actual_tweets.append(tweet.full_text)
            bio.append(tweet.user.description)

        creationdate = []
        for i in creationdatee:
            creationdate.append(i.strftime('%m/%d/%Y %I:%M:%S'))

        preprocessed_words = []

        def preprocessing(raw_data):
            review_text = BeautifulSoup(raw_data, "html.parser").get_text()  # removes html tags
            x = re.sub("[@]\w+", " ", review_text)  # remove usertags
            x = re.sub("[^a-zA-Z]", " ", x)
            x = re.sub("[#\(\)\[\]]", " ", x)  # remove brackets and from hashtags
            x = re.sub("https?[\w./:]+", " ", x)  # remove urls
            x = re.sub("\.{2,}", " ", x)  # replacing 2+ dots to space
            x = re.sub("(.)\1+", "\1\1", x)  # replace multiple chars to 2 chars
            x = re.sub("(-|\')", " ", x)  # removing -|\''
            words = x.lower().split()  # split into words
            meaningful_words = list(filter(lambda x: (stemmer.stem(x)), words))
            meaningful_words = [w for w in meaningful_words if not w in stops]
            for wo in meaningful_words:
                if not 2 < len(wo) < 31:
                    meaningful_words.remove(wo)

            for we in meaningful_words:
                preprocessed_words.append(we)

        top_words1 = []
        for tweet1 in test_data:
            preprocessing(tweet1.full_text)

        final_words_count = collections.Counter(preprocessed_words)

        for letter, count in final_words_count.most_common(30):
            top_words1.append(letter)

        top_words = top_words1[10:30]

        output = pd.DataFrame(data={"SentimentText": actual_tweets[0:size],
                                    "UserName": user_name[0:size], "CreationDate": creationdate[0:size],
                                    "Image": image[0:size],
                                    "FollowerCount": follower_count[0:size], "FollowingCount": following_count[0:size],
                                    "Verified": verified_check[0:size], "ReTweet": retweets_count[0:size],
                                    "Likes": favourite_count[0:size], "ID": tweet_id[0:size],
                                    "Polarity": polarity[0:size], "bio": bio[0:size]})

        output.to_csv("Entire_Output.csv", index=False)
        with open("Entire_Output.csv", newline='') as csvfile:
            spamreader = csv.DictReader(csvfile)
            sortedlist = sorted(spamreader, key=lambda row: (row['Polarity']), reverse=True)

        with open('Sorted_Entire_Output.csv', 'w') as f:
            fieldnames = ['SentimentText', 'UserName', 'CreationDate', 'Image', 'Location',
                          'FollowerCount', 'FollowingCount', 'Verified', 'ReTweet', 'Likes', 'ID', 'Polarity', 'bio']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in sortedlist:
                writer.writerow(row)

        with open("Sorted_Entire_Output.csv", newline='') as f0:
            reader = csv.DictReader(f0)
            rows0 = [row for row in reader if float(row['Polarity']) > 0]

        with open('Positive_Output.csv', 'w') as f:
            fieldnames = ['SentimentText', 'UserName', 'CreationDate', 'Image', 'Location',
                          'FollowerCount', 'FollowingCount', 'Verified', 'ReTweet', 'Likes', 'ID', 'Polarity', 'bio']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows0:
                writer.writerow(row)

        with open("Sorted_Entire_Output.csv", newline='') as f0:
            reader = csv.DictReader(f0)
            rows1 = [row for row in reader if float(row['Polarity']) < 0]

        with open('Negative_Output.csv', 'w') as f:
            fieldnames = ['SentimentText', 'UserName', 'CreationDate', 'Image', 'Location',
                          'FollowerCount', 'FollowingCount', 'Verified', 'ReTweet', 'Likes', 'ID', 'Polarity', 'bio']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows1:
                writer.writerow(row)

        with open("Sorted_Entire_Output.csv", newline='') as f0:
            reader = csv.DictReader(f0)
            rows2 = [row for row in reader if float(row['Polarity']) == 0.0]

        with open('Neutral_Output.csv', 'w') as f:
            fieldnames = ['SentimentText', 'UserName', 'CreationDate', 'Image', 'Location',
                          'FollowerCount', 'FollowingCount', 'Verified', 'ReTweet', 'Likes', 'ID', 'Polarity', 'bio']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows2:
                writer.writerow(row)

        df0 = pd.read_csv("Positive_Output.csv")
        sentiment_text0 = df0['SentimentText']
        user_name0 = df0['UserName']
        polarity0 = df0['Polarity']
        creationdate0 = df0['CreationDate']
        image0 = df0['Image']
        follower_count0 = df0["FollowerCount"]
        following_count0 = df0["FollowingCount"]
        verified0 = df0['Verified']
        retweets_count0 = df0['ReTweet']
        favourite_count0 = df0['Likes']
        tweet_id0 = df0['ID']
        bio0 = df0['bio']
        row0, column0 = df0.shape

        df1 = pd.read_csv("Negative_Output.csv")
        sentiment_text1 = df1['SentimentText']
        user_name1 = df1['UserName']
        polarity1 = df1['Polarity']
        creationdate1 = df1['CreationDate']
        image1 = df1['Image']
        follower_count1 = df1["FollowerCount"]
        following_count1 = df1["FollowingCount"]
        verified1 = df1['Verified']
        retweets_count1 = df1['ReTweet']
        favourite_count1 = df1['Likes']
        tweet_id1 = df1['ID']
        bio1 = df1['bio']
        row1, column1 = df1.shape

        df2 = pd.read_csv("Neutral_Output.csv")
        sentiment_text2 = df2['SentimentText']
        user_name2 = df2['UserName']
        polarity2 = df2['Polarity']
        creationdate2 = df2['CreationDate']
        image2 = df2['Image']
        follower_count2 = df2["FollowerCount"]
        following_count2 = df2["FollowingCount"]
        verified2 = df2['Verified']
        retweets_count2 = df2['ReTweet']
        favourite_count2 = df2['Likes']
        tweet_id2 = df2['ID']
        bio2 = df2['bio']
        row2, column2 = df2.shape

        positive = row0
        negative = row1
        neutral = row2

        labels = ["Positive", "Negative", "Neutral"]
        values = [positive, negative, neutral]
        colors = ["#70db70", " #ff6666", "#4dffff"]

        return render_template('analysis.html', topic=topic, set=zip(values, labels, colors), values=values, colors=colors,
                               labels=labels, sentiment_text1=sentiment_text1, sentiment_text0=sentiment_text0,
                               sentiment_text2=sentiment_text2,
                               user_name1=user_name1, user_name0=user_name0, user_name2=user_name2, polarity1=polarity1,
                               polarity0=polarity0, polarity2=polarity2, creationdate1=creationdate1,
                               creationdate0=creationdate0,creationdate2=creationdate2, image0=image0, image1=image1, image2=image2,
                               pol="Polarity : ", follower_count0=follower_count0, follower_count1=follower_count1,
                               follower_count2=follower_count2,
                               following_count0=following_count0, following_count1=following_count1,
                               following_count2=following_count2, verified0=verified0, verified1=verified1,
                               verified2=verified2, followers="Followers : ", following="Following : ",
                               retweets_count0=retweets_count0, retweets_count1=retweets_count1,
                               retweets_count2=retweets_count2, favourite_count0=favourite_count0,
                               favourite_count1=favourite_count1, favourite_count2=favourite_count2,
                               tweet_id0=tweet_id0, tweet_id1=tweet_id1, tweet_id2=tweet_id2, top_words=top_words,
                               bio0=bio0, bio1=bio1, bio2=bio2, output=output)

    return render_template('analysis.html')
