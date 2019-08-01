# Web Page Type Checker

This is a python module that can help determine the web page type. This module biclassifies a given web page as either list page or content page.
The input is the Unicode HTML string while the output is the page type.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
lxml
numpy
pyximport
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

### Example Usage

Here is an example usage:

```python
import urllib3
from hybrid_webpage_checker import check_page_type
url = "http://www.globaltimes.cn/"
http = urllib3.PoolManager()
req = http.request('GET', url)
html_str = req.data.decode("utf-8")
print(check_page_type(html_str))    # html_str is the Unicode string of the page content
```

## Authors

* **Ziming Sheng** - *Initial work*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
