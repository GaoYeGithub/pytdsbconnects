import asyncio
import datetime
import tdsbconnects
import json
from getpass import getpass

async def main():
    async with tdsbconnects.TDSBConnects() as session:
        print("Logging in")
        await session.login(input("Username: "), getpass())
        print("Getting info")
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

        date = datetime.datetime.strptime(input("Enter a date to get your timetable for (YYYY-MM-DD): "), "%Y-%m-%d")
        timetable = await info.schools[0].timetable(date)
        
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

        print("Data saved to user_data.json")

asyncio.get_event_loop().run_until_complete(main())
