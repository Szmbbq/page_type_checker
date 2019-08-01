from os import path
import urllib3
import chardet
from lxml import etree
import hybrid_webpage_checker
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def handle_err(url, desc, e):
    err_log = open(path.join(ROOT_DIR, "%s_err_log.txt" % FNAME), 'a')
    err_log.write("%s: %s\t%s\n" % (url, desc, e))
    err_log.close()



ROOT_DIR = path.dirname(path.abspath(__file__))
FNAME = "newscontroler.log.3"
INPUT_DIR = "inputs"
urls = [line.strip().split("\t")[0] for line in open(path.join(ROOT_DIR, INPUT_DIR, "%s.txt" % FNAME)).readlines()]
res = {}



http = urllib3.PoolManager(timeout=1.5)
for i, url in enumerate(urls[26000:]):
    try:
        req = http.request('GET', url)
    except urllib3.exceptions.MaxRetryError as max_retry_err:
        handle_err(url, "connection failed", max_retry_err)
    except urllib3.exceptions.SSLError as ssl_err:
        handle_err(url, "SSL error", ssl_err)
    except urllib3.exceptions.LocationParseError as loc_err:
        handle_err(url, "invalid url", loc_err)
    except UnicodeEncodeError as encode_err:
        handle_err(url, "request encode error", encode_err)
    else:
        try:
            encoding = chardet.detect(req.data)["encoding"]
        except:
            encoding = "utf-8"
        encoding = encoding if encoding else "utf-8"
        try:
            html_str = req.data.decode(encoding)
        except UnicodeDecodeError as decode_err:
            handle_err(url, "failed decoding html", decode_err)
        else:
            try:
                res[url] = hybrid_webpage_checker.check_page_type(html_str)
            except etree.ParserError as parser_err:
                handle_err(url, "failed parsing html", parser_err)
            except ValueError as val_err:
                handle_err(url, "broken page or decode issue", val_err)

    if (i + 1) % 100 == 0:
        with open("%s_predict.txt" % FNAME, 'a') as res_file:
            res_file.writelines(["%s: %s\n" % (k, v) for k, v in res.items()])
        res = {}