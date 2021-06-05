from cowin_api import CoWinAPI
import pandas as pd
from copy import deepcopy
import datetime
from decouple import config
import smtplib
from email.message import EmailMessage
import time
import os
import logging
import requests


# Either insert your emails and password here or use python-decouple or follow this article https://saralgyaan.com/posts/set-passwords-and-secret-keys-in-environment-variables-maclinuxwindows-python-quicktip/

#FROM_EMAIL = os.environ.get('email')
FROM_EMAIL="cowinniranam@gmail.com"
TO_EMAIL = "adilmathew@gmail.com"
#PASSWORD = os.environ.get('password')
PASSWORD="covid19@niranam"

# Just Change these values
no_of_days = 28   # Change this to 7,14,21 or 28
distcodes = ['300', '301']  # Add as many pincodes as you want separated by commas
min_age_limit = 18  # Change this to 18 if you want 18+

BASE_DATE = datetime.datetime.now()
#DATE_LIST = date_list = [BASE_DATE + datetime.timedelta(days=x * 7) for x in range(int(no_of_days / 7))]
DATE_LIST = date_list = [BASE_DATE + datetime.timedelta(days=x ) for x in range(int( 7))]

dates = [date.strftime("%d-%m-%Y") for date in date_list]


# Start the API
cowin = CoWinAPI()

# Logging stuff
MY_PATH = os.getcwd()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(f'{os.path.join(MY_PATH, "cowin_email_alerts.log")}')
fmt = logging.Formatter('%(levelname)s : %(name)s : %(asctime)s : %(message)s')
file_handler.setFormatter(fmt)
logger.addHandler(file_handler)


def send_email(text_file: str):
    """ This function sends the email if the Vaccination slot is available

    Parameters
    ----------
    text_file: str
    This is a text file containing the details of all the slots available, it is generated by main function if there is an availability.

    Requires
    --------
    TO_EMAIL : str
        The email address to which you need to send the email
    FROM_EMAIL: str
        The email address from which you want to send the email
    PASSWORD: str
        Password of the FROM_EMAIL

    You can either hard code it at line 11-13 above or use python-decouple or environmental variables

    For more details about sending emails, check this article
    https://saralgyaan.com/posts/use-python-to-send-email/

    Sends
    -----
    The email
    """

    message = EmailMessage()
    message['Subject'] = 'Covid Vaccination Slot is available'
    message['From'] = FROM_EMAIL
    message['To'] = TO_EMAIL
    with open(text_file, 'r') as f:
        contents = f.readlines()
        text = '\n'.join(contents)
        final_text = f'Dear adil,\n\n Covid Vaccination slots are available at the following locations\n {text} \n\nRegards,\n adil'
    message.set_content(final_text)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(FROM_EMAIL, PASSWORD)
        smtp.send_message(message)


def get_availability(distcode: str, date: str, min_age_limit: int):
    """
    This function checks the availability of the Covid Vaccination and create a pandas dataframe of the available slots details.

    Parameters
    ----------
    pincode : str
        It is provided by the user in the list on line 17
    date : str
        It is auto-generated on the basis of the no. of days for which inquiry is made. Days could be 7,14,21 or 28 (preferably).
    min_age_limit : int
        It is provided by the user at line 18

    Returns
    -------
    df : Pandas dataframe
        Containing the details of the hospital where slot is available.

    """
    #results = cowin.get_availability_by_district(distcode, date, min_age_limit)
    response = requests.get(
    'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict',
    params={'district_id': distcode,"date":date,},)
    response=response.json()
    master_data = response.get("sessions")
    
    if master_data != []:
        df = pd.DataFrame(master_data)
       
        if len(df):
            new_df=df[['name','district_name','pincode',"date",
            "available_capacity_dose1","available_capacity_dose2","available_capacity",
            "fee","min_age_limit"]].copy()
           
            return new_df


def main():
    """
    This is the main function which uses get_availability() to check for the availability and thereafter send_email() to send the emails if the slots are available.

    Parameters
    ----------
    None
    """

    final_df = None
    for distcode in distcodes:
        for date in dates:
            temp_df = get_availability(distcode, date, min_age_limit)
            if final_df is not None:
                final_df = pd.concat([final_df, temp_df])
            else:
                final_df = deepcopy(temp_df)

  
    dff=final_df[(final_df['min_age_limit']==18) & (final_df[ "available_capacity_dose1"]>0)]
    
    
    if dff.shape[0] !=0:
        dff.set_index('date', inplace=True)
        dff.to_csv(r'availability.txt', sep=' ')
        send_email('availability.txt')
        
        
    
    
        
    else:
        logger.info(f'There is no slot available for age {str(min_age_limit)} and above for pincode(s) {" ".join(distcodes)}')


if __name__ == '__main__':

    main()  # comment this

    # If you want to continuosly run it in background comment the above line and uncomment the following lines and the function will be repeated after every 15 minutes

    # while True:
    #     main()
    #     time.sleep(900)
