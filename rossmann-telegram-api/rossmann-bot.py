import os
import requests
import json
import pandas as pd
from flask import Flask, request, Response

# constants
TOKEN = '1428225644:AAFOUWJ2gj0sWY0_pBbnTwgY7U_xbAx8VQ4'

# info about the Bot
# https://api.telegram.org/bot1428225644:AAFOUWJ2gj0sWY0_pBbnTwgY7U_xbAx8VQ4/getMe
#
# getUpdates
# https://api.telegram.org/bot1428225644:AAFOUWJ2gj0sWY0_pBbnTwgY7U_xbAx8VQ4/getUpdates
#
# set Webhook
# https://api.telegram.org/bot1428225644:AAFOUWJ2gj0sWY0_pBbnTwgY7U_xbAx8VQ4/setWebhook?url=https://bot-telegram-rossmann.herokuapp.com
#
# send message
# https://api.telegram.org/bot1428225644:AAFOUWJ2gj0sWY0_pBbnTwgY7U_xbAx8VQ4/sendMessage?chat_id=1122694504&text=Hi Emidio. I am great. Thanks!

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}'
    r = requests.post(url, json={'text': text})
    print(f'Status code {r.status_code}')

    return None

def loading_dataset(store_id):
    # loading test dataset
    df10 = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')

    # merge test and store datasets
    df_test = pd.merge(df10, df_store_raw, how='left', on='Store')

    # choose store for prediction
    df_test = df_test[df_test['Store'] == store_id]

    if not df_test.empty:

        # remove days where stores haven't opened
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]

        # remove index
        df_test = df_test.drop('Id', axis=1)

        # converting dataframe into json
        data = json.dumps(df_test.to_dict(orient='records'))
    else:
        data = 'error'

    return data


def predict(data):
    # API Call
    url = 'https://rossmann-model-predict.herokuapp.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, data=data, headers=header)
    print('Status Code {}'.format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    return d1


def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']

    store_id = store_id.replace('/', '')

    try:
        store_id = int(store_id)
    except ValueError:
        store_id = 'error'

    return chat_id, store_id


# API initialise
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, store_id = parse_message(message)

        if store_id != 'error':
            data = loading_dataset(store_id)
            if data != 'error':
                d1 = predict(data)
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()

                msg = f">> Store number {d2['store'].values[0]} will sell €{d2['prediction'].values[0]:,.2f} " \
                      f"in the next 6 weeks."

                send_message(chat_id, msg)
                return Response('Ok', status=200)

            else:
                send_message(chat_id, 'Store ID not available.')
                return Response('Ok', status=200)

        else:
            send_message(chat_id, 'Invalid store.')
            return Response('Ok', status=200)

    else:
        return '<h1> Rossmann Telegram BOT </h1>'

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)
