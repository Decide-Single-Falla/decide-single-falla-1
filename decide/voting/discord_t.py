import discord
import requests
import pytest
import pytest_asyncio
from discord.ext import commands
from discord.ext.commands import Cog, command
import discord.ext.test as dpytest
from discord import Embed, Color
from dotenv import load_dotenv

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decide.settings')
django.setup()

from .models import Voting, Question, QuestionOption

load_dotenv()

BASE_URL = 'http://localhost:8000/'

class Misc(Cog):
    @command()
    async def list_all_votings(self, ctx):
        response = requests.get(BASE_URL + "voting/", timeout=5)
        votings = response.json()
        embed = Embed(title='Votings', color=Color.random())
        for voting in votings:
            embed.add_field(name=f'{voting["id"]}: {voting["name"]}',
                             value=voting["question"]["desc"], inline=False)
        await ctx.send(embed=embed)

@pytest_asyncio.fixture
async def bot():
    # Setup
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!",
                     intents=intents)
    await b._async_setup_hook()
    await b.add_cog(Misc())

    dpytest.configure(b)

    yield b

    # Teardown
    await dpytest.empty_queue() # empty the global message queue as test teardown


@pytest.fixture
def voting(db):
    question = Question.objects.create(desc="Question desc")
    question.save()
    for i in range(3):
        option = QuestionOption(question=question, option='option {}'.format(i+1))
        option.save()
    voting = Voting.objects.create(name="Test Voting", desc="This is a test voting", question=question)
    voting.save()
    print("Voting options: ", voting.question)
    return voting

@pytest.mark.asyncio
async def test_list_all_votings(bot, voting):
    await dpytest.message("!list_all_votings")
    response = dpytest.get_message()
    embed = response.embeds[0]
    assert embed.title == "Votings"

