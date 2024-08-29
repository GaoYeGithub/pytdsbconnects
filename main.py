import os
import json
import discord
import asyncio
import datetime
import tdsbconnects
from getpass import getpass

TOKEN = 'UR_DISCORD_TOKEN'
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def get_tdsb_data(username, password, date):
    async with tdsbconnects.TDSBConnects() as session:
        await session.login(username, password)
        info = await session.get_user_info()
        
        user_data = {
            "name": info.name,
            "role": str(info.roles[0]),
            "school": {
                "name": info.schools[0].name,
                "code": info.schools[0].code,
                "school_year": info.schools[0].school_year,
                "school_year_start": str(info.schools[0].school_year_start),
                "school_year_end": str(info.schools[0].school_year_end)
            }
        }

        timetable_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        timetable = await info.schools[0].timetable(timetable_date)
        
        if timetable:
            user_data["timetable"] = {
                "day": timetable[0].course_cycle_day,
                "courses": []
            }
            for item in timetable:
                user_data["timetable"]["courses"].append({
                    "period": item.course_period,
                    "start": str(item.course_start),
                    "end": str(item.course_end),
                    "course_name": item.course_name,
                    "course_code": item.course_code,
                    "course_block": item.course_block,
                    "teacher_name": item.course_teacher_name,
                    "teacher_email": item.course_teacher_email
                })
        else:
            user_data["timetable"] = None

        with open("user_data.json", "w") as json_file:
            json.dump(user_data, json_file, indent=4)

        return user_data

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

async def get_user_timetable(username, password, date):
    async with tdsbconnects.TDSBConnects() as session:
        await session.login(username, password)
        info = await session.get_user_info()
        school = info.schools[0]
        timetable = await school.timetable(date)
        return timetable

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!compare'):
        def check(m):
            return m.author == message.author and m.channel == message.channel

        await message.channel.send('Please enter your username:')
        username = await client.wait_for('message', check=check)
        await message.channel.send('Please enter your password:')
        password = await client.wait_for('message', check=check)
        await message.channel.send('Please enter the date you want to compare (YYYY-MM-DD):')
        date_input = await client.wait_for('message', check=check)

        date = datetime.datetime.strptime(date_input.content, "%Y-%m-%d")

        user_timetable = await get_user_timetable(username.content, password.content, date)
        my_timetable = await get_user_timetable('UR_USERNAME', 'UR_PASSWORD', date)

        shared_classes = []
        for user_class in user_timetable:
            for my_class in my_timetable:
                if (user_class.course_code == my_class.course_code and
                    user_class.course_start == my_class.course_start and
                    user_class.course_end == my_class.course_end):
                    shared_classes.append({
                        'period': user_class.course_period,
                        'course_name': user_class.course_name,
                        'course_code': user_class.course_code,
                        'course_start': user_class.course_start,
                        'course_end': user_class.course_end,
                        'teacher': user_class.course_teacher_name,
                    })

        if shared_classes:
            response = "**We have the following classes together:**\n\n"
            for c in shared_classes:
                response += (f"**Period {c['period']}**\n"
                             f"> **Course**: *{c['course_name']}*\n"
                             f"> **Code**: `{c['course_code']}`\n"
                             f"> **Time**: `{c['course_start']}` to `{c['course_end']}`\n"
                             f"> **Teacher**: *{c['teacher']}*\n\n")
            await message.channel.send(response)
        else:
            await message.channel.send("**We don't have any classes together on that day.**")

client.run(TOKEN)
