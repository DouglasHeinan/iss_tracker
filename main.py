import requests
from datetime import datetime
import smtplib
import time
import os


MY_LAT = os.environ["MY_LAT"]
MY_LNG = os.environ["MY_LNG"]
LOCAL_UTC_OFFSET = os.environ["LOCAL_UTC_OFFSET"]
MY_EMAIL = os.environ["MY_EMAIL"]
MY_PASSWORD = os.environ["MY_PASSWORD"]
TO_ADDRESS = os.environ["TO_ADDRESS"]


def main():

    # Sets the parameters for the sunrise get
    parameters = {
        "lat": MY_LAT,
        "lng": MY_LNG,
        "formatted": 0
    }

    # Gets the sunrise and sunset data, sets JUST the hour of both to variables, and turns them to ints
    response = requests.get("https://api.sunrise-sunset.org/json", params=parameters)
    response.raise_for_status()
    sun_data = response.json()
    sunrise = int(sun_data["results"]["sunrise"].split("T")[1].split(":")[0])
    sunrise = local_time_adjust(sunrise)
    sunset = int(sun_data["results"]["sunset"].split("T")[1].split(":")[0])
    sunset = local_time_adjust(sunset)

    # Gets the current hour
    now = datetime.now().hour

    # Every 60 seconds, checks the location of the ISS relative to the user's current location
    # AND whether or not it's nighttime. If so, the user is sent an email alerting them to look up for the ISS.
    while True:
        time.sleep(60)
        # Gets the ISS lat and long
        response = requests.get(url="http://api.open-notify.org/iss-now.json")
        response.raise_for_status()
        iss_data = response.json()
        iss_longitude = float(iss_data["iss_position"]["longitude"])
        iss_latitude = float(iss_data["iss_position"]["latitude"])

        if is_night(now, sunset, sunrise) and is_overhead(MY_LAT, MY_LNG, iss_latitude, iss_longitude):
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=MY_EMAIL, password=MY_PASSWORD)
                connection.sendmail(
                    from_addr=MY_EMAIL,
                    to_addrs=TO_ADDRESS,
                    msg=f"Subject: Look Up\n\nLook up!!! It's at Latitude:{iss_latitude}, Longitude:{iss_longitude}"
                )
        else:
            print("wait for sunset")
            print(f"iss_lat: {iss_latitude}, iss_long:{iss_longitude}, "
                  f"cur_hour:{now}, sunrise:{sunrise}, sunset:{sunset}")


# This function checks if it is currently nighttime in the user's area.
def is_night(now, sunset, sunrise):
    if sunrise > now or sunset < now:
        return True
    else:
        return False


# This function checks to see if the ISS is overhead relative to the user's current lat/long
def is_overhead(my_lat, my_lng, iss_lat, iss_lng):
    if (iss_lat + 5) > my_lat > (iss_lat - 5) and (iss_lng + 5) > my_lng > (iss_lng - 5):
        return True
    else:
        return False


# The sunrise/sunset api gets the time in utc. This function converts it to the user's local time.
def local_time_adjust(utc_time):
    local_time = utc_time - int(LOCAL_UTC_OFFSET)
    if local_time < 0:
        local_time += 24
    return local_time


if __name__ == '__main__':
    main()
