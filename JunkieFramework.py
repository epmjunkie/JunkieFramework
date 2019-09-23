class Settings(object):
    def __init__(self,
                 email_sender="hypadmin@epmjunkie.com",
                 email_smtp_host="localhost",
                 email_smtp_port=None,
                 email_smtp_password=None,
                 email_smtp_tls=False,
                 essbase_server=None,
                 essbase_application=None,
                 essbase_database=None,
                 essbase_log=False,
                 batch_command_line=True):
        self.email_sender = email_sender
        self.email_smtp_password = email_smtp_password
        self.email_smtp_host = email_smtp_host
        self.email_smtp_tls = email_smtp_tls
        if email_smtp_port:
            self.email_smtp_port = email_smtp_port
        elif email_smtp_tls:
            self.email_smtp_port = 465
        else:
            self.email_smtp_port = 25
        self.essbase_server = essbase_server
        self.essbase_application = essbase_application
        self.essbase_database = essbase_database
        self.essbase_log = essbase_log
        self.batch_command_line = batch_command_line


class Core(object):
    class _Log:
        def __init__(self, context, api, separator=":\t", delimiter="\n"):
            self._context = context
            self.api = api
            self.separator = separator
            self.delim = delimiter

        def _parse(self, obj, separator=None, delimiter=None):
            if not delimiter:
                delimiter = self.delim
            if not separator:
                separator = self.separator
            return delimiter.join(["%s%s%s" % (key, separator, obj[key]) for key in sorted(obj.keySet())])

        def object(self, obj, prefix="Object: ", separator=None, delimiter=None):
            if obj:
                return "%(prefix)s%(list)s" % {"prefix": prefix, "list": self._parse(obj, separator, delimiter)}
            return "%sEmpty" % prefix

        def context(self):
            if self.context:
                self.api.logDebug(self.object(self._context, prefix="FDM Context:\n"))
            else:
                self.api.logWarn(self.object(self._context, prefix="FDM Context: "))

    class _Email:
        def __init__(self, settings):
            self.sender = settings.email_sender
            self.host = settings.email_smtp_host
            self.port = settings.email_smtp_port
            self.password = settings.email_smtp_password
            self.tls = settings.email_smtp_tls

        # Handles sending email with optional attachments
        '''
        Sample usage:
        subject = "Data load has started"
        body = "Data load for location has started."
        recipients = can be a array ["hypadmin@epmjunkie.com","testing@epmjunkie.com"] or comma delimited list
        send(recipients=recipients, subject=subject, body=body)
        '''

        def send(self, recipients, body, subject="Test Message", attachment=[], sender=None, host=None, port=None,
                 password=None, tls=None):
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            if not sender:
                sender = self.sender
            if not host:
                host = self.host
            if not port:
                port = self.port
            if not password:
                password = self.password
            if tls is None:
                tls = self.tls
            if attachment is None:
                attachment = []

            if len(recipients) == 0:  # Catch missing emails
                recipients = sender
                recipients = [recipients]
                subject = "Invalid Recipients - " + subject
            else:
                if "," in recipients:  # Check if its a comma delimited string already
                    recipients = [x.strip() for x in recipients.split(",")]
                elif not isinstance(recipients, list):  # if its not a list make it one
                    recipients = [recipients]

            client = smtplib.SMTP(host, port)
            if tls:
                client.ehlo()
                client.starttls()
                client.ehlo()
            if password:
                client.login(sender, password)
            message = MIMEMultipart()
            message["From"] = sender
            message["To"] = ', '.join(recipients)
            message["Subject"] = subject
            for item in attachment:
                message.attach(item)
            message.attach(MIMEText(body))
            client.sendmail(sender, recipients, message.as_string())
            client.quit()
            client.close()

        # Handles creating attachment for emailing
        @staticmethod
        def create_attachment(path, name=None):
            from os import path as ospath
            if not name:
                name = ospath.basename(path)
            import mimetypes
            from email.mime.audio import MIMEAudio
            from email.mime.base import MIMEBase
            from email.mime.image import MIMEImage
            from email.mime.text import MIMEText
            from email import encoders
            if len(name) > 0 and len(path) > 0:
                content_type = mimetypes.guess_type(path)[0]

                if content_type is None:
                    content_type = "text/plain"

                maintype, subtype = content_type.split("/", 1)

                f = open(path)
                if maintype == "text":
                    attachment = MIMEText(f.read(), _subtype=subtype)
                elif maintype == "image":
                    attachment = MIMEImage(f.read(), _subtype=subtype)
                elif maintype == "audio":
                    attachment = MIMEAudio(f.read(), _subtype=subtype)
                else:
                    attachment = MIMEBase(_maintype=maintype, _subtype=subtype)
                    attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                f.close()
                attachment.add_header("Content-Disposition", "attachment", filename=name)

                return attachment
            return None

    class _File:
        class File(object):
            def __init__(self, username=None, password=None, path=None):
                self.username = username
                self.password = password
                self.path = path

        def __init__(self, framework, settings=None):
            self.framework = framework

        def get_info(self, logical_schema):
            import com.sunopsis.dwg.DwgObject as DwgObject
            sql_query = """SELECT c.USER_NAME, c.PASS, sp.SCHEMA_NAME
                           FROM SNP_CONNECT c
                             INNER JOIN SNP_PSCHEMA SP on c.I_CONNECT = SP.I_CONNECT
                             INNER JOIN SNP_PSCHEMA_CONT SPC on SP.I_PSCHEMA = SPC.I_PSCHEMA
                             INNER JOIN SNP_LSCHEMA SL on SPC.I_LSCHEMA = SL.I_LSCHEMA and SL.LSCHEMA_NAME = ?
                             INNER JOIN SNP_CONTEXT CX on SPC.I_CONTEXT = CX.I_CONTEXT and CX.DEF_CONT = 1
                             LEFT JOIN SNP_MTXT t on c.I_TXT_JAVA_URL = t.I_TXT"""
            result_set = self.framework._api.executeQuery(sql_query, [logical_schema])
            result_set.next()
            return self.File(result_set.getString('USER_NAME'), DwgObject.snpsDecypher(result_set.getString('PASS')),
                             result_set.getString('SCHEMA_NAME'))

    class _SQL:
        class SQL(object):
            def __init__(self, username=None, password=None, server=None, jdbc=None, connection=None):
                self.username = username
                self.password = password
                self.server = server
                self.jdbc = jdbc
                self.connection = connection

            def connect(self):
                import java.sql as sql
                self.connection = sql.DriverManager.getConnection(self.jdbc, self.username, self.password)
                return self

        def __init__(self, framework, settings):
            self.framework = framework
            self.connections = []

        def get_connection(self, logical_schema):
            import com.sunopsis.dwg.DwgObject as DwgObject
            sql_query = """SELECT c.USER_NAME, c.PASS, c.DSERV_NAME, t.FULL_TXT AS JDBC
                           FROM SNP_CONNECT c
                             INNER JOIN SNP_PSCHEMA SP on c.I_CONNECT = SP.I_CONNECT
                             INNER JOIN SNP_PSCHEMA_CONT SPC on SP.I_PSCHEMA = SPC.I_PSCHEMA
                             INNER JOIN SNP_LSCHEMA SL on SPC.I_LSCHEMA = SL.I_LSCHEMA and SL.LSCHEMA_NAME = ?
                             INNER JOIN SNP_CONTEXT CX on SPC.I_CONTEXT = CX.I_CONTEXT and CX.DEF_CONT = 1
                             LEFT JOIN SNP_MTXT t on c.I_TXT_JAVA_URL = t.I_TXT"""
            result_set = self.framework._api.executeQuery(sql_query, [logical_schema])
            result_set.next()
            connection = self.SQL(username=result_set.getString('USER_NAME'),
                                  password=DwgObject.snpsDecypher(result_set.getString('PASS')),
                                  server=result_set.getString('DSERV_NAME'),
                                  jdbc=result_set.getString("JDBC")).connect()
            self.connections.append(connection)
            return connection

    class _Essbase:
        def __init__(self, framework, settings, username=None, password=None, server=None, application=None,
                     database=None,
                     sso=True, log=False):
            self.username = username
            self.password = password
            self.server = server
            self.application = application
            self.database = database
            self.sso = sso
            self.framework = framework
            self.log = log
            if settings.essbase_server is not None and self.server is None:
                self.server = settings.essbase_server
            if settings.essbase_application is not None and self.application is None:
                self.application = settings.essbase_application
            if settings.essbase_database is not None and self.database is None:
                self.database = settings.essbase_database
            if self.username is None:
                self.username = self.framework.username
            if self.log is None:
                self.log = settings.essbase_log

            if self.application is None:
                if self.log:
                    self.framework._api.logDebug("Get App Name: %s" % (self.framework.target_app))
                self.application = self.framework.target_app
            if self.database is None:
                if self.log:
                    self.framework._api.logDebug("Get DB Name: %s" % (self.framework.target_app_db))
                self.database = self.framework.target_app_db
            self.essbase = None
            self.domain = None
            self.connection = None

        def get_info(self, logical_schema):
            import com.sunopsis.dwg.DwgObject as DwgObject
            sql_query = """SELECT c.USER_NAME, c.PASS, c.DSERV_NAME, SP.SCHEMA_NAME as APP, sp.CATALOG_NAME as DB
                           FROM SNP_CONNECT c
                             INNER JOIN SNP_PSCHEMA SP on c.I_CONNECT = SP.I_CONNECT
                             INNER JOIN SNP_PSCHEMA_CONT SPC on SP.I_PSCHEMA = SPC.I_PSCHEMA
                             INNER JOIN SNP_LSCHEMA SL on SPC.I_LSCHEMA = SL.I_LSCHEMA and SL.LSCHEMA_NAME = ?
                             INNER JOIN SNP_CONTEXT CX on SPC.I_CONTEXT = CX.I_CONTEXT and CX.DEF_CONT = 1"""
            result_set = self.framework._api.executeQuery(sql_query, [logical_schema])
            result_set.next()
            self.username = result_set.getString('USER_NAME')
            self.password = DwgObject.snpsDecypher(result_set.getString('PASS'))
            self.server = result_set.getString('DSERV_NAME')
            self.application = result_set.getString('APP')
            self.database = result_set.getString('DB')
            return self

        def connect(self):
            from com.essbase.api.session import IEssbase
            from com.hyperion.aif.util import RegistryUtil as aifUtil
            self.essbase = IEssbase.Home.create(IEssbase.JAPI_VERSION)
            if self.server is None:
                if self.log:
                    self.framework._api.logDebug("Get Server for: %s using user %s" % (self.application, self.username))
                self.server = aifUtil.getEssbaseServerName(self.application, self.username)
            if self.sso:
                if self.log:
                    self.framework._api.logDebug("Get SSO for: %s" % (self.username))
                token = aifUtil.getSSOTokenForUser(self.username)
                if self.log:
                    self.framework._api.logDebug("Sign on using token: %s" % (token))
                self.domain = self.essbase.signOn(self.username, token, True, None, "Embedded")
            else:
                if self.log:
                    self.framework._api.logDebug("Sign on using user/pass: %s/%s" % (self.username, self.password))
                self.domain = self.essbase.signOn(self.username, self.password, False, None, "Embedded")
            self.connection = self.domain.getOlapServer(self.server)
            self.connection.connect()
            return self

        def get_cube(self, application=None, database=None):
            if application is None:
                application = self.application
            if database is None:
                database = self.database
            if self.connection:
                if self.log:
                    self.framework._api.logDebug("Get Cube: %s.%s" % (application, database))
                return self.connection.getApplication(application).getCube(database)
            raise ("Connection unavilable: Unable to access cube.")

        def get_variable(self, variable):
            if not self.connection:
                self.connect()
            if self.connection:
                return self.connection.getSubstitutionVariableValue(variable)
            raise ("Connection unavilable: Unable to retreive variable.")

        def sign_off(self):
            if self.essbase:
                self.essbase.signOff()

    class _Batch(object):
        def __init__(self, framework, settings):
            self.framework = framework
            self.framework.append_path(self.fdmee_lib('aif-batch.jar'))
            from com.hyperion.aif.util import BatchExecutor
            self.batch = BatchExecutor()
            self.username = None
            self.password = None
            self.command_line = settings.batch_command_line

        def fdmee_lib(self, value):
            import os
            file = "%(home)s%(delim)sproducts%(delim)sFinancialDataQuality%(delim)slib%(delim)s%(value)s" % \
                   {"home": self.framework.epm_home, "delim": os.path.sep, "value": value}
            return file

        @staticmethod
        def true_false(value):
            if value is True or value == "Y":
                return "Y"
            else:
                return "N"

        def command(self, args):
            import os
            import subprocess
            path = "%s/financialdataquality/" % self.framework.epm_instance_home.replace("\\", "/")
            if args[0] == "loaddata":
                command = "loaddata.bat"
            if not args[2].startswith('-f:'):
                args[2] = '-f:%s' % args[2]
            if ' ' in args[3]:
                args[3] = args[3].replace(' ', '+')
            self.framework._api.logDebug('Running %s%s %s' % (path, command, ' '.join(args[1:])))
            os.chdir(path)
            result = subprocess.Popen('%s%s %s' % (path, command, ' '.join(args[1:])), stderr=subprocess.PIPE,
                                      stdout=subprocess.PIPE)
            stdout, stderr = result.communicate()
            if stderr:
                self.framework._api.logDebug(str(stderr))
            else:
                self.framework._api.logDebug(str(stdout))

        def loaddata(self, load_rule="", start_period="", end_period="", username=None, password=None,
                     import_from_source=True, export_to_target=True, export_mode="STORE_DATA", import_mode="REPLACE",
                     sync_mode=True, load_exchange_rate=False):
            if not username:
                username = self.username
            if not password:
                password = self.password
            if sync_mode == False or sync_mode == "ASYNC":
                sync_mode = "ASYNC"
            else:
                sync_mode = "SYNC"
            if end_period == "":
                end_period = start_period
            command = ["loaddata", username, password, load_rule, self.true_false(import_from_source),
                       self.true_false(export_to_target), export_mode, import_mode,
                       self.true_false(load_exchange_rate), start_period, end_period, sync_mode]
            for i in command:
                self.framework._api.logInfo(i)
            if not self.command_line:
                self.batch.main(command)
            else:
                self.command(command)

    class Status(object):
        def parse(self, value):
            return int(value) % 10

        @property
        def none(self):
            return 0

        @property
        def success(self):
            return 1

        @property
        def fail(self):
            return 2

        @property
        def unknown(self):
            return 3

    def __init__(self, context, api, settings=Settings()):
        self._context = context
        self._api = api
        self.settings = settings
        self.email = self._Email(settings=settings)
        self.log = self._Log(context, api)
        self.essbase = self._Essbase(self, settings=settings)
        self.sql = self._SQL(self, settings=settings)
        self.file = self._File(self, settings=settings)
        self.batch = self._Batch(self, settings=settings)
        self._log_file = None
        self.status = self.Status()

    def logoff(self):
        if self.essbase.connection:
            try:
                self.essbase.sign_off()
            finally:
                self.essbase.connection = None
        for connection in self.sql.connections:
            try:
                connection.connection.close()
            finally:
                connection.connection = None

    def cleanup(self):
        if self.batch.batch:
            del self.batch.batch
        del self.batch
        del self.essbase
        del self.sql
        del self.file
        del self.email
        del self.log
        try:
            import gc
            self._api.logInfo("Calling Garbage Collection")
            gc.collect()
        except ex:
            self._api.logInfo("Error Calling Garbage Collection: " + ex)

    def append_path(self, value):  # don't append if its already there
        import sys
        import os
        if os.path.exists(value):
            if value not in sys.path:
                self._api.logInfo("Adding \"%s\" to PATH" % (value))
                sys.path.append(value)
        else:
            self._api.logInfo("\"%s\" does not exist" % (value))
        self._api.logInfo(";".join(sys.path))

    def get_context_value(self, name):
        return str(self._context[name])

    @property
    def application_name(self):
        return self.get_context_value("APPNAME")

    @property
    def application_id(self):
        return self.get_context_value("APPID")

    @property
    def batch_script_directory(self):
        return self.get_context_value("BATCHSCRIPTDIR")

    @property
    def category(self):
        return self.get_context_value("CATNAME")

    @property
    def category_key(self):
        return self.get_context_value("CATKEY")

    @property
    def check_status(self):
        return self.get_context_value("CHKSTATUS")

    @property
    def epm_home(self):
        return self.get_context_value("EPMORACLEHOME")

    @property
    def epm_instance_home(self):
        return self.get_context_value("EPMORACLEINSTANCEHOME")

    @property
    def export_flag(self):
        return self.get_context_value("EXPORTFLAG")

    @property
    def export_mode(self):
        return self.get_context_value("EXPORTMODE")

    @property
    def file_directory(self):
        return self.get_context_value("FILEDIR")

    @property
    def file_name(self):
        return self.get_context_value("FILENAME")

    @property
    def import_flag(self):
        return self.get_context_value("IMPORTFLAG")

    @property
    def import_format(self):
        return self.get_context_value("IMPORTFORMAT")

    @property
    def import_status(self):
        return self.get_context_value("IMPSTATUS")

    @property
    def inbox_directory(self):
        return self.get_context_value("INBOXDIR")

    @property
    def load_id(self):
        return int(self.get_context_value("LOADID"))

    @property
    def location_key(self):
        return self.get_context_value("LOCKEY")

    @property
    def location(self):
        return self.get_context_value("LOCNAME")

    @property
    def multi_period_load(self):
        return self.get_context_value("MULTIPERIODLOAD")

    @property
    def outbox_directory(self):
        return self.get_context_value("OUTBOXDIR")

    @property
    def period(self):
        return self.get_context_value("PERIODNAME")

    @property
    def period_key(self):
        return self.get_context_value("PERIODKEY")

    @property
    def process_status(self):
        return self.get_context_value("PROCESSSTATUS")

    @property
    def rule(self):
        return self.get_context_value("RULENAME")

    @property
    def rule_id(self):
        return self.get_context_value("RULEID")

    @property
    def script_directory(self):
        return self.get_context_value("SCRIPTSDIR")

    @property
    def source_name(self):
        return self.get_context_value("SOURCENAME")

    @property
    def source_type(self):
        return self.get_context_value("SOURCETYPE")

    @property
    def target_app(self):
        return self.get_context_value("TARGETAPPNAME")

    @property
    def target_app_db(self):
        return self.get_context_value("TARGETAPPDB")

    @property
    def username(self):
        return self.get_context_value("USERNAME")

    @property
    def process_state(self):
        import java.math.BigDecimal as bd
        return self._api.getProcessStates(bd(self.load_id))

    @property
    def import_status(self):
        self._api.logInfo("Process Status: %s\tImport Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["IMPSTATUS"])))
        if self.process_state["IMPSTATUS"] == 1 or self.process_state["PROCESSSTATUS"] == 1:
            return self.status.success
        elif self.process_state["IMPSTATUS"] == 2 or self.process_state["PROCESSSTATUS"] == 2:
            return self.status.fail
        elif self.process_state["IMPSTATUS"] == 0 and self.process_state["PROCESSSTATUS"] == 0:
            return self.status.none
        self._api.logInfo("UNKNOWN Process Status: %s\tImport Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["IMPSTATUS"])))
        return self.status.unknown

    @property
    def validation_status(self):
        self._api.logInfo("Process Status: %s\tValidation Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["VALSTATUS"])))
        if self.process_state["VALSTATUS"] == 1 or self.process_state["PROCESSSTATUS"] == 11:
            return self.status.success
        elif self.process_state["VALSTATUS"] == 2 or self.process_state["PROCESSSTATUS"] == 12:
            return self.status.fail
        elif self.process_state["VALSTATUS"] == 0 and self.process_state["PROCESSSTATUS"] <= 10:
            return self.status.none
        self._api.logInfo("UNKNOWN Process Status: %s\tValidation Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["VALSTATUS"])))
        return self.status.unknown

    @property
    def export_status(self):
        self._api.logInfo("Process Status: %s\tExport Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["EXPSTATUS"])))
        if self.process_state["EXPSTATUS"] == 1 or self.process_state["PROCESSSTATUS"] == 21:
            return self.status.success
        elif self.process_state["EXPSTATUS"] == 2 or self.process_state["PROCESSSTATUS"] == 22:
            return self.status.fail
        elif self.process_state["EXPSTATUS"] == 0 and self.process_state["PROCESSSTATUS"] <= 20:
            return self.status.none
        self._api.logInfo("UNKNOWN Process Status: %s\tExport Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["EXPSTATUS"])))
        return self.status.unknown

    @property
    def load_status(self):
        self._api.logInfo("Process Status: %s\tLoad Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["PROCESSSTATUS"])))
        if self.process_state["PROCESSSTATUS"] == 31:
            return self.status.success
        elif self.process_state["PROCESSSTATUS"] == 32:
            return self.status.fail
        elif self.process_state["PROCESSSTATUS"] <= 30:
            return self.status.none
        self._api.logInfo("UNKNOWN Process Status: %s\tLoad Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["PROCESSSTATUS"])))
        return self.status.unknown

    @property
    def check_status(self):
        self._api.logInfo("Process Status: %s\tCheck Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["CHKSTATUS"])))
        if self.process_state["CHKSTATUS"] == 1 or self.process_state["PROCESSSTATUS"] == 41:
            return self.status.success
        elif self.process_state["CHKSTATUS"] == 2 or self.process_state["PROCESSSTATUS"] == 42:
            return self.status.fail
        elif self.process_state["CHKSTATUS"] == 0 and self.process_state["PROCESSSTATUS"] <= 40:
            return self.status.none
        self._api.logInfo("UNKNOWN Process Status: %s\tCheck Status:%s" % (
        str(self.process_state["PROCESSSTATUS"]), str(self.process_state["CHKSTATUS"])))
        return self.status.unknown

    @property
    def log_file(self, refresh=False):
        if not self._log_file or refresh:
            query = "SELECT LOG_FILE from AIF_PROCESSES WHERE PROCESS_ID = ?"
            result_set = self._api.executeQuery(query, [self.load_id])
            result_set.next()
            self._log_file = result_set.getString("LOG_FILE")
        return self._log_file

    @property
    def log_file_name(self):
        import os
        return os.path.basename(self.log_file.rstrip("/").rstrip('\\'))
