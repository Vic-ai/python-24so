"""
!!!

This is the OLD Api - only included for backwards compability

!!!
"""
import logging
from suds.client import Client
from tfsoffice import exceptions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('suds.client')
# logger.setLevel(logging.INFO)

# http://developer.24sevenoffice.com/#apiauthenticate
# http://developer.24sevenoffice.com/category/dev/#apiinvoiceservice
# http://developer.24sevenoffice.com/diverse/apiinvoiceservice-datatypes/
# http://developer.24sevenoffice.com/diverse/apicompanyservice-datatypes/
# http://developer.24sevenoffice.com/hidden/webserviceprojectservice/


class TwentyFour(object):
    _session_id = None
    _headers = None
    _faults = False
    _services = {
        'Authenticate':
            'https://api.24sevenoffice.com/authenticate/' +
            'v001/authenticate.asmx?WSDL',
        'Project':
            'http://webservices.24sevenoffice.com/Project/V001/' +
            'ProjectService.asmx?WSDL',
        'Template':
            'https://api.24sevenoffice.com/CRM/Template/V001/' +
            'TemplateService.asmx?WSDL',
        'Company':
            'https://api.24sevenoffice.com/CRM/Company/V001/' +
            'CompanyService.asmx?WSDL',
        'Product':
            'https://api.24sevenoffice.com/Logistics/Product/V001/' +
            'ProductService.asmx?WSDL',
        'Invoice':
            'https://api.24sevenoffice.com/Economy/InvoiceOrder/V001/' +
            'InvoiceService.asmx?WSDL',
        'Client':
            'https://api.24sevenoffice.com/Client/V001/' +
            'ClientService.asmx?WSDL',
        'Transaction':
            'https://api.24sevenoffice.com/Economy/Accounting/V001/' +
            'TransactionService.asmx?WSDL',
        'File':
            'https://webservices.24sevenoffice.com/file/V001/' +
            'FileService.asmx?wsdl',
        'FileInfo':
            'https://webservices.24sevenoffice.com/file/V001/' +
            'FileInfoService.asmx?wsdl',
        'Attachment':
            'https://webservices.24sevenoffice.com/Economy/Accounting/Accounting_V001/' +
            'AttachmentService.asmx?WSDL',
        'SalesOpp':
            'https://webservices.24sevenoffice.com/SalesOpp/V001/' +
            'SalesOppService.asmx?WSDL',
        'Invitation':
            'https://webservices.24sevenoffice.com/Invitation/' +
            'Invitation_V001/InvitationService.asmx?WSDL',
        'Time':
            'http://webservices.24sevenoffice.com/timesheet/v001/' +
            'timeservice.asmx?WSDL',
        'Account':
            'http://webservices.24sevenoffice.com/Economy/Account/' +
            'AccountService.asmx?WSDL',
    }
    _clients = {}

    def __init__(self, username, password, applicationid, faults=False):
        self._faults = faults

        # authenticate
        status, session_id = self._authenticate(
            username, password, applicationid)
        if status != 200:
            logger.warning('Cannot authenticate with 24so, Status is not OK: %s - %s' % (status, session_id))
        assert status == 200, 'Cannot authenticate with 24so, Status is not OK: %s' % status
        logging.debug('Authenticated OK as %s' % username)
        # store session id
        self._session_id = session_id
        self._headers = {'Cookie': 'ASP.NET_SessionId=%s' % self._session_id}

    def _authenticate(
            self,
            username,
            password,
            applicationid,
            identityid="00000000-0000-0000-0000-000000000000"
    ):
        client = Client(self._services['Authenticate'], faults=self._faults)
        cred = client.factory.create('Credential')
        cred.ApplicationId = applicationid
        # cred.identityid = identityid
        cred.Username = username
        cred.Password = password
        return client.service.Login(cred)

    def get_client(self, name):
        if name in self._clients:
            return self._clients[name]

        # Create a new client
        self._clients[name] = Client(
            self._services[name],
            faults=self._faults,
            headers=self._headers)
        logging.debug('Created new service: %s' % name)
        return self._clients[name]

    def get_project(self, project_id):
        """
        Load a single project
        """
        client = self.get_client('Project')
        status, project = client.service.GetSingleProject(project_id)
        assert status == 200, 'GetSingleProject is not ok: %s' % status
        return project

    def create_project(self, name):
        r"""
        Project
        """
        client = self.get_client('Project')
        project_name_type = client.factory.create('ProjectNameType')

        # create empty project
        project = client.factory.create('Project')
        project.Name = name
        project.NameDisplay = project_name_type
        project.Version = 1  # no rights management
        status, project_id = client.service.SaveProject(project)
        assert status == 200, 'SaveProject is not ok: %s' % status
        logging.info('Created new project: %s' % project_id)

        # return project
        status, project = client.service.GetSingleProject(project_id)
        assert status == 200, 'GetSingleProject is not ok: %s' % status

        return project

    def save_project(self, project):
        r"""
        Project
        """
        client = self.get_client('Project')
        status, result = client.service.SaveProject(project)
        assert status == 200, 'SaveProject is not ok: %s' % status
        logging.info('Project [%s] saved' % project.Id)
        return result

    def find_project(self, **kwargs):
        r"""
        Only accepts ONE parameter at a time.

        CustomerId int
        Search string
        ChangedAfter datetime
        StartedAfter datetime
        StartedBefore datetime
        MyProjects bool
        AllOpenProjects bool
        http://developer.24sevenoffice.com/hidden/webserviceprojectservicev001-datatypes/
        """
        # get project client
        client = self.get_client('Project')

        # create a basic search
        project_search = client.factory.create('ProjectSearch')
        for key, value in kwargs.items():
            setattr(project_search, key, value)

        # search for projects
        status, projects = client.service.GetProjectList(project_search)
        if status != 200:
            logger.warning('24so find_project: %s - %s' % (status, projects))

        assert status == 200, 'GetProjectList failed: %s, %s' % (status, str(kwargs))
        if 'Project' not in projects:
            return None
        projects = [p for p in projects.Project]
        return projects

    def get_company(self, CompanyId):  # noqa
        companies = self.list_companies(CompanyId=CompanyId)
        if not companies or len(companies) == 0:
            return None
        elif len(companies) > 1:
            raise exceptions.TooManyResultsException()
        return companies[0]

    def list_companies(self, **kwargs):
        r"""
        List companies by:

        CompanyId
        CompanyName (do not use *)
        ChangedAfter
        """
        # validate params
        assert kwargs.get('CompanyId') \
            or kwargs.get('CompanyName') \
            or kwargs.get('ChangedAfter'), \
            'No valid CompanySearchParameters '\
            '(CompanyId|CompanyName|ChangedAfter)'

        client = self.get_client('Company')

        # returnProperties
        return_values = client.factory.create('ArrayOfString')
        return_values.string = ['OrganizationNumber', 'Owner', 'Name', 'FirstName', 'NickName',
                                'Country', 'Status',
                                'APIException', 'Note', 'InvoiceLanguage',
                                'Type', 'Username', 'IncorporationDate',
                                'DateCreated', 'DateChanged', 'Status', 'BankAccountNo',
                                'TypeGroup', 'IndustryId', 'MemberNo',
                                'DistributionMethod', 'EmailAddresses', 'Addresses',
                                'PhoneNumbers', 'Maps', 'Relations', 'CurrencyId']

        params = client.factory.create('CompanySearchParameters')
        for key, value in kwargs.items():
            setattr(params, key, value)

        status, result = client.service.GetCompanies(params, return_values)
        if status != 200:
            logger.warning('24so list_companies: %s - %s' % (status, result))
        assert status == 200, 'GetCompanies failed: %s, %s - %s' % (status, kwargs.get('CompanyId'), kwargs.get('CompanyName'))

        if 'Company' not in result:
            return None
        return [c for c in result.Company]

    def save_company(self, name, company_type='Supplier', **kwargs):
        r"""
        Create or update a Company

        set parameter Id to update an existing company
        Available kwargs:
        - Name (as param)
        - InvoiceLanguage
        - Owner (user id)
        - BankAccountNo
        - TypeGroup
        - Country
        - email_work
        - email_invoice
        - phone
        """
        client = self.get_client('Company')

        company_types = client.factory.create('CompanyType')
        # currency_type = client.factory.create('CurrencyType')

        company = client.factory.create('Company')
        company.Name = name
        company.Type = getattr(company_types, company_type)  # default: Leverandor
        # country can be set with kwargs Country and InvoiceCountry
        company.Country = kwargs.pop('Country', 'NO')
        company.InvoiceLanguage = kwargs.pop('InvoiceLanguage', 'NO')
        # not needed, works better with default = None
        # company.CurrencyId = currency_type.NOK

        # email
        company.EmailAddresses.Work.Value = kwargs.pop('email_work', None)
        company.EmailAddresses.Invoice.Value = kwargs.pop(
            'email_invoice', None)

        # phone
        company.PhoneNumbers.Work.Value = kwargs.pop('phone', None)

        # apply kwargs
        for key, value in kwargs.items():
            setattr(company, key, value)

        # Send a list of companies
        company_list = client.factory.create('ArrayOfCompany')
        company_list.Company = [company, ]

        # Save/store companies in the list
        status, result = client.service.SaveCompanies(company_list)
        assert status == 200, 'SaveCompanies failed: %s' % status

        if 'Company' not in result:
            return []
        return [c for c in result.Company]

    def list_company_categories(self, company_id):
        client = self.get_client('Company')
        status, result = client.service.GetCustomerCategories(company_id)
        assert status == 200, 'GetCustomerCategories failed: %s' % status
        if 'int' not in result:
            return []
        return result.int

    def save_company_categories(self, company_id, categories):
        client = self.get_client('Company')

        available_categories = self.list_categories()

        category_list = client.factory.create('ArrayOfKeyValuePair')
        for cat in categories:
            pair = client.factory.create('KeyValuePair')
            for tmp in available_categories:
                if tmp.Name == cat:
                    # print 'Adding category: %s - %s' % (tmp.Id, tmp.Name)
                    pair.Key = tmp.Id
                    pair.Value = company_id
                    category_list.KeyValuePair.append(pair)

        status, result = client.service.SaveCustomerCategories(category_list)
        assert status == 200, 'SaveCustomerCategories failed: %s' % status
        return result

    def list_categories(self):
        client = self.get_client('Company')
        status, result = client.service.GetCategories()
        assert status == 200, 'GetCategories failed: %s' % status
        return [c for c in result.Category]
