import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
from selenium import webdriver
from sms_services import getsmscode, smspool

URL = 'https://accounts.google.com/signup'
WAIT = 5
NEXT_BUTTON_XPATH = [
        "//button[@class='VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 qIypjc TrZEUc lw1w4b']",
        "//button[contains(text(),'Next')]",
        "//button[contains(text(),'I agree')]",
        "//span[contains(text(), 'Next')]",
        "//div[@class='VfPpkd-RLmnJb']"
        ]

def next_button(driver):
    for selector in NEXT_BUTTON_XPATH:
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, selector))).click()
            break
        except:
            pass

def create_account(driver, 
                   sms_key,
                   username, 
                   password, 
                   first_name, 
                   last_name,
                   month,
                   day,
                   year):
    """
    Automatically creates a Gmail  account.

    Args:
        driver (WebDriver): The Selenium WebDriver instance for the configured browser.
        username (str): The desired username for the email account.
        password (str): The desired password for the email account.
        first_name (str): The first name for the account holder.
        last_name (str): The last name for the account holder.
        month (str): The birth month for the account holder.
        day (str): The birth day for the account holder.
        year (str): The birth year for the account holder.

    Returns:
        Email and password of the created account.

    """
    SMS_SERVICE = sms_key['name']

    if SMS_SERVICE == 'getsmscode':
        data = sms_key['data'] 
        data.update({'project': 1,
                     'country': 'us'})
        sms_provider = getsmscode.GetsmsCode(**data)
    elif SMS_SERVICE == 'smspool':
        data = sms_key['data']
        data.update({'service': 395})
        sms_provider = smspool.SMSPool(**data)

    logging.info('Creating Gmail account')

    driver.set_window_size(800, 600)
    driver.get(URL)

    driver.implicitly_wait(2)

    # Insert first and last name
    name_input = WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.ID, 'firstName')))
    name_input.send_keys(first_name)
    lastname_input = WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.ID, 'lastName')))
    lastname_input.send_keys(last_name)
    next_button(driver)

    # birthdate
    time.sleep(10)
    month_combobox = Select(WebDriverWait(driver, WAIT).until(EC.element_to_be_clickable((By.ID, 'month'))))
    month_combobox.select_by_index(month)
    # driver.find_element(By.XPATH, f'//*[@id="month"]/option[{month}]').click() alternative
    day_input = WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.XPATH, '//input[@name="day"]')))
    driver.execute_script("arguments[0].scrollIntoView();", day_input)
    driver.execute_script("arguments[0].setAttribute('value', arguments[1]);", day_input, int(day))
    year_input = WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.ID, 'year')))
    driver.execute_script("arguments[0].scrollIntoView();", year_input)
    driver.execute_script("arguments[0].setAttribute('value', arguments[1]);", year_input, year)
    gender_combobox = Select(WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.ID, 'gender'))))
    gender_combobox.select_by_index(3)
    next_button(driver)

    # select how to define username
    try:
        create_input = WebDriverWait(driver, WAIT).until(EC.element_to_be_clickable((By.ID, 'selectionc4')))
        create_input.click()
    except Exception as error:
        pass

    time.sleep(10)
    username_input = WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.NAME, 'Username')))
    username_input.send_keys(username)
    next_button(driver)

    # Insert Password
    password_input = WebDriverWait(driver, WAIT).until(EC.element_to_be_clickable((By.NAME, 'Passwd')))
    password_input.send_keys(password)
    password_confirm_input = WebDriverWait(driver, WAIT).until(EC.element_to_be_clickable((By.NAME, 'PasswdAgain')))
    password_confirm_input.send_keys(password)
    next_button(driver)

    if SMS_SERVICE == 'getsmscode':
        phone = sms_provider.get_phone(send_prefix=True)
    elif SMS_SERVICE == 'smspool':
        phone, order_id = sms_provider.get_phone(send_prefix=True)
    time.sleep(5)
    WebDriverWait(driver, WAIT).until(EC.element_to_be_clickable((By.ID, "phoneNumberId"))).send_keys('+' + str(phone) + Keys.ENTER)

    try:
        if SMS_SERVICE == 'getsmscode':
            code = sms_provider.get_code(phone)
        elif SMS_SERVICE == 'smspool':
            code = sms_provider.get_code(order_id)
        WebDriverWait(driver, WAIT).until(EC.element_to_be_clickable((By.ID, "code"))).send_keys(str(code) + Keys.ENTER)
    except (KeyboardInterrupt, Exception) as exc:
        raise exc

    time.sleep(5)
    driver.find_elements(By.TAG_NAME, "button")[-1].click()
    # recuperation phone (skip)
    next_button(driver)

    # final step
    next_button(driver)
    next_button(driver)
    time.sleep(8)

    logging.info("Verification complete.")
    logging.info("IF YOU ACCESS THIS ACCOUNT IMMEDIATELY FROM A DIFFERENT IP IT WILL BE BANNED")
    
    try:
        logging.info('Gmail email account created successfully.')
        logging.info("Account Details:")
        logging.info(f"Email:      {username}@gmail.com")
        logging.info(f"Password:      {password}")
        logging.info(f"First Name:    {first_name}")
        logging.info(f"Last Name:     {last_name}")
        logging.info(f"Date of Birth: {month}/{day}/{year}")
        driver.quit()
        return f"{username}@gmail.com", password
    except:
        logging.error("There was an error creating the Gmail account.")

    driver.quit()
