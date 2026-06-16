Deployment on IIS
git clone
activate venv
as python-ldap requires the wheel on windows run this first
pip install lib_resources/python_ldap_3.4.5-version_of_python
then 
pip install -r requirements.txt
then 
py manage.py collectstatic