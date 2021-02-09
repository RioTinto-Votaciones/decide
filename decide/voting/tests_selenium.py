import time

from base.models import Auth
from base.tests import BaseTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .models import PoliticalParty, Question, QuestionOption, Voting


class VotingAdminTestCase(StaticLiveServerTestCase):

    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()

        question = Question(desc="_Question_Test_Descripción_")
        question.save()

        option1 = QuestionOption(question=question, option="_Option_1_Test_")
        option1.save()

        option2 = QuestionOption(question=question, option="_Option_2_Test_")
        option2.save()

        political_party = PoliticalParty(name="_Political_Party_Test_", acronym="_PPT_", description="_Political_Party_Test_Descripción_", leader="_Leader_")
        political_party.save()

        auth = Auth(name="_Auth_Test", url=self.live_server_url, me=True)
        auth.save()

        voting = Voting(desc="_Votación_Test_Ya_Existente", name="_Votación_Test_Ya_Existente_Descripción", question=question, political_party=political_party, url="_votacion_test_ejemplo_already_exists")
        voting.save()

        voting.auths.add(auth)

        options = webdriver.ChromeOptions()
        # options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()            
            
    def tearDown(self):           
        super().tearDown()
        self.driver.quit()

        self.base.tearDown()

    def create_voting(self, url=None):
        self.driver.get(f'{self.live_server_url}/admin')
        self.driver.set_window_size(924, 1053)
        self.driver.find_element(By.ID, "id_username").send_keys("admin-selenium")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        time.sleep(3)

        self.driver.find_element(By.CSS_SELECTOR, ".model-voting .addlink").click()
        time.sleep(3)
        self.driver.find_element(By.ID, "id_name").send_keys("_Votación_Test_")
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("_Votación_Test_Descripción_")

        select = Select(self.driver.find_element_by_id('id_question'))
        select.select_by_visible_text('_Question_Test_Descripción_')

        select = Select(self.driver.find_element_by_id('id_political_party'))
        select.select_by_visible_text('_PPT_ (_Political_Party_Test_) - _Leader_')

        select = Select(self.driver.find_element_by_id('id_auths'))
        select.select_by_visible_text(str(self.live_server_url))
        
        if url:
            self.driver.find_element(By.ID, "id_url").click()
            self.driver.find_element(By.ID, "id_url").send_keys(url)

        self.driver.find_element(By.NAME, "_save").click()

    def test_create_voting_with_url(self):
        self.create_voting(url="_votacion_test_ejemplo_")
        self.assertTrue(len(self.driver.find_elements_by_class_name('success'))==1)

    def test_create_voting_without_url(self):
        self.create_voting()
        self.assertTrue(len(self.driver.find_elements_by_class_name('errorlist'))==1)

    def test_create_voting_existing_url(self):
        self.create_voting(url="_votacion_test_ejemplo_already_exists")
        self.assertTrue(len(self.driver.find_elements_by_class_name('errorlist'))==1)
    
    def create_orderquestionsuccess(self):
        self.driver.get(f'{self.live_server_url}/admin')
        self.driver.set_window_size(1920, 1031)
        self.driver.find_element(By.ID, "id_username").send_keys("admin-selenium")
        self.driver.find_element(By.ID, "id_password").click()
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "container").click()
        self.driver.find_element(By.CSS_SELECTOR, ".model-orderquestion .addlink").click()
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("¿Del 1 al 3 cuanto te gusta este partido?")
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.CSS_SELECTOR, "html").click()
        self.driver.find_element(By.CSS_SELECTOR, "html").click() 
        
    def test_create_orderquestion_success(self):
        self.create_orderquestionsuccess()
        self.assertTrue(len(self.driver.find_elements_by_class_name('success'))==1)

    def test_create_voting_orderquestion(self):
        self.create_orderquestionsuccess()
        self.driver.find_element(By.LINK_TEXT, "Home").click()
        self.driver.find_element(By.CSS_SELECTOR, ".model-voting .addlink").click()
        time.sleep(3)
        self.driver.find_element(By.ID, "id_name").send_keys("_Votación_Test_")
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("_Votación_Test_Descripción_")

        select = Select(self.driver.find_element_by_id('id_order_question'))
        select.select_by_visible_text('¿Del 1 al 3 cuanto te gusta este partido?')

        select = Select(self.driver.find_element_by_id('id_auths'))
        select.select_by_visible_text(str(self.live_server_url))

        self.driver.find_element(By.ID, "id_url").click()
        self.driver.find_element(By.ID, "id_url").send_keys('test')

        self.driver.find_element(By.NAME, "_save").click()
        self.assertTrue(len(self.driver.find_elements_by_class_name('success'))==1)

    
    def test_orderquestionwitherror(self):
        self.driver.get(f'{self.live_server_url}/admin')
        self.driver.set_window_size(1920, 1031)
        self.driver.find_element(By.ID, "id_username").send_keys("admin-selenium")
        self.driver.find_element(By.ID, "id_password").click()
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "container").click()
        self.driver.find_element(By.CSS_SELECTOR, ".model-orderquestion .addlink").click()
        self.driver.find_element(By.NAME, "_save").click()
        self.assertTrue(len(self.driver.find_elements_by_class_name('errorlist'))==1) 
