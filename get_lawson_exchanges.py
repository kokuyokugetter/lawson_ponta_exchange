import requests, bs4
import datetime

url = 'http://www.lawson.co.jp'
today = datetime.datetime.today()

# redirect
before_redirect_info = requests.get(url + '/ponta/tsukau/otameshi/')
bs4Obj_br = bs4.BeautifulSoup(before_redirect_info.text, 'lxml')
meta_refresh = bs4Obj_br.select('meta')[0]
meta_cont = meta_refresh.attrs["content"]
redirect_url = meta_cont.split("URL=")[1]

# 現在の引き換え可能商品取得 + 利率追加
info_ar = requests.get(url + redirect_url)
info_ar.encoding = info_ar.apparent_encoding # ISO-8859-1が帰ってくる不具合をケア
bs4Obj_ar = bs4.BeautifulSoup(info_ar.text, 'lxml')
item_list_w_tag = bs4Obj_ar.find_all(class_="col-2 heightLineParent")[0].select("li")
item_list_w_tag_required = []
rate_list = []
for item_w_tag in item_list_w_tag:
    if not "円引券" in str(item_w_tag):
        date = item_w_tag.select("dd")[0].text
        date_parsed = datetime.datetime.strptime(date, '%Y.%m.%d')
        if today > date_parsed:
            # 利率計算
            txt = item_w_tag.find_all(class_="smalltxt")[0].text
            price_str = ''.join(c for c in txt if c.isdigit())
            price_int = int(price_str)
            point_str = item_w_tag.select("dd")[1].text[:-1]
            point_int = int(point_str)
            rate = price_int / point_int
            rate_list.append(rate)
            # 利率タグ追加
            bs4_tag_obj = item_w_tag.select("dl")[0]
            tag = bs4Obj_ar.new_tag("dt")
            tag.string = "利率"
            bs4_tag_obj.append(tag)
            tag2 = bs4Obj_ar.new_tag("dd")
            tag2.string = "{0:.4f}".format(rate)
            bs4_tag_obj.append(tag2)
            # 画像のPATHを絶対PATHに
            img = item_w_tag.select("img")[0]
            img.attrs["src"] = url + img.attrs["src"]
            item_list_w_tag_required.append(item_w_tag)

# 利率順に並び替え
zipped = zip(rate_list, item_list_w_tag_required)
zipped_sorted = sorted(zipped, key=lambda x:x[0], reverse=True)
rate_list, item_list_w_tag_sorted = zip(*zipped_sorted)
item_list_w_tag_sorted = list(item_list_w_tag_sorted)

# とりあえずのアレ
print("利率   商品名")
for item_w_tag in item_list_w_tag_sorted:
    print(item_w_tag.select("dd")[-1].text, item_w_tag.select("p")[0].text)

# htmlにしてみる
file = open('test.html', 'w', encoding="utf-8")
html_head = """
<html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>ポンタポイントローソン引き換えポイント効率順</title>
<style>

body {
    background: #f0f7ff;
}
ul.bluetable {
    display: table;
    width:95%;
}
ul.bluetable > li:nth-child(2n+1) {
    clear: both;
}
ul.bluetable > li {
    display: table-cell;
    float: left;
    width: 43%;
    height: 35em;
    font-size: 14pt;
    padding: 0.5em 0.5em;
    margin: 0.5em 0.5em;
    border: double 5px #4ec4d3;
}

</style>
<body>
<ul class="bluetable">
"""
file.write(html_head)
for item_w_tag in item_list_w_tag_sorted:
    file.write(str(item_w_tag))
file.write("</ul></body></html>")
file.close()
