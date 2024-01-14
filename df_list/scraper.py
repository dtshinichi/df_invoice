import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import configparser
import time

# 設定ファイルの読み込み
config = configparser.ConfigParser()
config.read('../settings.ini')

# メンテナンスモードの確認
maintenance_mode = config.getboolean('DEFAULT', 'MaintenanceMode')
if maintenance_mode:
    print('現在メンテナンス中です')
    exit()

# アクセス間隔、ページ制限、頻度制限の取得
access_interval = config.getfloat('DEFAULT', 'AccessInterval') / 1000.0  # msからsに変換
page_limit = config.getint('DEFAULT', 'PageLimit')
rate_limit = config.getint('DEFAULT', 'RateLimit')

def scrape(writer_name, start_date_input, end_date_input):
    # 日付をdatetimeオブジェクトに変換
    start_date = datetime.strptime(start_date_input, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_input, '%Y-%m-%d')

    # ログの設定
    logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s - %(message)s', encoding='utf-8-sig')

    page = 1
    articles = []

    found_out_of_range_article = False

    while True:
        # ページ制限を超えたらループを終了
        if page > page_limit:
            print(f"ページ制限に到達しました。スクリプトを終了します: {page_limit}ページ")
            logging.info(f"ページ制限に到達しました。スクリプトを終了します: {page_limit}ページ")
            break

        url = f"https://news.denfaminicogamer.jp/tag/{writer_name}"
        if page > 1:
            url += f"/page/{page}"

        try:
            response = requests.get(url, timeout=10)  # 10秒のタイムアウトを設定
            time.sleep(access_interval)  # アクセス間隔を設定
        except requests.exceptions.Timeout:
            print(f'Timeout occurred while accessing: {url}')
            logging.error(f'Timeout occurred while accessing: {url}')
            return  # タイムアウトが発生した場合、関数を終了

        if response.status_code != 200:
            if page == 1:
                print(f'指定されたライター名は存在しませんでした: {writer_name}')
                logging.info(f'指定されたライター名は存在しませんでした: {writer_name}')
                return
            else:
                print(f'指定されたページは存在しません: ページ {page}')
                logging.info(f'指定されたページは存在しません: ページ {page}')
                break  # 増えるページがない場合は終了

        logging.info(f'Scraping page {page}')

        soup = BeautifulSoup(response.text, 'html.parser')
        article_sections = soup.find_all('section', class_='articleContent row')

        #日付、タイトル、URLの抽出開始
        for section in article_sections:
            ul = section.find('ul', class_='gridList')
            for li in ul.find_all('li'):
                a = li.find('a', class_='flxBox')
                title = a.find('span', class_='title').text
                datetime_str = a.find('time')['datetime']
                article_date = datetime.strptime(datetime_str, '%Y-%m-%d')
                url = a['href']

                # 日付が指定された期間外にあるかどうかを確認
                if article_date < start_date:
                    print("指定期間の探索を完了しました。スクレイピングを終了します。")
                    logging.info("指定期間の探索を完了しました。スクレイピングを終了します。")
                    found_out_of_range_article = True  # 期間外の記事を見つけたことをマークします。
                    break  # 指定された期間外の記事を見つけた場合は終了

                # 日付が指定された期間内にあるかどうかを確認
                if start_date <= article_date <= end_date:
                    formatted_date = '/'.join(datetime_str.split('-'))
                    articles.append((formatted_date, title, url))  # URLを追加

            if found_out_of_range_article:
                break  # 期間外の記事を見つけた場合、外側のforループも終了します。

        if found_out_of_range_article:
            break  # 期間外の記事を見つけた場合、whileループも終了します。

        page += 1

    # CSVデータを文字列として生成
    csv_content = "Date,Title,URL\n"
    for article in articles:
        csv_content += f'"{article[0]}","{article[1]}","{article[2]}"\n'  # カンマや改行を含むデータに対応

    # 結果を文字列として保存
    result_str = f'ライター名：{writer_name}\n'
    result_str += f'期間：{start_date_input}から{end_date_input}\n'
    result_str += f'記事数：{len(articles)}\n'

    # 結果を表示
    print(result_str)
    logging.info(f'ライター名：{writer_name}、期間：{start_date_input}から{end_date_input}、記事数：{len(articles)}')

    result = {
        'article_count': len(articles),
        'csv_content': csv_content,
    }
    return result

    #return csv_content, result_str