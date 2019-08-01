"""
This module provides methods for checking webpage type.
@ author: Ziming Sheng
@ date: 2019-07-25
"""


import collections
import re
from urllib import parse
from lxml import etree
from lxml.html import clean, defs
import numpy
import pyximport
pyximport.install(pyimport=True)
from cyGaussian import gaussian


def collect_text_and_a_tag(root):
    """
    Collect node index, path and depth information of text tags and a tags
    :param root: lxml etree root object
    :return: A dict maps tag path to the corresponding tag info. For instance:
            {"html/div/div/p": [(34, "Best places to visit...", 4)],
             "html/div/div/div/p": [(40, "What's your problem?", 5)]}
            {"html/div/h/a": [(48, "back to top", "html/div/h/a")],
             "html/div/div/li/a": [(59, "python is fun", "html/div/div/li/a")]}
    """
    # initialize dict to store info of link nodes and text nodes
    # initialize visit index and depth to 0
    a_path = collections.defaultdict(list)
    text_path = collections.defaultdict(list)
    d = index = 0
    # lxml built-in DFS traversal
    context = etree.iterwalk(root, events=("start", "end"))
    path = ""
    for action, elem in context:
        # upon visit a new node:
        # 1. update path, depth
        # 2. check tag style, ignore subtree if node is invisible
        # 3. ignore nodes belong to "foot" or "footer"
        # 4. collect info of a tags (excess space removed)
        # 5. collect info of node text (direct text within a node, not including text from its children)
        if action == 'start':
            path += "/%s" % elem.tag
            style = elem.get("style")
            tag_class = elem.get("class")
            if style and style.strip().replace(" ", "") == "display:none;":
                context.skip_subtree()
            elif tag_class and tag_class.strip().replace(" ", "") in {"foot", "footer"}:
                context.skip_subtree()
            elif elem.tag == 'a':
                context.skip_subtree()
                tag_text = elem.xpath("normalize-space()")
                a_path[path].append((index, tag_text, path))
            elif elem.xpath("text()"):
                tag_text = re.sub("\s{2,}", "", "".join(elem.xpath("text()")))
                if tag_text and not re.search('^[0-9—»›\s!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~·]*$', tag_text):
                    text_path[path].append((index, tag_text, d))
            d += 1
            index += 1
        else:
            path = path.rsplit("/", 1)[0]
            d -= 1
    return text_path, a_path


def get_text_text_score(text_path):
    """
    Compute relational score between text nodes.
    Text nodes share same tag path forms a group. Within each
    group, the score each text node contributes is the weighted
    text length sum between that node and all the other nodes
    in this group. Total score for each group sums over all
    individual contributions. Finally the text-text score of
    the whole page is the weighted sum of group scores respect
    to all different paths.
    Note: the self relational score is handled separately
    :param text_path: a dict maps tag path with list of tag information (index, text, depth)
    :return: text-text score of the entire document
    """
    score = 0
    # compute pure text length on webpage
    text_nodes = {node for same_path_tags in text_path.values() for node in same_path_tags}
    text_total_len = sum([len(node[1]) for node in text_nodes])
    # compute score for each group
    for path in text_path:
        text_path_score = 0
        std = numpy.std([node[0] for node in text_path[path]])
        # contribution of each text node
        for j, (index, text, depth) in enumerate(text_path[path]):
            self_w = len(text)/text_total_len
            text_path_score += len(text)*self_w + sum([gaussian(std, node[0], index)*len(node[1])
                                                       for node in text_path[path][:j]+text_path[path][j+1:]])
        d = path.count('/')
        depth_w = d/(1+d)
        score += depth_w * text_path_score
    return score


