import arxiv
import requests
import json
import os


def lambda_handler(event, context):
    token = get_token()
    new_papers = get_new_arxiv_papers()
    for paper in new_papers:
        post_paper_to_slack(paper, token, translate=False)


def get_token():
    if os.path.exists('TOKEN.json'):
        with open('TOKEN.json') as f:
            token = json.load(f)
            return token
    else:
        token = {'GOOGLE_API_KEY': os.environ['GOOGLE_API_KEY'],
                 'SLACK_BOT_USER_OATH_ACCESS_TOKEN': os.environ['SLACK_BOT_USER_OATH_ACCESS_TOKEN'],
                 'SLACK_OATH_ACCESS_TOKEN': os.environ['SLACK_OATH_ACCESS_TOKEN']}
        return token


def get_new_arxiv_papers(search_query="cs.CV", max_results=20):
    arxiv_res = arxiv.query(search_query=search_query,
                            max_results=max_results, sort_by="submittedDate")

    with open('last_arxiv_ids.txt', 'r') as f:
        last_arxiv_ids = f.read()
        last_arxiv_ids = last_arxiv_ids.split('\n')

    news_paper_list = []
    for res in arxiv_res:
        if res['id'] not in last_arxiv_ids:
            news_paper_list.append(res)

    arxiv_ids = [x['id'] for x in arxiv_res]
    with open('last_arxiv_ids.txt', 'w') as f:
        f.write('\n'.join(arxiv_ids))

    return news_paper_list


def translate(text, token):
    translate_url = "https://translation.googleapis.com/language/translate/v2?key=" + \
        token['GOOGLE_API_KEY']
    headers = {"Content-Type": "application/json"}
    content = {'q': text,
               'source': 'en',
               'target': 'ja',
               'format': 'text'}
    response = requests.post(
        translate_url, data=json.dumps(content), headers=headers)
    if response.ok:
        translated_data = json.loads(response.text)
        translated_text = translated_data['data']['translations'][0]['translatedText']
        return translated_text
    else:
        return False


def post_paper_to_slack(paper, token, channel_id='CHFGJ2PJ6', translate=True):
    post_message_url = 'https://slack.com/api/chat.postMessage'
    abstract = paper['summary']
    if translate:
        abstract = translate(paper['summary'].replace('\n', ' '), token)

    post_json = {
        'token': token['SLACK_OATH_ACCESS_TOKEN'],
        'text': '*' + paper['title'].replace('\n', '') + '*' + '\n' + paper['arxiv_url'],
        'channel': channel_id,
        'username': 'arXiv-crawling',
        'icon_url': 'https://i.imgur.com/ldRH2jt.png',
        'attachments': str([
            {
                "color": "#36a64f",
                "fields": [
                    {
                        "title": "Abstract",
                        "value": abstract,
                    }
                ]
            }])
    }
    requests.post(post_message_url, data=post_json)


