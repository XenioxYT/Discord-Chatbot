# Helpful Bot README

Helpful Bot is a Discord bot that can answer questions and perform tasks, such as searching the web and scraping web pages. It utilizes OpenAI's GPT-3.5 Turbo model, Google API, and a back-end web scraper server to fetch relevant information and generate helpful responses.

## Features

- Answer questions and perform tasks for users
- Use Google API for web search and return results in a conversational format
- Scrape web pages and incorporate scraped data into responses
- Run as a Discord bot to respond to messages in real-time

## Dependencies

- [discord.py](https://pypi.org/project/discord.py/)
- [openai](https://pypi.org/project/openai/)
- [re](https://docs.python.org/3/library/re.html)
- [json](https://docs.python.org/3/library/json.html)
- [requests](https://docs.python.org/3/library/urllib.request.html)
- [datetime](https://docs.python.org/3/library/datetime.html)
- [pytz](https://pypi.org/project/pytz/)
- [os](https://docs.python.org/3/library/os.html)
- [google-api-python-client](https://pypi.org/project/google-api-python-client/)
- [tiktoken](https://pypi.org/project/tiktoken/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

## Installation

1. Install the required Python packages:

```bash
pip install discord.py openai re json requests datetime pytz os google-api-python-client tiktoken python-dotenv
```

2. [Create a new Discord bot](https://discordpy.readthedocs.io/en/latest/discord.html) and copy the bot token.

3. [Get an API key from OpenAI](https://beta.openai.com/signup/) and copy the key.

4. Obtain the [Google Search API Key](https://console.developers.google.com/apis) and Custom Search Engine ID (CSE ID). [Here's a guide](https://developers.google.com/custom-search/v1/introduction) on how to do that.

5. Create a `.env` file in the same folder as the bot script and add your bot token, OpenAI API key, Google API Key, and Google CSE ID:

```
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
```

6. Save the bot script as `helpful_bot.py` and run it:

```python
python helpful_bot.py
```

7. For web scraping capabilities, set up the [Web Scraper Server](https://github.com/XenioxYT/web-scraper-nodejs) and follow the instructions in its README.

## Usage

To trigger the bot, mention its name or an associated keyword in a Discord channel, followed by your message. The bot will then run its search, scrape data if necessary, and generate a helpful response based on the available information.
