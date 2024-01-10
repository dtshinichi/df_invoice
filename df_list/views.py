from django.shortcuts import render
from django.http import HttpResponse
# scraper.pyからscrape関数をインポート
from .scraper import scrape

def index(request):
    if request.method == 'POST':
        writer_name = request.POST.get('writer_name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # スクレイピングを実行
        result = scrape(writer_name, start_date, end_date)

        # レスポンスを作成
        response = HttpResponse(content=result['csv_content'], content_type='text/csv', charset='utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="articles.csv"'
        response['Article-Count'] = str(result['article_count'])

        return response

    return render(request, 'index.html')