def get_link_link_score(a_path):
    """
    Compute relational score between link nodes.
    Link nodes share same tag path forms a group. Within each
    group, the score each link node contributes is the weighted
    link text length sum between that node and all the other nodes
    in this group. Total score for each group sums over all
    individual contributions. Finally the text-text score of
    the whole page is the weighted sum of group scores respect
    to all different paths.
    :param a_path: a dict maps tag path with list of tag information (index, text, path)
    :return: link-link score of the entire document
    """
    if not a_path: return 0
    score = 0
    # compute score for each group
    for path in a_path:
        link_path_score = 0
        std = numpy.std([node[0] for node in a_path[path]])
        # contribution of each link node
        for index, text, path in a_path[path]:
            link_path_score += sum([gaussian(std, node[0], index)*len(node[1])
                                    for node in a_path[path]])
        d = path.count('/')
        depth_w = d/(1+d)
        score += depth_w * link_path_score
    return score


def get_text_link_score(a_path, text_path):
    """
    Compute relational score between text nodes and neighboring a tags.
    The purpose of computing this is to somehow capture "framework" links.
    (e.g. copyrights, menu bars) These links may sometimes contribute a lot
    to the link-link score, though they actually are not indicators of a list
    page.
    For each text node, find the nearest link node's path. (If there is a tie,
    return the one has longer link text) links matches this path are claimed
    as neighboring link tags. Compute weighted link text length sum between
    that node and all other neighboring nodes. Finally the text-link score of
    the whole page is the weighted sum of all individual text-link scores
    :param a_path: A dict maps tag path to the corresponding link tag info.
    :param text_path: A dict maps tag path to the corresponding text tag info.
    :return: text-link score of the entire document
    """
    if not a_path: return 0
    text_nodes = {node for same_path_tags in text_path.values() for node in same_path_tags}
    a_nodes = {node for same_path_tags in a_path.values() for node in same_path_tags}
    score = 0
    for text_node in text_nodes:
        text_index = text_node[0]
        a_tag_path = min(a_nodes, key=lambda x:abs(x[0]-text_index+(1/len(x[1]) if len(x[1]) != 0 else 10)))[2]
        std = numpy.std([node[0] for node in a_path[a_tag_path]])
        d = a_tag_path.count('/')
        depth_w = d/(1+d)
        score += depth_w * sum([gaussian(std, node[0], text_index)*len(node[1])
                                for node in a_path[a_tag_path]])
    return score


def predict(text_text_score, link_link_score, text_link_score, url):
    """
    Given text-text, link-link and text-link scores, determine page type.
    If hard to tell (text-text falls in between link-link and text-link), compute the difference
    between link-link score and text-link score. Compare text-text score with it. If text-text
    score is greater, then claim the page type as list page.
    Otherwise, greater text-text score indicates content page and greater average(link-link, text-link)
    indicates list page.
    If auxiliary url presents, parse and check path segment. Add bonus score to link-link score if
    the path segments matches typical index page paths.
    :param text_text_score: text-text score of the document
    :param link_link_score: link-link score of the document
    :param text_link_score: text-link score of the document
    :param url: auxiliary urls helps to distinguish list page
    :return: web page type, either "list page" or "content page"
    """
    path = parse.urlparse(url).path
    if path in set(["/", "/home/"]):
        link_link_score += 400
    if text_link_score <= text_text_score <= link_link_score:
        return "content page" if link_link_score - text_link_score < text_text_score else "list page"
    else:
        s = (link_link_score + text_link_score) / 2
        return "list page" if s > text_text_score else "content page"


def check_page_type(html_str, url=""):
    parser = etree.HTMLParser(remove_blank_text=True)
    # cleaner configuration
    cleaner = clean.Cleaner(javascript=True,
                            style=True,
                            safe_attrs=defs.safe_attrs | set(["style"]),
                            scripts=True,
                            comments=True,
                            meta=True,
                            remove_unknown_tags=True,
                            remove_tags=["font", "strong", "b", "br", "em"],
                            kill_tags=["footer"])
    try:
        cleaned_html = cleaner.clean_html(html_str)
    except etree.ParserError as parser_err:
        raise parser_err
    except ValueError as val_err:
        raise val_err
    root = etree.fromstring(cleaned_html, parser)
    text_path, a_path = collect_text_and_a_tag(root)
    text_s = get_text_text_score(text_path)
    a, b = get_text_link_score(a_path, text_path), get_link_link_score(a_path)
    page_type = predict(text_s, b, a, url)
    return page_type