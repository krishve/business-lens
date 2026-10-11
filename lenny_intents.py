"""Small, explicit phrase matcher. No language model, code execution or guessing."""
from dataclasses import dataclass
import re
from lenny import QUESTIONS


def normalize(text):
    return re.sub(r'[^a-z0-9%]+', ' ', text.lower()).strip()


@dataclass
class Request:
    question: str | None = None
    year: int | None = None
    customer_id: str | None = None
    product_area: str | None = None
    message: str | None = None


def match_question(text, data=None, year=None, customer_id=None, product_area=None):
    """Match only supported topics and explicit years/names from the loaded data."""
    query = normalize(text)
    result = Request(year=year, customer_id=customer_id, product_area=product_area)
    if not query:
        result.message = 'Type a question or choose one of the suggestions above.'
        return result
    if query in ('help', 'explain this page', 'what does this page show', 'help me understand this page'):
        result.question = 'page'
        return result
    if re.search(r'\b(forecast|predict|prediction|tomorrow|next year|next quarter)\b', query):
        result.message = 'I can explain recorded results, but I cannot predict future performance. Try “How did profit change from last year?”'
        return result
    if '%' in query:
        result.message = 'To change a percentage assumption, use the controls on FAQ opportunities. I will use those settings when you ask about FAQ savings.'
        return result
    explicit_years = set(int(y) for y in re.findall(r'\b20\d{2}\b', query))
    if len(explicit_years) > 1:
        result.message = 'Please ask about one year at a time. For a year-over-year comparison, ask “How did profit change in 2025?” and I will compare with 2024.'
        return result
    if explicit_years:
        result.year = explicit_years.pop()
    if 'last year' in query and not re.search(r'profit.*change|change.*profit', query):
        if re.search(r'\b20\d{2}\b', query):
            result.message = 'Please use either a named year or “last year” so the time period is clear.'
            return result
        if year is not None:
            result.year = year - 1
    named_customer = False
    if data is not None:
        if result.year not in set(data['periods'].year):
            result.message = 'That year is not loaded. Available years: ' + ', '.join(map(str, sorted(data['periods'].year))) + '.'
            return result
        matches = []
        for row in data['customers'].itertuples():
            name = normalize(row.customer_name)
            aliases = [name] + ([name.split()[0]] if len(name.split()[0]) >= 4 else [])
            if any(re.search(r'\b' + re.escape(alias) + r'\b', query) for alias in aliases):
                matches.append(row.customer_id)
        if len(matches) > 1:
            result.message = 'Please ask about one customer at a time, or ask for the customer ranking.'
            return result
        if matches:
            named_customer = True
            result.customer_id = matches[0]
        areas = [a for a in data['topics'].product_area.unique() if re.search(r'\b' + re.escape(normalize(a)) + r'\b', query)]
        if len(areas) > 1:
            result.message = 'Please name one product area, or ask about support time across all areas.'
            return result
        if areas:
            result.product_area = areas[0]
    if 'all customers' in query:
        result.customer_id = None
    if 'all areas' in query:
        result.product_area = None
    exact = {normalize(label): key for key, label in QUESTIONS.items()}
    if query in exact:
        result.question = exact[query]
        return result
    intents = set()
    patterns = {
        'top': r'\b(most profitable|highest contribution|best customers|top customers|contribute the most)\b',
        'bottom': r'\b(least profitable|lowest contribution|worst customers|bottom customers|contribute the least)\b',
        'losses': r'\b(loss making|making a loss|losing money|customers with losses|unprofitable)\b',
        'support': r'\b(support time|support hours|support effort|handling time|handling hours|time on support)\b',
        'defects': r'\b(defects|bugs|backlog)\b',
        'projects': r'\b(projects|project hours|over budget|hours budget|consulting budget)\b',
        'faq': r'\b(faq|automation|repeated questions|self service)\b',
        'focus': r'\b(focus|priorities|improvement|improve|attention)\b',
        'revenue': r'\b(revenue|income|sales)\b',
        'profit': r'\b(profit|profitability|profitable|margin)\b',
    }
    for intent, pattern in patterns.items():
        if re.search(pattern, query):
            intents.add(intent)
    if intents & {'top', 'bottom', 'losses'}:
        intents.discard('profit')
    refers_to_customer = named_customer or (customer_id is not None and re.search(r'\b(this customer|selected customer)\b', query))
    if refers_to_customer and (not intents or intents <= {'profit', 'losses', 'revenue'}):
        result.question = 'customer'
    elif len(intents) == 1:
        result.question = intents.pop()
    elif len(intents) > 1:
        result.message = 'That covers more than one topic. Please ask about one at a time, such as customer profit, support hours or revenue.'
    else:
        result.message = 'I could not match that to a supported question. Try “Which customers are making a loss?”, “Show support hours” or “Explain this page”.'
    if result.question in ('profit', 'revenue') and not named_customer and re.search(r'\b(for|of) [a-z]', query):
        result.question = None
        result.message = 'If you mean a customer, use a customer name from the data or select one on Customers. For the whole business, try “How did operating profit change?”'
    return result
