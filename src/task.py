from selenium import webdriver
from selenium.common.exceptions import TimeoutException
import pickle
import logger
import time
import threading
import options

thread_id = 0


class Task:
    def __init__(self, website, sleep_time=0, timeout=10):
        global thread_id
        thread_id += 1
        self.id = thread_id
        self.website = website
        self.sleep_time = sleep_time
        self.timeout = timeout
        self.driver = webdriver.Firefox(executable_path="../lib/geckodriver")

        if options.rewrite_cookies:
            self.driver.get(website.url)
            logger.log(f"Log into {website.name}, checking 'Keep me signed in' then press enter in the terminal.", self.id)
            input()
            logger.log("Saving cookies...", self.id)
            pickle.dump(self.driver.get_cookies(), open("Cookies.pkl", "wb"))
            logger.log("Finished storing cookies. You may now run the program without passing " + options.cookie_arg, self.id)
            exit(0)
        else:
            self.website.login(self.driver, self.timeout, self.id)

    def main_loop(self):
        while True:
            if not self.website.in_stock(self.driver, self.timeout, self.id):
                logger.log(f"{self.website.name} is out of stock. Retrying.", self.id)
                time.sleep(self.sleep_time)
                try:
                    self.driver.get(self.website.url)
                except TimeoutException:
                    logger.log(f"Reloading webpage timed out...", self.id)
                except Exception as e:
                    logger.log(f"Unexpected error loading page... Continuing.", self.id)
                    logger.log_exception(e, self.id)
                continue
            logger.log(f"{self.website.name} is in stock!", self.id)

            try:
                self.website.add_to_cart(self.driver, self.timeout, self.id)
            except Exception as e:
                logger.log("Exception occured while adding to cart...", self.id)
                logger.log_exception(e, self.id)
                continue

            try:
                purchase_result = self.website.checkout(self.driver, self.timeout, self.id)
            except Exception as e:
                logger.log(f"Exception occured while checking out...", self.id)
                logger.log_exception(e, self.id)
                continue
            if purchase_result:
                logger.log(f"Purchase successful from {self.website.url}", self.id)
                break

    def start(self):
        logger.log(f"Task {self.id} started!", self.id)
        t = threading.Thread(target=self.main_loop)
        t.start()

    def close(self):
        self.driver.close()
