import re

from pathlib import Path
def get_tweets_from_text(username,text):
    spans = re.findall('<span(.*?)>\s*(.*?)\s*</span>', text, re.DOTALL)
    spans = [_[1] for _ in spans]
    tweets = []
    isp = []
    start = False
    for span in spans:
        if span and span[0]=='@':
            start = True
            isp = []
        if start:
            if 'span' in span:
                start = False
                tweets.append("".join(isp))
            else:
                if username not in span:
                    isp.append(span)
    return tweets
if __name__ == '__main__':
    text  =Path("/home/ntlpt59/MAIN/pyopengenai/tests/home_page_tweets.txt").read_text()
    tweets = get_tweets_from_text('skarandom',text)
    for x in tweets:
        print(x)
