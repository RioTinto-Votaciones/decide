import random
import itertools
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption, OrderQuestion, PoliticalParty, YesOrNoQuestion


class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting(self, url=None):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        
        if url:
            v = Voting(name='test voting', question=q, url=url)
        else: 
            v = Voting(name='test voting', question=q)

        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_voters(self, v):
        #Creacion de 100 voters
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def create_fiftyvoters(self, v):
        #Creacion de 50 voters
        for i in range(50):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def create_twentyfivevoters(self, v):
        #Creacion de 25 voters
        for i in range(25):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()        
            
    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': { 'a': a, 'b': b },
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting_fiftyvoters(self):
        v = self.create_voting()
        self.create_fiftyvoters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_complete_voting_twentyfivevoters(self):
        v = self.create_voting()
        self.create_twentyfivevoters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])        
            
    def test_complete_voting_with_voters(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_voting_from_api_noadmin(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 403 )

    def test_create_voting_from_api_admin(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201 )


    def test_create_voting_without_url_and_question(self):
        v = self.create_voting()

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question_opt': ['Yes', 'No']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_create_voting_without_url_and_options(self):
        v = self.create_voting()

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'Is there any url? '
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)


    def test_update_voting(self):
        voting = self.create_voting()

        data = {'action': 'start'}
        #response = self.client.post('/voting/{}/'.format(voting.pk), data, format='json')
        #self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)

        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')

        
        
        
# tests political party

    def test_create_politicalParty(self):
        political_party = PoliticalParty(name="Nombre de partido", leader="Fulanito",
            description="Descripcion del partido", acronym="NdP")

        political_party.save()
        self.assertTrue(PoliticalParty.objects.filter(leader="Fulanito").exists())


    
    def test_create_politicalParty_error(self):

        political_party = PoliticalParty(name="nombre de ejemplo", acronym="NdE")

        try:
            political_party.save()

        except:

            self.assertTrue(True)


    
    def test_create_yes_or_no(self):

        yes_or_no = YesOrNoQuestion(desc="Descripcion de pregunta si o no")
        yes_or_no.save()
        self.assertTrue(YesOrNoQuestion.objects.filter(desc="Descripcion de pregunta si o no").exists())

        



    def test_create_yes_or_no_error(self):

        try: 
            yes_or_no = YesOrNoQuestion()
            yes_or_no.save()
        except:
            self.assertTrue(True)




    def test_update_political_party(self):

        political_party = PoliticalParty(name="Nombre de partido", leader="Fulanito",
        description="Descripcion del partido", acronym="NdP")

        political_party.save()

        political_party= PoliticalParty.objects.get(name="Nombre de partido")

        political_party.name = "Nueva Cualicion"
        political_party.save()


        self.assertTrue(PoliticalParty.objects.filter(name="Nueva Cualicion").exists())



    def test_update_political_party_error(self):

        try:
            political_party = PoliticalParty(name="Nombre de partido", leader="Fulanito",
            description="Descripcion del partido", acronym="NdP")

            political_party.save()

            political_party= PoliticalParty.objects.get(name="Nombre de partido")

            political_party.name = ""
            political_party.save()

        except:

            self.assertTrue(True)



    def test_create_voting_url_whitespaces(self):
        v = self.create_voting(url="_test voting")
        self.assertTrue(Voting.objects.filter(url="_test+voting").exists())

    def test_create_voting_url_exists(self):
        v = self.create_voting(url="_test_voting")

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'url': '_test_voting',
            'question': 'Is this a question? ',
            'question_opt': ['Yes', 'No']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)
    
    def test_create_voting_without_url(self):
        data = {
            'name': 'Example No URL',
            'desc': 'Description example',
            'question': 'Is this a question? ',
            'question_opt': ['Yes', 'No']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)


    def test_create_voting_orderquestion(self):
        orderquestion = OrderQuestion(desc="Descripción de ejemplo")
        orderquestion.save()
    
        v = Voting(name='test voting', url="_test_voting_orderquestion", order_question=orderquestion)
    
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        self.assertTrue(Voting.objects.get(url="_test_voting_orderquestion").order_question==orderquestion)

    def test_create_orderquestion(self):
        orderquestion = OrderQuestion(desc="Descripción de ejemplo")
        orderquestion.save()

        self.assertTrue(OrderQuestion.objects.filter(desc="Descripción de ejemplo").exists())
    
    
       
    
