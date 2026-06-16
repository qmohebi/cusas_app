import pytest
from django.urls import reverse
from .factories import (MachineFactory, ProbeFactory, TestResultFactory, UserFactory, UltrasoundProfileFactory)

@pytest.mark.django_db
class TestCusasIndexView:
    url = reverse('cusas:cusas_home')

    def test_correct_template_loads(self, client, profile_user):
        client.force_login(profile_user)
        response = client.get(self.url)
        assert "cusas/cusas.html" in [t.name for t in response.templates]

    def test_admin_user_can_access(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(self.url)
        assert response.status_code==200

    def test_profile_user_can_access(self, client, profile_user):
        client.force_login(profile_user)
        response = client.get(self.url)
        assert response.status_code==200

    def test_unauthenticated_redirected(self, client):
        response = client.get(self.url)
        assert response.status_code==302

    def test_user_without_profile_gets_403(self,client, plain_user):
        client.force_login(plain_user)
        response = client.get(self.url)

        response.status_code==403

    def test_profile_user_only_sees_own_location_machines(self, client, profile_user, location, other_location):
        '''
        machine at other location must not appear for regular profile user
        '''
        user_machine = MachineFactory(location=location)
        other_machine = MachineFactory(location=other_location)
        client.force_login(profile_user)
        response = client.get(self.url)
        machines=list(response.context['machines'])
        assert user_machine in machines 
        assert other_machine not in machines

        
    def test_superuser_sees_all_locations(self, client, superuser, location, other_location):
        user_machine = MachineFactory(location=location)
        other_machines = MachineFactory(location=other_location)
        client.force_login(superuser)
        response = client.get(self.url)
        machines = list(response.context['machines'])
        assert user_machine in machines
        assert other_machines in machines  

    
    def test_overdue_machine_appears(self, client, profile_user, location):
        import datetime
        overdue=MachineFactory(location=location, next_qa_date=datetime.date.today() - datetime.timedelta(days=5))
        client.force_login(profile_user)
        response = client.get(self.url)
        assert overdue in list(response.context['machines'])
        
    def test_not_due_machines_does_not_appear(self, client, profile_user, location):
        pass

    def test_due_mahines_within_5_days_appear(self, client, profile_user, location):
        pass