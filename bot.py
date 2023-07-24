import discord
import openai
import re
import json
import requests
import datetime
import pytz
import os
from googleapiclient.discovery import build
import tiktoken
from dotenv import load_dotenv


# get from environment variables
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")

token_limit = 16000
max_response_tokens = 750

# Load an encoding for the specific model
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

def count_tokens(text):
    return len(encoding.encode(text))

def count_tokens_in_conversation(conversation):
    return sum(count_tokens(m["content"]) for m in conversation)

def would_exceed_limit(conversation, new_message, limit):
    return count_tokens_in_conversation(conversation) + count_tokens(new_message) > limit


def get_date_time(timezone="UTC"):
    now = datetime.datetime.now(pytz.timezone(timezone))
    return now.strftime("%Y-%m-%d %H:%M:%S")


def google_search(search_term, api_key, cse_id, num_results=5, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, gl='uk', **kwargs).execute()
    search_results = [{"title": item["title"], "link": item["link"], "snippet": item["snippet"]} for item in res['items'][:num_results]]
    search_results_str = json.dumps(search_results)
    print("(debug) Used Google search. Number of search results: ", num_results, "with search term: ", search_term)
    return search_results_str

def scrape_web_page(url):
    # Send the URL to the Node.js server and get the scraped data
    response = requests.post('http://localhost:3000/scrape', json = {'url': url})
    print("(debug) Scraped web page. response: ", response.status_code)

    scraped_data = response.json()

    # Limit the length of the scraped text
    scraped_text = ("this is the data from the webpage, please use this in your response and say you accesed the webpage:" +scraped_data['data'][0:1750])
    return scraped_text

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)
        self.conversations = {}
        self.embed_messages = {}

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.channel.id not in self.conversations:
            self.conversations[message.channel.id] = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful bot that can answer questions and perform tasks, such as searching the web and scraping web pages. "
                    )
                },
            ]
        


        content = f"{message.author.name}: {message.content}"

        if would_exceed_limit(self.conversations[message.channel.id], content, token_limit):
            print("This message would exceed the token limit and won't be added to the conversation.")
        else:
            self.conversations[message.channel.id].append({"role": "user", "content": content.strip()})

        while count_tokens_in_conversation(self.conversations[message.channel.id]) > token_limit:
            self.conversations[message.channel.id].pop(0)

        functions = [
            { #google search
                "name": "google_search",
                "description": "Perform a Google search. Interpret the results given by the API and return them in a conversational format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {"type": "string"},
                        "num_results": {"type": "integer"},
                    },
                    "required": ["search_term", "num_results"],
                },
            },
            { #scrape web page
                "name": "scrape_web_page",
                "description": "Scrape the webpage data given a URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                    },
                    "required": ["url"],
                },
            },
            { # get date and time
                "name": "get_date_time",
                "description": "Get the current date and time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {"type": "string"},
                    },
                },
            },
        ]
        if 'byte' in message.content.lower():  # the bot's name is mentioned
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=self.conversations[message.channel.id],
                temperature=1,
                functions=functions,
                max_tokens=max_response_tokens
            )

            response_message = response['choices'][0]['message']

            # Check if a function call was made
            if response_message.get("function_call"):
                function_name = response_message["function_call"]["name"]
                function_args = json.loads(response_message["function_call"]["arguments"], strict=False)

                if function_name == "google_search":
                    function_response = google_search(
                        search_term=function_args.get("search_term"),
                        api_key=google_api_key,
                        cse_id=google_cse_id,
                    )
                    # print(function_response)

                    self.conversations[message.channel.id].append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": function_response,
                        }
                    )

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo-16k",
                        messages=self.conversations[message.channel.id],
                        temperature=1,
                        max_tokens=max_response_tokens
                    )

                    response_content = response['choices'][0]['message']['content']
                    response_content = re.sub(r"^Byte: ", "", response_content)
                    print(f"Response content before chunking: {response_content}")
                elif function_name == "scrape_web_page":
                
                    function_response = scrape_web_page(function_args.get("url"))
                    # print(function_response)

                    self.conversations[message.channel.id].append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": function_response,
                        }
                    )

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo-16k",
                        messages=self.conversations[message.channel.id],
                        temperature=1,
                        max_tokens=max_response_tokens
                    )
                    response_content = response['choices'][0]['message']['content']
                    response_content = re.sub(r"^Byte: ", "", response_content)
                elif function_name == "get_date_time":
                    function_response = get_date_time()
                    

                    self.conversations[message.channel.id].append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": function_response,
                        }
                    )

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo-16k",
                        messages=self.conversations[message.channel.id],
                        temperature=1,
                        max_tokens=max_response_tokens
                    )

                    response_content = response['choices'][0]['message']['content']
                    response_content = re.sub(r"^Byte: ", "", response_content)

            else:
                # No function call was made, so we use the message content
                response_content = response_message['content'] if 'content' in response_message else str(response_message)

            inline_link_regex = r'\[(.*?)\]\((.*?)\)'
            inline_links = re.findall(inline_link_regex, response_content)
            print(f"Inline links found: {inline_links}")

            for i, (text, url) in enumerate(inline_links, start=1):
                response_content = response_content.replace(f'[{text}]({url})', f'{text}[{i}]')

            embed_description = ""
            if inline_links:
                for i, (text, url) in enumerate(inline_links, start=1):
                    embed_description += f'Source {i}: {url}\n'

            chunks = [response_content[i:i+2000] for i in range(0, len(response_content), 2000)]



            if embed_description:
                for chunk in chunks:
                    response_message = await message.channel.send(chunk)

                sources_message = await message.channel.send("👆 I've found {} source(s) for the information provided. Click the 📚 reaction to view the sources, and click again to hide them.".format(len(inline_links)))

                self.embed_messages[response_message.id] = embed_description
                await response_message.add_reaction('📚')
            else:
                for chunk in chunks:
                    await message.channel.send(chunk)

    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return

        if reaction.message.id in self.embed_messages and str(reaction.emoji) == '📚':
            if reaction.count > 1:  # More than one reaction, so show sources
                embed_description = self.embed_messages[reaction.message.id]
                embed = discord.Embed(title="Sources", description=embed_description, color=0xFFA500)
                await reaction.message.edit(embed=embed)

    async def on_reaction_remove(self, reaction, user):
        if user == self.user:
            return

        if reaction.message.id in self.embed_messages and str(reaction.emoji) == '📚':
            if reaction.count <= 1:  # One or no reactions left, so hide sources
                await reaction.message.edit(embed=None)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True
client = MyClient(intents=intents)
client.run(discord_token) # type: ignore
