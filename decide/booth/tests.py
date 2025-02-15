from base.tests import BaseTestCase

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from census.models import Census
from django.utils import timezone
from mixnet.models import Auth
from django.conf import settings

from voting.models import Voting, Question, QuestionOption
from store.models import Vote

from selenium import webdriver
from selenium.webdriver.common.by import By

import time

# Create your tests here.

class BoothTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
    def tearDown(self):
        super().tearDown()
    def testBoothNotFound(self):
        
        # Se va a probar con el numero 10000 pues en las condiciones actuales en las que nos encontramos no parece posible que se genren 10000 votaciones diferentes
        response = self.client.get('/booth/10000/')
        self.assertEqual(response.status_code, 404)
    
    def testBoothRedirection(self):
        
        # Se va a probar con el numero 10000 pues en las condiciones actuales en las que nos encontramos no parece posible que se genren 10000 votaciones diferentes
        response = self.client.get('/booth/10000')
        self.assertEqual(response.status_code, 301)


class SeleniumBoothTestCase(StaticLiveServerTestCase):

    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        self.q = Question(desc='test question')
        self.q.save()
        self.v = Voting(name='test voting', question=self.q)
        self.v.save()
        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        self.v.auths.add(a)
        self.v.create_pubkey()
        self.v.start_date = timezone.now()
        self.v.save()
        
        self.questionOption = QuestionOption(question = self.q, number = 1, option = 'Booth test option')
        self.questionOption.save()

        self.user = User(username='test', is_staff=True, is_superuser=True)
        self.user.set_password('testpassword')
        self.user.save()

        self.census = Census(voting_id=self.v.pk, voter_id=self.user.pk)
        self.census.save()

        super().setUp()


    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()


    def test_selenium_booth(self):              

        self.base.login('test', 'testpassword')

        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}/')
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".navbar-toggler-icon").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".btn-secondary").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "username").send_keys("test")
        self.driver.find_element(By.ID, "password").send_keys("testpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "q1").click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()
        time.sleep(1)
        vState= self.driver.find_element(By.CSS_SELECTOR,".alert-success").text
        self.assertTrue(vState, 'Congratulations. Your vote has been sent')
    
    def test_selenium_booth_logout(self):

        self.base.login('test', 'testpassword')

        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}/')
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".navbar-toggler-icon").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".btn-secondary").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "username").send_keys("test")
        self.driver.find_element(By.ID, "password").send_keys("testpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()
        time.sleep(1)
        # Now we click on the logout button
        self.driver.find_element(By.CSS_SELECTOR, ".btn-secondary").click()
        time.sleep(1)
        # We should be redirected to the login page, we check the text
        # in the same btn-secondary button
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".btn-secondary").text, 'Login')

    def test_selenium_booth_failed_login(self):

        self.base.login('test', 'testpassword')

        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}/')
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".navbar-toggler-icon").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".btn-secondary").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "username").send_keys("test")
        self.driver.find_element(By.ID, "password").send_keys("testpassword-fake")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()
        time.sleep(1)
        # In div class alert alert-danger we should have the error message Error: Bad Request
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".alert-danger").text, 'Error: Bad Request')

class PrivateVotingBoothTestCase(StaticLiveServerTestCase):

    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        self.q = Question(desc='test question')
        self.q.save()
        self.v = Voting(name='test voting', question=self.q, private=True)
        self.v.save()
        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        self.v.auths.add(a)
        self.v.create_pubkey()
        self.v.start_date = timezone.now()
        self.v.save()
        
        self.questionOption = QuestionOption(question = self.q, number = 1, option = 'Booth test option')
        self.questionOption.save()

        self.anonymousUser = User(pk=2 ,username='anonymous')
        self.anonymousUser.set_password('tbo12345')
        self.anonymousUser.save()

        self.user = User(username='notanonymous')
        self.user.set_password('qwerty12345')
        self.user.save()

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()

    def test_private_booth_success(self):

        # By default, the view should do this to let the user vote, but its not done in the test
        self.base.login('anonymous', 'tbo12345')

        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}/')
        time.sleep(1)
        self.driver.find_element(By.ID, "q1").click()
        self.driver.find_element(By.XPATH, "//*[@id='app-booth']/div/div[2]/div/button").click()
        time.sleep(1)

        vState = self.driver.find_element(By.CSS_SELECTOR,".alert-success").text
        self.assertTrue(vState, 'Congratulations. Your vote has been sent')

    def test_private_booth_other_user(self):

        # In case the user is logged because he done other voting o by the method
        self.base.login('notanonymous', 'qwerty12345')

        self.driver.get(f'{self.live_server_url}/booth/{self.v.pk}/')
        time.sleep(1)
        self.driver.find_element(By.ID, "q1").click()
        self.driver.find_element(By.XPATH, "//*[@id='app-booth']/div/div[2]/div/button").click()
        time.sleep(1)

        vState = self.driver.find_element(By.CSS_SELECTOR,".alert-success").text
        self.assertTrue(vState, 'Congratulations. Your vote has been sent')

        self.assertEqual(Vote.objects.count(), 1)
        vote = Vote.objects.last()
        # The private voting should have logged out and logged in with the anonymous user
        self.assertEqual(vote.voter_id, self.anonymousUser.pk)
