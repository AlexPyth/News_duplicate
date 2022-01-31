import requests
import re


class NewsDuplicate:
    def __init__(self):
        self.token_vk = ''    # Сервисный ключ приложения в Vk
        self.v_api = '5.131'  # Версия API Vk
        self.token_tg = ''    # API токен бота Telegram
        self.chat_ids = []    # ID чатов в Telegram, куда бот должен присылать новости
        self.groups_vk = []   # ID групп в VK, откуда бот берёт новости
        self.keywords = []    # Ключевые слова, которые должны присутствовать в записи
        try:
            open('old_news_id.txt')
        except IOError:
            open('old_news_id.txt', 'w')
    
    def get_records(self):
        records = []
        for group in self.groups_vk:
            params = {
                'access_token': self.token_vk,
                'v': self.v_api,
                'owner_id': group,
                'count': 10,
                'filter': 'owner'
            }
            response = requests.get('https://api.vk.com/method/wall.get', params=params)
            for record in response.json()['response']['items']:
                for key in self.keywords:
                    if ' '+key.lower()+' ' in record['text'].lower():
                        break
                else:
                    continue
                attachs = []
                for attach in record['attachments']:
                    if attach['type'] == 'video':
                        attachs.append({'type': 'video', 'url': f'https://vk.com/{attach["video"]["type"]}{attach["video"]["owner_id"]}_{attach["video"]["id"]}'})
                    if attach['type'] == 'photo':
                        attachs.append({'type': 'photo', 'url': attach['photo']['sizes'][-1]['url']})
                record_data = {
                    'id': str(record["id"]),
                    'record_url': f'https://vk.com/wall{record["owner_id"]}_{record["id"]}',
                    'text': record['text'],
                    'attachs': attachs
                }
                records.append(record_data)
        return records

    def video_download(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.116 YaBrowser/22.1.1.1544 Yowser/2.5 Safari/537.36'
        }
        r = requests.get(url, headers=headers)
        urls = re.findall(r'<BaseURL>([\w\W]*?)<\\/BaseURL>', r.text)[-1].replace('\\/', '/').replace('&amp;', '&')
        r = requests.get(urls, headers=headers)
        open('video.mp4', 'wb').write(r.content)

    def photo_download(self, url):
        r = requests.get(url)
        open('photo.jpg', 'wb').write(r.content)

    def exam_to_new(self, records):
        news = []
        id_news = open('old_news_id.txt', 'r').read().split(',')
        for record in records:
            for i in id_news:
                if i == record['id']:
                    break
            else:
                news.append(record)
        return news

    def send_tg(self, news):
        for new in news:
            caption = new['text']+'\n\n'+'Источник: '+new['record_url']
            if new['attachs']:
                for attach in new['attachs']:
                    if attach['type'] == 'video':
                        self.video_download(attach['url'])
                        for chat_id in self.chat_ids:
                            requests.post(f'https://api.telegram.org/bot{self.token_tg}/sendVideo', data={'chat_id': chat_id, 'caption': caption}, files={'video': open("video.mp4", "rb")})
                        break
                else:
                    self.photo_download(new['attachs'][0]['url'])
                    for chat_id in self.chat_ids:
                        requests.post(f'https://api.telegram.org/bot{self.token_tg}/sendPhoto', data={'chat_id': chat_id, 'caption': caption}, files={'photo': open("photo.jpg", "rb")})
            else:
                for chat_id in self.chat_ids:
                    requests.post(f'https://api.telegram.org/bot{self.token_tg}/sendMessage', data={'chat_id': chat_id, 'text': caption})
            open('old_news_id.txt', 'a').write(','+new['id'])
            

    def run(self):
        records = self.get_records()
        news = self.exam_to_new(records)
        self.send_tg(news)


if __name__ == '__main__':
    bot = NewsDuplicate()
    bot.run()
