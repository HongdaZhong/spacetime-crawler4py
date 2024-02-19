import re
from urllib.parse import urlparse, urljoin, urlunparse

stop_words = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
]

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def getSubdomain(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    subdomain = hostname.split(".")[0]
    return hostname.endswith(".ics.uci.edu"), subdomain  #(parsed_url.scheme + "://" + hostname)

def getUnique(url):
    parsed_url = urlparse(url)
    cleaned_url = urlunparse(parsed_url._replace(fragment=""))
    return cleaned_url


def getWordsDict(url, resp):
    temp_dict = dict()
    if resp.status == 200:
        contents = resp.raw_response.content.decode('utf-8', errors="ignore")
        # Remove scripts and styles
        contents = re.sub('<script[^<]*?>.*?</script>', ' ', contents, flags=re.DOTALL)
        contents = re.sub('<style[^<]*?>.*?</style>', ' ', contents, flags=re.DOTALL)
        # Remove HTML tags
        contents = re.sub('<[^<]+?>', ' ', contents)
        # Replace HTML entities with a space
        contents = re.sub('&[a-zA-Z]+;', ' ', contents)
        # Remove all non-word characters and normalize whitespaces
        contents = re.sub(r'\W+', ' ', contents)
        # Convert to lowercase to count all words uniformly
        contents = contents.lower()
        # Normalize multiple whitespaces to a single space and strip leading/trailing whitespace
        text_only = re.sub('\s+', ' ', contents).strip()
        # Count words
        words = text_only.split(' ')
        for word in words:
            if word:  # Check if word is not empty
                if word not in stop_words and word.isdigit() == False:
                    if len(word) > 1:
                        temp_dict[word] = temp_dict.get(word, 0) + 1

    return temp_dict

    
def amountWords(url, resp):
    word_count = 0
    if resp.status == 200:
        contents = resp.raw_response.content.decode('utf-8', errors="ignore")
    
        # Remove scripts and styles
        contents = re.sub('<script[^<]*?>.*?</script>', ' ', contents, flags=re.DOTALL)
        contents = re.sub('<style[^<]*?>.*?</style>', ' ', contents, flags=re.DOTALL)
        # Introduce space around tags to prevent word concatenation
        contents = re.sub('<[^<]+?>', ' ', contents)
        # Replace HTML entities with a space
        contents = re.sub('&[a-zA-Z]+;', ' ', contents)
        # Normalize multiple whitespaces to a single space and strip leading/trailing whitespace
        text_only = re.sub('\s+', ' ', contents).strip()
        # Count words
        words = text_only.split(' ')
        word_count = len(words) if words[0] != '' else 0  # Adjust for case where result is empty string

    return word_count

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    links = []
    if resp.status == 200:
        try:
            contents = resp.raw_response.content.decode('utf-8', errors="ignore")
            # contents = resp.raw_response.content.decode('utf-8')
            link_pattern = re.compile(r'href=["\'](.*?)["\']')
            links = link_pattern.findall(contents)
            links = [urljoin(resp.url, link) for link in links]
        except UnicodeDecodeError as e:
            print(end="")
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check wether it is correct domain name
        hostname = str(parsed.hostname)
        indi = 0
        valid_domains = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]
        for x in valid_domains:
            if hostname.endswith(x):
                indi = 1
        if indi == 0:
            return False

        if re.search(r"\b(?:index|main)\b", parsed.path, re.IGNORECASE):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
